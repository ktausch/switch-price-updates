"""Module defining all of the possible jobs to modify subscriptions."""
from abc import ABCMeta, abstractmethod
from math import nan
import os
from typing import Any, Callable, Dict, List, Optional

from botocore.response import StreamingBody
import boto3

from game_shop_state import GameShopState
from get_logger import get_logger
from link_formatter import make_link_formatter
from send_email import send_email
from subscriber_state import SingleGameSubscriberState

logger = get_logger(__file__)
s3_client = boto3.client("s3")

STORECHECKER_S3_BUCKET: str = os.environ["STORECHECKER_S3_BUCKET"]
SUBSCRIBE_URL_S3_KEY: str = os.environ["SUBSCRIBE_URL_S3_KEY"]


def get_this_functions_url() -> str:
    """Gets the URL of this function."""
    data: StreamingBody = s3_client.get_object(
        Bucket=STORECHECKER_S3_BUCKET, Key=SUBSCRIBE_URL_S3_KEY
    )["Body"]
    return data.read().decode()


class SubscriberJob(metaclass=ABCMeta):
    """Base class for object that modifies subscriber state."""

    @abstractmethod
    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """
        Mutates the subscriber state based on specific task (see subclasses).
        
        The returned value is sent as a response to the caller of the lambda function
        """
        raise ValueError("Cannot call perform on abstract SubscriberJob class.")


class AddGameJob(SubscriberJob):
    """Class that adds a game with a name and the query used to find it."""

    def __init__(self, slug: str, title: str):
        """
        Creates a new AddGameJob

        Args:
            slug: the unique slug of the game
            title: the full title of the game
        """
        self.slug: str = slug
        self.title = title

    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """
        Mutates the subscriber state by adding the game

        NOTE: throws an error if the game handle already exists.
        """
        response: Dict[str, Any] = {"type": str(type(self))}
        if (current_state := state.get(self.slug)) is None:
            new_state: SingleGameSubscriberState = SingleGameSubscriberState(
                to_addresses=[], title=self.title
            )
            state[self.slug] = new_state
            logger.info(
                f'Adding new game "{self.title}" with state {new_state.dictionary}'
            )
            response.update({"success": True, "reason": ""})
        else:
            logger.warning(
                f'Trying to add game with slug "{self.slug}" to subscribed games, '
                f"but it already exists with value {current_state.dictionary}"
            )
            response.update({"success": False, "reason": "game already exists"})
            response["success"] = False
        return response


class AddOrSubtractSubscribersJob(SubscriberJob):
    """Class that adds or removes subscribers from a single game."""

    def __init__(
        self,
        slug: str,
        lowest_price: float,
        subscribers_to_add: Optional[List[str]] = None,
        subscribers_to_remove: Optional[List[str]] = None,
    ):
        """
        Args:
            name: the handle of the game to modify the subcribers of
            subscribers_to_add: if applicable, the subscribers to newly include
            subscribers_to_remove: if applicable, the subscribers to remove
        """
        self.subscribers_to_add: List[str] = [
            subscriber.lower() for subscriber in (subscribers_to_add or [])
        ]
        self.subscribers_to_remove: List[str] = [
            subscriber.lower() for subscriber in (subscribers_to_remove or [])
        ]
        self.slug: str = slug
        self.lowest_price: float = lowest_price
        self._link_formatter: Optional[Callable[[str, str], str]] = None

    @property
    def link_formatter(self) -> Callable[[str, str], str]:
        """
        Property storing function that takes in email body to format
        and recipient email address and yields formatted email body.
        """
        if self._link_formatter is None:
            self._link_formatter = make_link_formatter(
                get_this_functions_url(), self.slug
            )
        return self._link_formatter
    
    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """Mutates game's subscriber state by adding and/or removing subscribers"""
        response: Dict[str, Any] = {"type": str(type(self))}
        if (game_state := state.get(self.slug)) is None:
            raise ValueError(
                f'Cannot update subscribers of game "{self.slug}" because '
                f"that game does not exist (existing games: {list(state)})."
            )
        subscribers_added: List[str] = []
        for new_subscriber in self.subscribers_to_add:
            current_subscriber: bool = new_subscriber in game_state.to_addresses
            if current_subscriber:
                logger.warning(
                    f'Trying to add {new_subscriber} to game "{game_state.title}", '
                    "but they are already a subscriber! Not sending any email."
                )
            else:
                try:
                    remove_index: int = self.subscribers_to_remove.index(new_subscriber)
                except ValueError:
                    game_state.to_addresses.append(new_subscriber)
                    subscribers_added.append(new_subscriber)
                else:
                    logger.error(
                        f"{new_subscriber} to be both added and removed from game "
                        f'"{game_state.title}". This doesn\'t make sense, so not '
                        f"sending any email."
                    )
                    self.subscribers_to_remove.pop(remove_index)
        send_email(
            to_addresses=subscribers_added,
            subject=f"Thanks for subscribing to price updates for {game_state.title}!",
            body=(
                    "<div>"
                    "<p>"
                    f"You have been added as a subscriber to {game_state.title} price "
                    f"updates.\n\nThe current price of {game_state.title} is "
                    f"${self.lowest_price:.2f}."
                    "</p>"
                    "<p>"
                    "To unsubscribe from price updates on this game, click "
                    '<a href="{single_game_unsubscribe_link}">here</a>.'
                    "</p>"
                    "<p>"
                    "To unsubscribe from price updates on all games, click "
                    '<a href="{all_games_unsubscribe_link}">here</a>.'
                    "</p>"
                    "</div>"
            ),
            is_html=True,
            formatter=self.link_formatter,
        )
        response["subscribers_added"] = subscribers_added
        for removed_subscriber in self.subscribers_to_remove:
            try:
                index: int = game_state.to_addresses.index(removed_subscriber)
            except ValueError:
                logger.warning(
                    f'Trying to remove {removed_subscriber} from game '
                    f'"{game_state.title}", but they are not currently a subscriber. '
                    'Not sending any email.'
                )
            else:
                # this is the happy path
                game_state.to_addresses.pop(index)
        send_email(
            to_addresses=self.subscribers_to_remove,
            subject=f"You have been unsubscribed from {game_state.title} price updates",
            body=(
                "<div>"
                "<p>"
                "We're sorry to see you go!"
                "</p>"
                "<p>"
                "If this is a mistake, you can resubscribe to price updates on this "
                'game, click <a href="{single_game_subscribe_link}">here</a>.'
                "</p>"
                "<p>"
                "To unsubscribe from price updates on all other games, click "
                '<a href="{all_games_unsubscribe_link}">here</a>.'
                "</p>"
                "</div>"
            ),
            is_html=True,
            formatter=self.link_formatter,
        )
        response["subscribers_removed"] = self.subscribers_to_remove
        response["success"] = True
        return response


class RemoveSubscriberJob(SubscriberJob):
    """Class that removes a subscriber from all games updates."""

    def __init__(self, to_address: str):
        """Creates a job that will remove the given subscriber from all updates."""
        self.to_address = to_address.lower()

    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """Modifies the subscriber state by removing the subscriber from all updates."""
        response: Dict[str, Any] = {"type": str(type(self))}
        for value in state.values():
            try:
                index: int = value.to_addresses.index(self.to_address)
            except ValueError:
                pass
            else:
                value.to_addresses.pop(index)
        send_email(
            to_addresses = [self.to_address],
            subject="Unsubscribed from all price updates",
            body="You have been unsubscribed from all price updates.",
            is_html=False,
            formatter=None,
        )
        response["subscriber_completely_removed"] = self.to_address
        return response


class CheckSubscriberJob(SubscriberJob):
    """Class that checks which games a subscriber is signed up for"""

    def __init__(self, to_address: str):
        """Creates job that will check which games given subscriber is signed up for"""
        self.to_address: str = to_address.lower()

    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """Gets all games the subscriber is subscribed to"""
        return {
            "type": str(type(self)),
            "games": [
                {"title": subscriber_state.title, "slug": slug}
                for (slug, subscriber_state) in state.items()
                if self.to_address in subscriber_state.to_addresses
            ],
        }


class RemoveEmptyGamesSubscriberJob(SubscriberJob):
    """Class that removes games with no subscribers from tracking."""

    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """Removing stored data about games with no subscribers."""
        games_to_remove: List[Dict[str, str]] = []
        for (slug, value) in state.items():
            if not value.to_addresses:
                games_to_remove.append({"title": value.title, "slug": slug})
        for game in games_to_remove:
            state.pop(game["slug"])
        return {"type": str(type(self)), "games_removed": games_to_remove}


class CombinedSubscriberJob(SubscriberJob):
    """Class that will mutate the subscriber state in a sequence of small tasks"""

    def __init__(self, jobs: List[SubscriberJob]):
        """Creates a job that will perform the list of jobs"""
        self.jobs: List[SubscriberJob] = jobs

    def perform(self, state: Dict[str, SingleGameSubscriberState]) -> Dict[str, Any]:
        """Performs each job in turn"""
        responses: List[Dict[str, Any]] = [job.perform(state) for job in self.jobs]
        return {"type": str(type(self)), "responses": responses}


class _SubscriberJobParser:
    """Class that will parse a SubscriberJob from an input the subscribe lambda"""

    def __init__(
        self, event: Dict[str, Any], state: Dict[str, SingleGameSubscriberState]
    ):
        """
        Creates an object that will parse a SubscriberJob from given event.

        Args:
            event: the incoming event to the subscribe lambda function
        """
        self.details: Dict[str, Any] = event
        self.event_type: str = self.details.pop("type")
        self.subscriber: str = self.details.pop("subscriber")
        self.state: Dict[str, SingleGameSubscriberState] = state
        self._jobs: List[SubscriberJob] = []
        self.parsed: SubscriberJob = self._parse()

    def _parse_new_subscriber_event(self) -> None:
        """
        Parses a job from a new subscriber to a single game

        NOTE: Requires parameters in event:
            name: the string handle to refer to the game with
            subscriber: email address to subscribe to updates on given game
        """
        slug: str = self.details["slug"]
        shop_state: GameShopState = GameShopState(slug)
        if slug not in self.state:
            self._jobs.append(AddGameJob(slug=slug, title=shop_state.title))
        self._jobs.append(
            AddOrSubtractSubscribersJob(
                slug=slug,
                subscribers_to_add=[self.subscriber],
                lowest_price=shop_state.lowest_price,
            )
        )
        return

    def _parse_remove_subscriber_event(self) -> None:
        """
        Parses a job to remove a subscriber from one or all games

        NOTE: Requires parameters in event:
            slug (optional): if given, the unique string handle with which to refer to
                the single game from which to unsubscribe. if not given, unsubscribes
                from all games.
            subscriber: email address to unsubscribe to updates on one or all games
        """
        if (slug := self.details.get("slug")) is None:
            self._jobs.append(RemoveSubscriberJob(self.subscriber))
        else:
            self._jobs.append(
                AddOrSubtractSubscribersJob(
                    slug=slug, subscribers_to_remove=[self.subscriber], lowest_price=nan
                )
            )
        self._jobs.append(RemoveEmptyGamesSubscriberJob())
        return

    def _parse_check_event(self) -> None:
        """
        Parses a job to check which games a subscriber is subscribed to.

        NOTE: Requires parameters in event:
            subscriber: the subscriber to find games subscribed to
        """
        self._jobs.append(CheckSubscriberJob(self.subscriber))
        return

    def _parse(self) -> SubscriberJob:
        """Parses the job of the input event"""
        if self.event_type == "ADD":
            self._parse_new_subscriber_event()
        elif self.event_type == "REMOVE":
            self._parse_remove_subscriber_event()
        elif self.event_type == "CHECK":
            self._parse_check_event()
        else:
            raise ValueError(
                "Could not parse a subscriber job from the given input event."
            )
        if self._jobs:
            if len(self._jobs) == 1:
                return self._jobs[0]
            else:
                return CombinedSubscriberJob(self._jobs)
        else:
            raise ValueError("For some reason, no jobs were able to be parsed.")


def parse_and_perform_subscriber_job(
    event: Dict[str, Any], state: Dict[str, SingleGameSubscriberState]
) -> Dict[str, Any]:
    """
    Parses a job to change the subscribe state from the event input to the lambda

    Args:
        event: the input event to the lambda function, assumed to have a string value
            of event["type"]. All other elements of event are specific to the type. See
            _parse_* methods of _SubscriberJobParser for formats.
        state: the current state of subscriptions. This will be modified!

    Returns:
        the response to send to the caller of the lambda function
    """
    return _SubscriberJobParser(event, state).parsed.perform(state)
