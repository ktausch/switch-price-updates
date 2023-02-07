import { useSessionStorage } from "usehooks-ts";
import { SearchForm } from "./SearchForm";
import { SingleHit } from "./SingleHit";
import { DummyHit } from "./DummyHit";
import { LoginForm } from "./LoginForm";
import { Hit } from "../types/Hit";
import { User } from "../types/User";
import { gameSearch } from "../utils/GameSearch";
import {
  subscribeUserToSlug,
  unsubscribeUserFromSlug,
} from "../utils/InvokeLambda";

export function SearchPage(props: {
  user: User | null;
  setUser: (user: User | null) => void;
  reloadUser: () => Promise<void>;
}): JSX.Element {
  const [hits, setHits] = useSessionStorage<Hit[]>("searchHits", []);

  async function performSearch(query: string): Promise<void> {
    setHits(
      (await gameSearch(query)).filter((hit) => hit.slug.includes("switch"))
    );
  }

  function hasSlug(hit: Hit): boolean | null {
    return props.user ? props.user.slugs.includes(hit.slug) : null;
  }

  function addSlug(hit: Hit): () => Promise<void> {
    return async () => {
      if (props.user) {
        props.setUser(await subscribeUserToSlug(props.user, hit.slug));
      }
    };
  }

  function removeSlug(hit: Hit): () => Promise<void> {
    return async () => {
      if (props.user) {
        props.setUser(await unsubscribeUserFromSlug(props.user, hit.slug));
      }
    };
  }

  function renderSingleHit(hit: Hit): JSX.Element {
    return (
      <SingleHit
        key={hit.slug}
        details={hit}
        hasSlug={hasSlug(hit)}
        addSlug={addSlug(hit)}
        removeSlug={removeSlug(hit)}
      />
    );
  }

  function clearSearch(): void {
    setHits([]);
  }

  return (
    <div>
      <LoginForm user={props.user} setUser={props.setUser} />
      <h1>Search</h1>
      <SearchForm
        performSearch={performSearch}
        hasHits={!!hits.length}
        clearSearch={clearSearch}
      />
      {hits.length ? (
        <ul>
          <DummyHit
            key="refresh"
            userSet={!!props.user}
            reloadUser={props.reloadUser}
          />
          {hits.map(renderSingleHit)}
        </ul>
      ) : null}
    </div>
  );
}
