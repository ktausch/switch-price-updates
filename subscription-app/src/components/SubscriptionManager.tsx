import { useState } from "react";
import { User } from "../types/User";
import { LoginForm } from "./LoginForm";
import { SingleSubscription } from "./SingleSubscription";
import {
  unsubscribeUserFromSlug,
  unsubscribeUserFromAllSlugs,
} from "../utils/InvokeLambda";

export function SubscriptionManager(props: {
  user: User | null;
  setUser: (user: User | null) => void;
  reloadUser: () => Promise<void>;
}): JSX.Element {
  const [
    unsubscribeFromAllButtonDisabled,
    setUnsubscribeFromAllButtonDisabled,
  ] = useState(false);
  const [refreshButtonDisabled, setRefreshButtonDisabled] = useState(false);

  function renderSingleSubscription(slug: string): JSX.Element {
    return (
      <SingleSubscription
        key={slug}
        slug={slug}
        removeSlug={async () => {
          if (props.user) {
            props.setUser(await unsubscribeUserFromSlug(props.user, slug));
          }
        }}
      />
    );
  }

  async function unsubscribeFromAll(): Promise<void> {
    if (props.user) {
      setUnsubscribeFromAllButtonDisabled(true);
      props.setUser(await unsubscribeUserFromAllSlugs(props.user));
      setUnsubscribeFromAllButtonDisabled(false);
    } else {
      console.error(
        "Tried to unsubscribe from all updated when no user is loaded."
      );
    }
  }

  async function refreshUser(): Promise<void> {
    setRefreshButtonDisabled(true);
    await props.reloadUser();
    setRefreshButtonDisabled(false);
  }

  return (
    <div>
      <LoginForm user={props.user} setUser={props.setUser} />
      <h1>Active subscriptions</h1>

      {props.user?.slugs.length ? (
        <div>
          <button
            onClick={unsubscribeFromAll}
            disabled={unsubscribeFromAllButtonDisabled}
          >
            Unsubscribe from all price updates!
          </button>
          {unsubscribeFromAllButtonDisabled ? null : (
            <button onClick={refreshUser} disabled={refreshButtonDisabled}>
              ↻
            </button>
          )}
        </div>
      ) : (
        <div></div>
      )}
      {!props.user ? (
        <p>
          You are not logged in. Log in at the top of this page to manage
          subscriptions!
        </p>
      ) : props.user.slugs.length ? (
        <ul>{props.user.slugs.map(renderSingleSubscription)}</ul>
      ) : (
        <p>
          You don't currently have any subscriptions! Hop on over to the{" "}
          <a href="/">search page</a> to find games to subscribe to!
        </p>
      )}
    </div>
  );
}
