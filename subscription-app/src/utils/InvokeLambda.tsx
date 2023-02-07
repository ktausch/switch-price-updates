import { User, addSlugToUser, removeSlugFromUser } from "../types/User";

type CheckSubscribeGame = {
  slug: string;
  title: string;
};

type CheckSubscribeResponse = {
  type: string;
  games: CheckSubscribeGame[];
};

type SubscribeLambdaPayload = {
  type: string;
  subscriber: string;
  slug?: string;
};

async function invokeLambda(payload: SubscribeLambdaPayload): Promise<any> {
  const query: string = new URLSearchParams({ ...payload }).toString();
  const url: string = `${process.env.REACT_APP_SUBSCRIBE_LAMBDA_BASE_URL}?${query}`;
  const response: Response = await fetch(url);
  return await response.json();
}

export async function makeUser(email: string): Promise<User> {
  const response: CheckSubscribeResponse = await invokeLambda({
    type: "CHECK",
    subscriber: email,
  });
  return {
    email,
    slugs: response.games.map((game) => game.slug),
  };
}

export async function subscribeUserToSlug(
  user: User,
  slug: string
): Promise<User> {
  console.log(
    `subscribing user ${user.email} to price updates for game ${slug}`
  );
  console.log(
    await invokeLambda({
      type: "ADD",
      slug,
      subscriber: user.email,
    })
  );
  return addSlugToUser(user, slug);
}

export async function unsubscribeUserFromSlug(
  user: User,
  slug: string
): Promise<User> {
  console.log(
    `unsubscribing user ${user.email} from price updates for game ${slug}`
  );
  console.log(
    await invokeLambda({
      type: "REMOVE",
      slug,
      subscriber: user.email,
    })
  );
  return removeSlugFromUser(user, slug);
}

export async function unsubscribeUserFromAllSlugs(user: User): Promise<User> {
  console.log(
    `unsubscribing user ${user.email} from price updates for all games`
  );
  console.log(
    await invokeLambda({
      type: "REMOVE",
      subscriber: user.email,
    })
  );
  return { ...user, slugs: [] };
}
