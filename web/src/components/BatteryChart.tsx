import { useEffect, useState } from "react";
import { api, type Mission } from "../lib/api";

const WIDTH = 480;
const HEIGHT = 120;

/** Battery-at-start-of-mission over time — a plain inline SVG sparkline to avoid
 * pulling in a charting library for one chart (see docs/experiments for the
 * fuller "battery health tracker" idea this is a seed of). */
export default function BatteryChart() {
  const [missions, setMissions] = useState<Mission[]>([]);

  useEffect(() => {
    api.listMissions(100).then(setMissions).catch(() => {});
  }, []);

  const points = missions
    .filter((m) => m.battery_start_pct != null)
    .slice()
    .reverse();

  if (points.length < 2) {
    return <section className="card">Not enough missions yet for a battery trend.</section>;
  }

  const path = points
    .map((m, i) => {
      const x = (i / (points.length - 1)) * WIDTH;
      const y = HEIGHT - ((m.battery_start_pct as number) / 100) * HEIGHT;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <section className="card">
      <h2>Battery at mission start</h2>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} width="100%" height={HEIGHT} role="img">
        <path d={path} fill="none" stroke="currentColor" strokeWidth={2} />
      </svg>
    </section>
  );
}
