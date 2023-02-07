export type User = {
  email: string;
  slugs: string[];
};

export function addSlugToUser(user: User, slug: string): User {
  if (user.slugs.includes(slug)) {
    console.log(
      `Trying to add ${slug} to user failed because user already has slug.`
    );
    return user;
  }
  return {
    ...user,
    slugs: Array.prototype.concat(user.slugs, [slug]),
  };
}

export function removeSlugFromUser(user: User, slug: string): User {
  const slugIndex = user.slugs.indexOf(slug);
  if (slugIndex === -1) {
    console.log(
      `Trying to remove slug ${slug} from user failed because user doesn't include slug.`
    );
    return user;
  }
  return {
    ...user,
    slugs: Array.prototype.concat(
      user.slugs.slice(0, slugIndex),
      user.slugs.slice(slugIndex + 1)
    ),
  };
}
