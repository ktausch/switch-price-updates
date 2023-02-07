"""
Module with class that can represent who has been updated and
when, along with functions to load it from and save it to s3.
"""
from datetime import datetime
import json
import os
from typing import Any, Dict, List, Optional

import boto3

from get_logger import get_logger

STORECHECKER_S3_BUCKET: str = os.environ["STORECHECKER_S3_BUCKET"]
STATE_S3_KEY: str = os.environ["STATE_S3_KEY"]

logger = get_logger(__file__)
s3_client = boto3.client("s3")


class SingleGameUpdateState:
    """Class that can represent who has been updated and when"""

    def __init__(
        self,
        lowest_price: float,
        subscribers_up_to_date: List[str],
        last_updated: Optional[str] = None,
    ):
        """
        Initializes the in-memory update state.

        Args:
            lowest_price: the lowest price when this state was made
            subscribers_up_to_date: subscribers that are currently up-to-date on price
            last_updated: timestamp of form YYYYmmDDHHMMSS indicating when last updated
        """
        self.lowest_price: float = lowest_price
        self.last_updated = last_updated or datetime.now().strftime(r"%Y%m%d%H%M%S")
        self.subscribers_up_to_date: List[str] = subscribers_up_to_date.copy()

    @property
    def dictionary(self) -> Dict[str, Any]:
        """Dictionary form of single game state that is easily JSON-able"""
        return {
            "lowest_price": self.lowest_price,
            "last_updated": self.last_updated,
            "subscribers_up_to_date": self.subscribers_up_to_date,
        }
    

def load_game_update_states_from_s3() -> Dict[str, SingleGameUpdateState]:
    """Loads update state of all games from s3"""
    json_data: Dict[str, Dict[str, Any]] = json.load(
        s3_client.get_object(
            Bucket=STORECHECKER_S3_BUCKET, Key=STATE_S3_KEY
        )["Body"]
    )
    logger.info(f"Loaded {len(json_data)} single game update states from s3.")
    return {key: SingleGameUpdateState(**value) for (key, value) in json_data.items()}

def save_game_update_states_to_s3(
    data: Dict[str, SingleGameUpdateState]
) -> Dict[str, Dict[str, Any]]:
    """Saves update state of all games to s3 and returns JSON form of saved data"""
    json_data: Dict[str, Dict[str, Any]] = {
        name: value.dictionary for (name, value) in data.items()
    }
    body: bytes = json.dumps(json_data).encode()
    s3_client.put_object(Bucket=STORECHECKER_S3_BUCKET, Key=STATE_S3_KEY, Body=body)
    logger.info(f"Saved {len(data)} single game update states to s3.")
    return json_data
