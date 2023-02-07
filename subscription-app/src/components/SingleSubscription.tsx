import { useEffect, useState } from "react";
import { useSessionStorage } from "usehooks-ts";
import { getGame } from "../utils/GameSearch";
import { Hit } from "../types/Hit";
import { formatPrice } from "../utils/Utilities";

export function SingleSubscription(props: {
  slug: string;
  removeSlug: () => Promise<void>;
}): JSX.Element | null {
  const [loadComplete, setLoadComplete] = useState(false);
  const [buttonDisabled, setButtonDisabled] = useState(false);
  const [hit, setHit] = useSessionStorage<Hit | null>(
    `${props.slug}-hit`,
    null
  );

  async function unsubscribe(): Promise<void> {
    setButtonDisabled(true);
    await props.removeSlug();
    setButtonDisabled(false);
  }

  useEffect(() => {
    async function loadHit(): Promise<void> {
      const loadedHit: Hit | null = await getGame(props.slug);
      setHit(loadedHit);
      setLoadComplete(true);
    }
    if (!loadComplete) {
      loadHit();
    }
  });

  if (!loadComplete) {
    return null;
  }
  if (!hit) {
    return <p>Game with slug {props.slug} failed to load</p>;
  }
  return (
    <li>
      <h2>
        <b>{hit.title}</b>
      </h2>
      <div className="SingleHit">
        <div className="SingleHitText">
          <p>
            <b>Slug</b>: {hit.slug}
          </p>
          <p>
            <b>Current price</b>: {formatPrice(hit.lowestPrice)}
          </p>
          <p>
            <b>Description</b>: {hit.description}
          </p>
        </div>
        <div className="SingleHitBoxArt">
          <img src={hit.boxart} alt={`Box art for ${hit.title}`} />
        </div>
        <div className="SingleHitSubscribe">
          <button onClick={unsubscribe} disabled={buttonDisabled}>
            Unsubscribe from price updates!
          </button>
        </div>
      </div>
    </li>
  );
}
