import { useEffect, useState } from "react";
import { api, type ErrorEvent } from "../lib/api";

export default function ErrorLog() {
  const [errors, setErrors] = useState<ErrorEvent[]>([]);

  useEffect(() => {
    api.listErrors().then(setErrors).catch(() => {});
  }, []);

  return (
    <section className="card">
      <h2>Error log</h2>
      {errors.length === 0 ? (
        <p>No errors recorded.</p>
      ) : (
        <ul className="timeline">
          {errors.map((e) => (
            <li key={e.id}>
              <time>{new Date(e.occurred_at * 1000).toLocaleString()}</time>
              <span>code {e.error_code}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
