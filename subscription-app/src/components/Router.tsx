import { useLocalStorage } from "usehooks-ts";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SearchPage } from "./SearchPage";
import { SubscriptionManager } from "./SubscriptionManager";
import { makeUser } from "../utils/InvokeLambda";
import { NotFound } from "./NotFound";
import { User } from "../types/User";

export function Router(): JSX.Element {
  const [user, setUser] = useLocalStorage<User | null>("user", null);

  async function reloadUser(): Promise<void> {
    if (user) {
      setUser(await makeUser(user.email));
    } else {
      console.error("Trying to refresh user when no user is loaded.");
    }
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <SearchPage user={user} setUser={setUser} reloadUser={reloadUser} />
          }
        />
        <Route
          path="/manage"
          element={
            <SubscriptionManager
              user={user}
              setUser={setUser}
              reloadUser={reloadUser}
            />
          }
        />
        <Route path="/:anythingelse" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
