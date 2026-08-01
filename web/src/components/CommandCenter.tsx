import { useEffect, useState } from "react";
import { api, subscribeLiveStatus, type MissionCommand, type Status } from "../lib/api";
import Roombie, { statusMood, type RoombieMood } from "./Roombie";

const COMMAND_ERROR_DISPLAY_MS = 5000;

const GAUGE_RADIUS = 51;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;

const PlayIcon = () => (
  <svg viewBox="0 0 16 16" fill="currentColor">
    <path d="M4 2.5v11l10-5.5-10-5.5Z" />
  </svg>
);

const StopIcon = () => (
  <svg viewBox="0 0 16 16" fill="currentColor">
    <rect x="3.5" y="3.5" width="9" height="9" rx="1.5" />
  </svg>
);

const HomeIcon = () => (
  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round">
    <path d="M2 7.5 8 2.5l6 5v6a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-6Z" />
  </svg>
);

const FindIcon = () => (
  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="7" cy="7" r="4.5" />
    <path d="M10.3 10.3 13.5 13.5" strokeLinecap="round" />
  </svg>
);

const SpotIcon = () => (
  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="8" cy="8" r="5.5" />
    <circle cx="8" cy="8" r="1.5" fill="currentColor" stroke="none" />
  </svg>
);

function batteryColor(pct: number | null): string {
  if (pct == null) return "var(--text-tertiary)";
  if (pct < 20) return "var(--red)";
  if (pct < 50) return "var(--amber)";
  return "var(--teal)";
}

function phaseBadge(status: Status): { label: string; className: string } {
  if (status.error_code) return { label: `Error ${status.error_code}`, className: "badge-danger" };
  switch (status.phase) {
    case "run":
      return { label: "Cleaning", className: "badge-success" };
    case "charge":
      return { label: "Charging", className: "badge-info" };
    case "stop":
    case "hmUsrDock":
      return { label: "Docked", className: "badge-neutral" };
    default:
      return { label: status.phase ?? "Unknown", className: "badge-neutral" };
  }
}

/** The primary "what's happening + what can I do about it" panel — status and
 * controls live together so acting on what you see doesn't mean jumping
 * between separate cards. A single live-status subscription backs both
 * halves (the gauge/badges and the Start button's "already running" state). */
export default function CommandCenter() {
  const [status, setStatus] = useState<Status | null>(null);
  const [connected, setConnected] = useState(false);
  const [pending, setPending] = useState<MissionCommand | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  // Clears the command-send error after a few seconds so it doesn't linger
  // forever and so Roombie's face reverts back to reflecting real robot state.
  useEffect(() => {
    if (!error) return;
    const timer = setTimeout(() => setError(null), COMMAND_ERROR_DISPLAY_MS);
    return () => clearTimeout(timer);
  }, [error]);

  async function send(command: MissionCommand) {
    setPending(command);
    setError(null);
    try {
      await api.sendCommand(command);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPending(null);
    }
  }

  const isCleaning = status?.phase === "run" && !status.error_code;
  const pct = status?.battery_pct ?? null;
  const color = batteryColor(pct);
  const dashoffset = GAUGE_CIRCUMFERENCE * (1 - (pct ?? 0) / 100);
  const badge = status ? phaseBadge(status) : null;

  // Roombie's face reflects real robot state, but momentarily reacts to the
  // outcome of a command you just sent — "thinking" while it's in flight,
  // "error" if it failed — before settling back to whatever's actually true.
  const mood: RoombieMood = pending !== null ? "thinking" : error ? "error" : statusMood(status);

  return (
    <section className="card command-center">
      <h2>
        Command center <span className={connected ? "dot dot-live" : "dot"} />
      </h2>

      {!status ? (
        <div className="empty-state">
          <Roombie mood="thinking" size={64} />
          <p>Waiting for a status update…</p>
        </div>
      ) : (
        <div className="command-grid">
          <div className="command-status">
            <Roombie mood={mood} size={104} className="roombie-hero" />
            <div className={isCleaning ? "gauge gauge-active" : "gauge"}>
              <svg viewBox="0 0 116 116">
                <circle className="gauge-track" cx="58" cy="58" r={GAUGE_RADIUS} />
                <circle
                  className="gauge-value"
                  cx="58"
                  cy="58"
                  r={GAUGE_RADIUS}
                  style={{ stroke: color, strokeDasharray: GAUGE_CIRCUMFERENCE, strokeDashoffset: dashoffset }}
                />
              </svg>
              <div className="gauge-label">
                <strong style={{ color }}>{pct != null ? pct : "—"}</strong>
                <span>{pct != null ? "% battery" : "no data"}</span>
              </div>
            </div>

            <div className="stat-grid">
              <div className="stat">
                <span className="stat-label">Phase</span>
                <span className={`badge ${badge!.className}${isCleaning ? " badge-active" : ""}`}>
                  {badge!.label}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Bin</span>
                <span className="stat-value">{status.bin_full == null ? "—" : status.bin_full ? "Full" : "Clear"}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Cycle</span>
                <span className="stat-value">{status.cycle ?? "—"}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Mission time</span>
                <span className="stat-value">
                  {status.mission_minutes != null ? `${status.mission_minutes}m` : "—"}
                </span>
              </div>
            </div>
          </div>

          <div className="command-actions">
            <span className="card-label">Mission controls</span>
            <div className="button-row">
              <button
                className={`btn btn-primary${isCleaning ? " btn-active" : ""}`}
                disabled={pending !== null || isCleaning}
                onClick={() => send("start")}
              >
                {isCleaning ? <span className="dot dot-live" /> : <PlayIcon />}
                {pending === "start" ? "Starting…" : isCleaning ? "Cleaning in progress" : "Start Cleaning"}
              </button>
              <button className="btn btn-danger" disabled={pending !== null} onClick={() => send("stop")}>
                <StopIcon />
                {pending === "stop" ? "Stopping…" : "Stop"}
              </button>
              <button className="btn" disabled={pending !== null} onClick={() => send("dock")}>
                <HomeIcon />
                {pending === "dock" ? "Docking…" : "Send Home"}
              </button>
            </div>

            <div className="button-row button-row-compact">
              <button className="btn btn-sm" disabled={pending !== null} onClick={() => send("spot")}>
                <SpotIcon />
                {pending === "spot" ? "Spot cleaning…" : "Spot Clean"}
              </button>
              <button className="btn btn-sm" disabled={pending !== null} onClick={() => send("find")}>
                <FindIcon />
                {pending === "find" ? "Beeping…" : "Find Robot"}
              </button>
            </div>
            {error && <p className="error-text">{error}</p>}
          </div>
        </div>
      )}
    </section>
  );
}
