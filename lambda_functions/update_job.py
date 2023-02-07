"""Module with class that updates subscribers about price changes."""
import os
from typing import Optional

from game_shop_state import GameShopState
from get_logger import get_logger
from link_formatter import make_link_formatter
from send_email import send_email
from subscriber_state import SingleGameSubscriberState
from update_state import SingleGameUpdateState

SUBSCRIBE_LAMBDA_URL: str = os.environ["SUBSCRIBE_LAMBDA_URL"]

logger = get_logger(__file__)


class UpdateJob:
    """Class that can update subscribers about price changes"""

    def __init__(self, slug: str, subscriber_state: SingleGameSubscriberState):
        """
        Initializes a job to update subscribers (if necessary) about a single game.

        Args:
            name: the name of the game to update subscribers about
            subscriber_state: information about the game and its subscribers
        """
        self.slug: str = slug
        self.subscriber_state: SingleGameSubscriberState = subscriber_state
        self._shop_state: Optional[GameShopState] = None

    @property
    def shop_state(self) -> GameShopState:
        """The current lowest price of the game in USD."""
        if self._shop_state is None:
            self._shop_state = GameShopState(self.slug)
        return self._shop_state

    def perform(
        self, current_state: Optional[SingleGameUpdateState]
    ) -> SingleGameUpdateState:
        """Updates all subscribers via email if the price has changes."""
        new_state: SingleGameUpdateState = SingleGameUpdateState(
            lowest_price=self.shop_state.lowest_price,
            subscribers_up_to_date=self.subscriber_state.to_addresses
        )
        if current_state is None:
            logger.info(
                f"First fulfillment for game {self.shop_state.title}. No email to send."
            )
            return new_state
        price_change: float = new_state.lowest_price - current_state.lowest_price
        if abs(price_change) <= 0.01:
            logger.info(
                f"Price ({self.shop_state.title}) hasn't changed above $0.01 level: "
                f"${current_state.lowest_price:.2f} -> ${new_state.lowest_price:.2f}"
            )
            return new_state
        continuing_subscribers = [
            subscriber
            for subscriber in current_state.subscribers_up_to_date
            if subscriber in new_state.subscribers_up_to_date
        ]
        if not continuing_subscribers:
            logger.info(
                "No continuing subscribers to update. (New subscribers "
                "should've received first email from subscribe lambda)"
            )
            return new_state
        adjective: str = "up" if (price_change > 0) else "down"
        subject: str = (
            f'Price {"increase" if (price_change > 0) else "decrease"} '
            f"on {self.subscriber_state.title} by ${abs(price_change):.2f}"
        )
        message: str = (
            "<div>"
            "<p>"
            f"The current price of {self.subscriber_state.title} is "
            f"${self.shop_state.lowest_price:.2f}, {adjective} "
            f"from old price of ${current_state.lowest_price:.2f}.\n\n"
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
        )
        send_email(
            to_addresses=continuing_subscribers,
            subject=subject,
            body=message,
            is_html=True,
            formatter=make_link_formatter(SUBSCRIBE_LAMBDA_URL, slug=self.slug),
        )
        return new_state
