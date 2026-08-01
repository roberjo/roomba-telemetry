import { useEffect, useState } from "react";
import { subscribeLiveStatus, type Status } from "../lib/api";
import Roombie from "./Roombie";

const PREFS: { key: keyof Status; label: string }[] = [
  { key: "pref_carpet_boost", label: "Carpet boost" },
  { key: "pref_vac_high", label: "Max vacuum" },
  { key: "pref_two_pass", label: "Two-pass cleaning" },
  { key: "pref_eco_charge", label: "Eco charge" },
  { key: "pref_bin_pause", label: "Pause on full bin" },
];

/** Read-only — these are configured via the iRobot app; the local API exposes
 * them as plain booleans in every state update, so surfacing them here is free. */
export default function PreferencesCard() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => subscribeLiveStatus(setStatus), []);

  return (
    <section className="card">
      <h2>Preferences</h2>
      {!status ? (
        <div className="empty-state">
          <Roombie mood="thinking" size={40} />
          <p>Waiting for a status update…</p>
        </div>
      ) : (
        <ul className="pref-list">
          {PREFS.map(({ key, label }) => {
            const value = status[key] as boolean | null;
            return (
              <li key={key}>
                <span>{label}</span>
                <span className={`pref-pill${value ? " pref-on" : ""}`}>
                  {value == null ? "—" : value ? "On" : "Off"}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
