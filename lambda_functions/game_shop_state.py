"""Module that contains a class to encapsulate current state in the shop"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote as url_encode

from urllib3 import HTTPResponse, PoolManager

from get_logger import get_logger

US_ALGOLIA_KEY: str = os.environ["US_ALGOLIA_KEY"]
US_ALGOLIA_ID: str = os.environ["US_ALGOLIA_ID"]
US_GAMES_INDEX_NAME: str = os.environ["US_GAMES_INDEX_NAME"]

US_ALGOLIA_HEADERS: Dict[str, str] = {
    "Content-Type": "application/json",
    "X-Algolia-API-Key": US_ALGOLIA_KEY,
    "X-Algolia-Application-Id": US_ALGOLIA_ID,
}
US_GET_GAMES_BASE_URL: str = (
    f"https://{US_ALGOLIA_ID}-dsn.algolia.net/1/indexes/{US_GAMES_INDEX_NAME}"
)
logger = get_logger(__file__)


class GameShopState:
    """Class representing current state of a game in the shop"""

    def __init__(self, slug: str):
        """
        Initiates a new game shop state.

        Args:
            slug: the unique slug identifier of the game in the shop
        """
        self.slug: str = slug
        self.__title_and_lowest_price: Optional[Tuple[str, float]] = None

    def _get_game(self) -> Dict[str, Any]:
        """Gets the game with the given slug."""
        query: str = " ".join(self.slug.split("-")[:-1])  # leave off "switch"
        url: str = f"{US_GET_GAMES_BASE_URL}?query={url_encode(query)}"
        http: PoolManager = PoolManager()
        response: HTTPResponse = http.request(
            "GET", url, headers=US_ALGOLIA_HEADERS
        )
        if response.status != 200:
            logger.error(f"Received bad response {response.status} from API call.")
            logger.debug(f"Response data: {response.data.decode()}")
        hits: List[Dict[str, Any]] = json.loads(response.data.decode())["hits"]
        logger.debug(f'hits from query "{query}": {hits}')
        try:
            return next(filter(lambda hit: hit["slug"] == self.slug, hits))
        except StopIteration:
            raise ValueError(
                f'Game with slug "{self.slug}" did not appear in search '
                f'results using query "{query}". See debug logs for hits'
            )

    @property
    def _title_and_lowest_price(self) -> Tuple[str, float]:
        """Private property containing the title and lowest price in a single tuple."""
        if self.__title_and_lowest_price is None:
            game: Dict[str, Any] = self._get_game()
            title: str = game["title"]
            lowest_price: float = game["lowestPrice"]
            logger.info(f"Lowest price for {self.slug} is now ${lowest_price}")
            self.__title_and_lowest_price = (title, lowest_price)
        return self.__title_and_lowest_price
    
    @property
    def title(self) -> str:
        """The full title of the game"""
        return self._title_and_lowest_price[0]

    @property
    def lowest_price(self) -> float:
        """The lowest price (USD) of the game"""
        return self._title_and_lowest_price[1]
