"""
Main handler module for the fulfillment lambda function, which runs periodically
to check all current game prices and notify subscribers of any changes.
"""
from typing import Any, Dict

from update_job import UpdateJob
from get_logger import get_logger
from subscriber_state import (
    load_game_subscriber_states_from_s3, SingleGameSubscriberState
)
from update_state import (
    load_game_update_states_from_s3,
    save_game_update_states_to_s3,
    SingleGameUpdateState,
)

logger = get_logger(__file__)


def lambda_handler(event: Any, _: Any) -> Dict[str, Dict[str, Any]]:
    """
    Checks all current game prices and notifies subscribers of any changes

    NOTE: event is unused
    """
    logger.info(f"Got event: {event}")
    update_state: Dict[str, SingleGameUpdateState] = load_game_update_states_from_s3()
    subscriber_state: Dict[str, SingleGameSubscriberState] = (
        load_game_subscriber_states_from_s3()
    )
    new_update_state: Dict[str, SingleGameUpdateState] = {}
    for (slug, single_subscriber_state) in subscriber_state.items():
        job: UpdateJob = UpdateJob(slug, single_subscriber_state)
        new_update_state[slug] = job.perform(update_state.get(slug))
    resp: Dict[str, Dict[str, Any]] = save_game_update_states_to_s3(new_update_state)
    logger.info(f"Sending response: {resp}")
    return resp
