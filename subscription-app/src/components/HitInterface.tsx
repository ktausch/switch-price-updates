import { useState } from "react";
import "../styles/SingleHit.css";

export function HitInterface(props: {
  buttonExists: boolean;
  onButtonClick: () => Promise<void>;
  getButtonText: () => string;
  renderTitle?: () => JSX.Element;
  renderSlug?: () => JSX.Element;
  renderPrice?: () => JSX.Element;
  renderDescription?: () => JSX.Element;
  renderBoxArt?: () => JSX.Element;
}): JSX.Element {
  const [buttonDisabled, setButtonDisabled] = useState(false);

  async function onClick(): Promise<void> {
    setButtonDisabled(true);
    await props.onButtonClick();
    setButtonDisabled(false);
  }

  function renderPiece(
    renderFunction: (() => JSX.Element) | undefined
  ): JSX.Element | null {
    return renderFunction ? renderFunction() : null;
  }

  return (
    <div>
      {renderPiece(props.renderTitle)}
      <div className="SingleHit">
        <div className="SingleHitText">
          {renderPiece(props.renderSlug)}
          {renderPiece(props.renderPrice)}
          {renderPiece(props.renderDescription)}
        </div>
        <div className="SingleHitBoxArt">{renderPiece(props.renderBoxArt)}</div>
        <div className="SingleHitSubscribe">
          {props.buttonExists ? (
            <button onClick={onClick} disabled={buttonDisabled}>
              {props.getButtonText()}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
