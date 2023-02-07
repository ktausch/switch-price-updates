import { Hit } from "../types/Hit";

const US_ALGOLIA_ID = "U3B6GR4UA3";
const US_ALGOLIA_KEY = "c4da8be7fd29f0f5bfa42920b0a99dc7";
const US_GAMES_INDEX_NAME = "ncom_game_en_us_title_asc";
const US_ALGOLIA_HEADERS = {
  "Content-Type": "application/json",
  "X-Algolia-API-Key": US_ALGOLIA_KEY,
  "X-Algolia-Application-Id": US_ALGOLIA_ID,
};
const US_GET_GAMES_BASE_URL = `https://${US_ALGOLIA_ID}-dsn.algolia.net/1/indexes/${US_GAMES_INDEX_NAME}`;

export async function gameSearch(query: string): Promise<Hit[]> {
  const url = `${US_GET_GAMES_BASE_URL}?query=${encodeURIComponent(query)}`;
  const response = await fetch(url, {
    method: "get",
    headers: US_ALGOLIA_HEADERS,
  });
  const data = await response.json();
  console.log("Completed search!");
  console.log(data);
  return data.hits;
}

export async function getGame(slug: string): Promise<Hit | null> {
  const tokens: string[] = slug.split("-");
  tokens.pop();
  const query: string = tokens.join(" ");
  return (await gameSearch(query)).find((hit) => hit.slug === slug) || null;
}
