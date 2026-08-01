import { useEffect, useState } from "react";
import { api, type ErrorEvent } from "../lib/api";

export default function ErrorLog() {
  const [errors, setErrors] = useState<ErrorEvent[]>([]);

  useEffect(() => {
    api.listErrors().then(setErrors).catch(() => {});
  }, []);

  if (errors.length === 0) {
    return <section className="card">No errors recorded.</section>;
  }

  return (
    <section className="card">
      <h2>Error log</h2>
      <ul>
        {errors.map((e) => (
          <li key={e.id}>
            {new Date(e.occurred_at * 1000).toLocaleString()} — code {e.error_code}
          </li>
        ))}
      </ul>
    </section>
  );
}
