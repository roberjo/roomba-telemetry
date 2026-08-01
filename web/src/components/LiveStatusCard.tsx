import { useEffect, useState } from "react";
import { api, subscribeLiveStatus, type Status } from "../lib/api";

export default function LiveStatusCard() {
  const [status, setStatus] = useState<Status | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    api.getStatus().then(setStatus).catch(() => {});

    const unsubscribe = subscribeLiveStatus(
      (next) => {
        setStatus(next);
        setConnected(true);
      },
      () => setConnected(false),
    );
    return unsubscribe;
  }, []);

  if (!status) {
    return <section className="card">Waiting for status…</section>;
  }

  return (
    <section className="card">
      <h2>
        Live status <span className={connected ? "dot dot-live" : "dot"} />
      </h2>
      <dl>
        <dt>Phase</dt>
        <dd>{status.phase ?? "unknown"}</dd>

        <dt>Battery</dt>
        <dd>{status.battery_pct != null ? `${status.battery_pct}%` : "—"}</dd>

        <dt>Bin</dt>
        <dd>{status.bin_full == null ? "—" : status.bin_full ? "Full" : "OK"}</dd>

        <dt>Error</dt>
        <dd>{status.error_code ? `Code ${status.error_code}` : "None"}</dd>
      </dl>
    </section>
  );
}
