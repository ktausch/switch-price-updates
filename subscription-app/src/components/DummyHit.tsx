import { HitInterface } from "./HitInterface";

export function DummyHit(props: {
  userSet: boolean;
  reloadUser: () => Promise<void>;
}): JSX.Element {
  return (
    <HitInterface
      buttonExists={props.userSet}
      onButtonClick={props.reloadUser}
      getButtonText={() => "↻"}
    />
  );
}
