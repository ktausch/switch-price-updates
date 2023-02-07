"""
Main handler module for the subscribe lambda function, which can be
used to add subscribers, remove subscribers, or add games.
"""
from typing import Any, Dict, List
from urllib.parse import unquote as decode_url

from get_logger import get_logger
from subscriber_job import parse_and_perform_subscriber_job
from subscriber_state import (
    load_game_subscriber_states_from_s3,
    save_game_subscriber_states_to_s3,
    SingleGameSubscriberState,
)

logger = get_logger(__file__)


def detect_call_type(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Allows this lambda to be both invoked directly and called via a function URL.

    NOTE: this function will need to be revisited if any of the parameters expected
          is not a string.

    Args:
        event: the input event

    Returns:
        the parameters necessary to complete the subscription job
    """
    if (url_parameters := event.get("queryStringParameters")) is None:
        return event
    elif url_parameters:
        logger.info(f"Got the following job spec from URL: {url_parameters}")
        return url_parameters
    else:
        try:
            referer: str = event["headers"]["referer"]
        except KeyError:
            raise ValueError(
                "Couldn't understand response. It seemed to be called "
                "via the URL, but no query params or referer found."
            )
        arg_strings: List[str] = referer.split("?")[-1].split("&")
        args: Dict[str, str] = {}
        for arg_string in arg_strings:
            try:
                (name, encoded_value) = arg_string.split("=")
            except ValueError:
                raise ValueError("params not understood from referer link.")
            args[name] = decode_url(encoded_value)
        return args


def lambda_handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    """Performs a SubscriberJob (see subscribe_job module) loaded from input event."""
    logger.info(f"Got event: {event}")
    job_spec: Dict[str, Any] = detect_call_type(event)
    state: Dict[str, SingleGameSubscriberState] = load_game_subscriber_states_from_s3()
    response: Dict[str, Any] = parse_and_perform_subscriber_job(job_spec, state)
    current_subscriptions: Dict[str, Dict[str, Any]] = (
        save_game_subscriber_states_to_s3(state)
    )
    logger.info(f"Current subscriptions: {current_subscriptions}")
    logger.info(f"Sending response: {response}")
    return response
