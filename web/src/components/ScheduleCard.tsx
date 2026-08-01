import { useEffect, useState } from "react";
import { subscribeLiveStatus, type Status, type WeeklySchedule } from "../lib/api";
import Roombie from "./Roombie";

const DAY_SHORT = ["S", "M", "T", "W", "T", "F", "S"];
const DAY_LABEL = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const DAY_FULL = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function isActive(schedule: WeeklySchedule, day: number): boolean {
  return Boolean(schedule.cycle[day]) && schedule.cycle[day] !== "none";
}

function formatTime(hour: number | null, minute: number | null): string {
  if (hour == null || minute == null) return "";
  const period = hour >= 12 ? "PM" : "AM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${h12}:${minute.toString().padStart(2, "0")} ${period}`;
}

/** The single most useful fact on this card — when's the next clean — found by
 * walking forward from right now (assumes the robot's schedule times are in the
 * same timezone as whoever's looking at this dashboard, which holds for a local
 * network tool used near the robot itself). */
function findNext(schedule: WeeklySchedule): { day: number; time: string; daysAway: number } | null {
  const now = new Date();
  const nowMinutes = now.getHours() * 60 + now.getMinutes();

  for (let offset = 0; offset < 7; offset++) {
    const day = (now.getDay() + offset) % 7;
    if (!isActive(schedule, day)) continue;
    const hour = schedule.hour[day];
    const minute = schedule.minute[day];
    if (hour == null || minute == null) continue;
    if (offset === 0 && hour * 60 + minute <= nowMinutes) continue; // already passed today
    return { day, time: formatTime(hour, minute), daysAway: offset };
  }
  return null;
}

/** Groups days that share the same clean time — "Mon, Wed, Fri · 9:00 AM"
 * instead of three separate, repetitive lines. */
function groupByTime(schedule: WeeklySchedule): { days: string[]; time: string }[] {
  const order: string[] = [];
  const groups = new Map<string, string[]>();

  for (let day = 0; day < 7; day++) {
    if (!isActive(schedule, day)) continue;
    const time = formatTime(schedule.hour[day], schedule.minute[day]);
    if (!time) continue;
    if (!groups.has(time)) {
      groups.set(time, []);
      order.push(time);
    }
    groups.get(time)!.push(DAY_LABEL[day]);
  }

  return order.map((time) => ({ time, days: groups.get(time)! }));
}

/** The robot's onboard weekly schedule — already present in every state update
 * (`cleanSchedule`), no separate read command needed. Redesigned to lead with
 * "when's the next clean" (the actual question people have) rather than a flat
 * 7-row list that's mostly "No clean scheduled" repeated. */
export default function ScheduleCard() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => subscribeLiveStatus(setStatus), []);

  const schedule = status?.schedule;

  if (!schedule) {
    return (
      <section className="card">
        <h2>Weekly schedule</h2>
        <div className="empty-state">
          <Roombie mood={status ? "idle" : "thinking"} size={40} />
          <p>{status ? "No schedule data yet." : "Waiting for a status update…"}</p>
        </div>
      </section>
    );
  }

  const next = findNext(schedule);
  const groups = groupByTime(schedule);

  return (
    <section className="card">
      <h2>Weekly schedule</h2>

      <p className="schedule-next">
        {next ? (
          <>
            Next clean:{" "}
            <strong>
              {next.daysAway === 0 ? "Today" : next.daysAway === 1 ? "Tomorrow" : DAY_FULL[next.day]} at{" "}
              {next.time}
            </strong>
          </>
        ) : (
          "No cleanings scheduled"
        )}
      </p>

      <div className="day-strip">
        {DAY_SHORT.map((label, i) => (
          <span
            key={i}
            className={`day-pill${isActive(schedule, i) ? " day-pill-active" : ""}${
              next?.day === i ? " day-pill-next" : ""
            }`}
            title={DAY_LABEL[i]}
          >
            {label}
          </span>
        ))}
      </div>

      {groups.length > 0 && (
        <ul className="schedule-groups">
          {groups.map(({ days, time }) => (
            <li key={time}>
              <span>{days.join(", ")}</span>
              <span className="schedule-group-time">{time}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
