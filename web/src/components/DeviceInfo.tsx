import { useEffect, useState } from "react";
import { subscribeLiveStatus, type Status } from "../lib/api";
import Roombie from "./Roombie";

function timeAgo(unixSeconds: number): string {
  const diffMin = Math.round((Date.now() / 1000 - unixSeconds) / 60);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${Math.round(diffHr / 24)}d ago`;
}

/** Device identity + who/what last controlled it — fields the local API
 * re-sends with every state update but this dashboard didn't previously show. */
export default function DeviceInfo() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => subscribeLiveStatus(setStatus), []);

  if (!status) {
    return (
      <section className="card">
        <h2>Device</h2>
        <div className="empty-state">
          <Roombie mood="thinking" size={40} />
          <p>Waiting for a status update…</p>
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Device</h2>
      <dl className="kv-list">
        <dt>Model</dt>
        <dd>{status.sku ?? "—"}</dd>
        <dt>Firmware</dt>
        <dd>{status.software_version ?? "—"}</dd>
        <dt>Last command</dt>
        <dd>
          {status.last_command ? (
            <>
              {status.last_command}
              <span className="kv-sub">
                {" "}
                via {status.last_command_initiator ?? "unknown"}
                {status.last_command_time != null && ` · ${timeAgo(status.last_command_time)}`}
              </span>
            </>
          ) : (
            "—"
          )}
        </dd>
      </dl>
    </section>
  );
}
