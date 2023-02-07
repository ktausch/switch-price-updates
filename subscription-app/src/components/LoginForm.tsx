import { useNavigate } from "react-router-dom";
import { useState, ChangeEvent, FormEvent } from "react";
import { User } from "../types/User";
import { makeUser } from "../utils/InvokeLambda";
import "../styles/LoginForm.css";

type ButtonInfo = {
  path: string;
  text: string;
};

export function LoginForm(props: {
  user: User | null;
  setUser: (user: User | null) => void;
}): JSX.Element {
  const [email, setEmail] = useState<string>("");
  const [buttonDisabled, setButtonDisabled] = useState(false);
  const navigate = useNavigate();

  function onChange(event: ChangeEvent<HTMLInputElement>): void {
    event.preventDefault();
    setEmail(event.currentTarget.value);
  }

  async function onLoginSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setButtonDisabled(true);
    props.setUser(await makeUser(email));
    setEmail("");
    setButtonDisabled(false);
  }

  function onLogoutSubmit(): void {
    props.setUser(null);
  }

  const buttonInfo: ButtonInfo =
    window.location.pathname === "/"
      ? { path: "/manage", text: "Go to subscription management page" }
      : { path: "/", text: "Go to search page" };
  return (
    <div className="LogInLogOut">
      <div className="LogInLogOutLeftEmptySpace" />
      <button
        className="LogInLogOutNavButton"
        onClick={() => {
          navigate(buttonInfo.path);
        }}
      >
        {buttonInfo.text}
      </button>
      {props.user ? (
        <form className="LogInLogOutForm" onSubmit={onLogoutSubmit}>
          <input type="text" disabled={true} defaultValue={props.user.email} />
          <button>Logout</button>
        </form>
      ) : (
        <form className="LogInLogOutForm" onSubmit={onLoginSubmit}>
          <input type="text" onChange={onChange} placeholder="email" />
          <button disabled={buttonDisabled}>Log in</button>
        </form>
      )}
      <div className="LogInLogOutRightEmptySpace" />
    </div>
  );
}
