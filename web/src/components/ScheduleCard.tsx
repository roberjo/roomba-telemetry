import { useEffect, useState } from "react";
import { subscribeLiveStatus, type Status } from "../lib/api";
import Roombie from "./Roombie";

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatTime(hour: number | null, minute: number | null): string {
  if (hour == null || minute == null) return "";
  const period = hour >= 12 ? "PM" : "AM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${h12}:${minute.toString().padStart(2, "0")} ${period}`;
}

/** The robot's onboard weekly schedule — already present in every state update
 * (`cleanSchedule`), no separate read command needed. */
export default function ScheduleCard() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => subscribeLiveStatus(setStatus), []);

  const schedule = status?.schedule;

  return (
    <section className="card">
      <h2>Weekly schedule</h2>
      {!schedule ? (
        <div className="empty-state">
          <Roombie mood={status ? "idle" : "thinking"} size={40} />
          <p>{status ? "No schedule data yet." : "Waiting for a status update…"}</p>
        </div>
      ) : (
        <ul className="schedule-list">
          {DAY_LABELS.map((label, i) => {
            const active = schedule.cycle[i] && schedule.cycle[i] !== "none";
            return (
              <li key={label} className={active ? "schedule-active" : ""}>
                <span className="schedule-day">{label}</span>
                <span>{active ? formatTime(schedule.hour[i], schedule.minute[i]) : "No clean scheduled"}</span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
