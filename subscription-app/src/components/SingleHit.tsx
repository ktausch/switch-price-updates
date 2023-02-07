import { formatPrice } from "../utils/Utilities";
import { Hit } from "../types/Hit";
import { HitInterface } from "./HitInterface";

export function SingleHit(props: {
  details: Hit;
  hasSlug: boolean | null;
  removeSlug: () => Promise<void>;
  addSlug: () => Promise<void>;
}): JSX.Element {
  const {
    slug,
    lowestPrice,
    title,
    boxart,
    description,
    //horizontalHeaderImage,
  } = props.details;

  async function subscribe(): Promise<void> {
    if (props.hasSlug === null) {
      throw new Error("Cannot subscribe when no user is logged in.");
    }
    if (!props.hasSlug) {
      await props.addSlug();
    }
  }

  async function unsubscribe(): Promise<void> {
    if (props.hasSlug === null) {
      throw new Error("Cannot unsubscribe when no user is logged in.");
    }
    if (props.hasSlug) {
      await props.removeSlug();
    }
  }

  function getButtonText(): string {
    return props.hasSlug
      ? "Unsubscribe from price updates!"
      : "Subscribe to price updates!";
  }

  function renderSlug(): JSX.Element {
    return (
      <p>
        <b>Slug</b>: {slug}
      </p>
    );
  }

  function renderPrice(): JSX.Element {
    return (
      <p>
        <b>Current price</b>: {formatPrice(lowestPrice)}
      </p>
    );
  }

  function renderDescription(): JSX.Element {
    return (
      <p>
        <b>Description</b>: {description}
      </p>
    );
  }

  function renderBoxArt(): JSX.Element {
    return <img src={boxart} alt={`Box art for ${title}`} />;
  }

  function renderTitle(): JSX.Element {
    return (
      <h2>
        <b>{title}</b>
      </h2>
    );
  }

  return (
    <HitInterface
      buttonExists={props.hasSlug !== null}
      onButtonClick={props.hasSlug ? unsubscribe : subscribe}
      getButtonText={getButtonText}
      renderTitle={renderTitle}
      renderSlug={renderSlug}
      renderPrice={renderPrice}
      renderDescription={renderDescription}
      renderBoxArt={renderBoxArt}
    />
  );
}
