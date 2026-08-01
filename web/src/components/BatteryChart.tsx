import { useEffect, useState } from "react";
import { api, type Mission } from "../lib/api";

const WIDTH = 480;
const HEIGHT = 130;
const PAD_Y = 12;

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

  return (
    <section className="card">
      <h2>Battery at mission start</h2>
      {points.length < 2 ? (
        <p>Not enough missions yet for a battery trend.</p>
      ) : (
        (() => {
          const line = points
            .map((m, i) => {
              const x = (i / (points.length - 1)) * WIDTH;
              const y = HEIGHT - PAD_Y - ((m.battery_start_pct as number) / 100) * (HEIGHT - PAD_Y * 2);
              return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
            })
            .join(" ");
          const area = `${line} L ${WIDTH} ${HEIGHT} L 0 ${HEIGHT} Z`;

          return (
            <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} width="100%" height={HEIGHT} role="img">
              <defs>
                <linearGradient id="battery-line" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#2dd4ee" />
                  <stop offset="100%" stopColor="#b083f7" />
                </linearGradient>
                <linearGradient id="battery-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2dd4ee" stopOpacity="0.28" />
                  <stop offset="100%" stopColor="#2dd4ee" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path d={area} fill="url(#battery-fill)" stroke="none" />
              <path
                d={line}
                fill="none"
                stroke="url(#battery-line)"
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ filter: "drop-shadow(0 0 5px rgba(45, 212, 238, 0.5))" }}
              />
            </svg>
          );
        })()
      )}
    </section>
  );
}
