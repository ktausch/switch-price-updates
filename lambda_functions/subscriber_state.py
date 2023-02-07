"""
Module with class that can represent subscriber state,
along with functions to load it from and save it to s3.
"""
from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

import boto3

from get_logger import get_logger

STORECHECKER_S3_BUCKET: str = os.environ["STORECHECKER_S3_BUCKET"]
SUBSCRIBERS_S3_KEY: str = os.environ["SUBSCRIBERS_S3_KEY"]

logger = get_logger(__file__)
s3_client = boto3.client("s3")


class SingleGameSubscriberState:
    """Class that can represent subscriber state for a given game"""

    def __init__(
        self,
        to_addresses: List[str],
        title: str,
        last_updated: Optional[str] = None,
    ):
        """
        Initializes in-memory state for single game

        Args:
            to_addresses: email addresses of subscribers to updates of this game
            title: the full string title of the game
            last_updated: YYYYmmDDHHMMSS timestamp of when this game was last updated
                NOTE: this is distinct from when subscribers were last updated!
        """
        self.to_addresses: List[str] = to_addresses
        self.title: str = title
        self.last_updated = last_updated or datetime.now().strftime(r"%Y%m%d%H%M%S")

    @property
    def dictionary(self) -> Dict[str, Any]:
        """Dictionary form of single game state that is easily JSON-able"""
        return {
            "to_addresses": self.to_addresses,
            "title": self.title,
            "last_updated": self.last_updated,
        }


def load_game_subscriber_states_from_s3() -> Dict[str, SingleGameSubscriberState]:
    """Loads subscriber state of all games from s3"""
    data: Dict[str, Dict[str, Any]] = json.load(
        s3_client.get_object(
            Bucket=STORECHECKER_S3_BUCKET, Key=SUBSCRIBERS_S3_KEY
        )["Body"]
    )
    logger.info(f"Loaded {len(data)} games of subscriber state from s3.")
    return {key: SingleGameSubscriberState(**value) for (key, value) in data.items()}


def save_game_subscriber_states_to_s3(
    data: Dict[str, SingleGameSubscriberState]
) -> Dict[str, Dict[str, Any]]:
    """Saves subscriber state of all games to s3 and returns JSON form of saved data"""
    json_data: Dict[str, Dict[str, Any]] = {
        name: value.dictionary for (name, value) in data.items()
    }
    body: bytes = json.dumps(json_data).encode()
    s3_client.put_object(
        Bucket=STORECHECKER_S3_BUCKET, Key=SUBSCRIBERS_S3_KEY, Body=body
    )
    logger.info(f"Saved {len(data)} single game subscriber states to s3.")
    return json_data
