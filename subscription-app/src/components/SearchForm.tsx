import { useState, ChangeEvent, FormEvent } from "react";
import "../styles/SearchForm.css";

export function SearchForm(props: {
  performSearch: (query: string) => Promise<void>;
  hasHits: boolean;
  clearSearch: () => void;
}): JSX.Element {
  const [query, setQuery] = useState("");

  function onChange(event: ChangeEvent<HTMLInputElement>): void {
    event.preventDefault();
    setQuery(event.currentTarget.value);
  }

  async function onSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    await props.performSearch(query);
  }

  return (
    <div>
      <form className="SignupForm" onSubmit={onSubmit}>
        <div>
          <input
            type="text"
            name="query"
            onChange={onChange}
            placeholder="Put something here!"
            value={query}
          />
          <button className="SearchButton">Search</button>
        </div>
      </form>
      {props.hasHits ? (
        <button
          className="ClearSearchButton"
          onClick={() => {
            props.clearSearch();
            setQuery("");
          }}
        >
          Clear
        </button>
      ) : null}
    </div>
  );
}
