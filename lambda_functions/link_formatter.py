"""
Module with a function that will make an email formatting function that will add URLs.
"""
from typing import Callable, Dict, Optional

from urllib.parse import quote as url_encode


def make_link_formatter(
    base_url: str, slug: Optional[str] = None
) -> Callable[[str, str], str]:
    """
    Makes an email formatting function that will add URLs to email bodies.

    NOTE: single_game_* strings are only available if a slug is given

    Args:
        base_url: the base (parameter-less) email to call the lambda function with
        slug: the slug of the game 

    Returns:
        function that will take in an email body to format and a recipient and formats
        its "{single_game_subscribe_link}", "{all_games_unsubscribe_link}",
        "{single_game_unsubscribe_link}", and "{recipient}" strings.
    """

    def formatter(body: str, recipient: str) -> str:
        """
        Formats the body of the email message with customized
        links to unsubscribe from price updates.

        Args:
            body: the string email message, including the raw, unformatted
                strings "{single_game_subscribe_link}", "{all_games_unsubscribe_link}",
                "{single_game_unsubscribe_link}", and "{recipient}"
            recipient: the email address the message will be sent to

        Returns:
            final body text to send in an email, adorned with unsubscribe links
        """
        kwargs: Dict[str, str] = {"recipient": recipient}
        url_with_subscriber: str = f"{base_url}?subscriber={url_encode(recipient)}"
        kwargs["all_games_unsubscribe_link"] = f"{url_with_subscriber}&type=REMOVE"
        if slug is not None:
            kwargs["single_game_unsubscribe_link"] = (
                f'{kwargs["all_games_unsubscribe_link"]}&slug={slug}'
            )
            kwargs["single_game_subscribe_link"] = (
                f"{url_with_subscriber}&type=ADD&slug={slug}"
            )
        return body.format(**kwargs)

    return formatter
