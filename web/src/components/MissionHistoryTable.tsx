import { useEffect, useState } from "react";
import { api, type Mission } from "../lib/api";

export default function MissionHistoryTable() {
  const [missions, setMissions] = useState<Mission[]>([]);

  useEffect(() => {
    api.listMissions().then(setMissions).catch(() => {});
  }, []);

  return (
    <section className="card">
      <h2>Mission history</h2>
      {missions.length === 0 ? (
        <p>No missions recorded yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Started</th>
              <th>Outcome</th>
              <th>Duration</th>
              <th>Area</th>
            </tr>
          </thead>
          <tbody>
            {missions.map((m) => (
              <tr key={m.id}>
                <td>{new Date(m.started_at * 1000).toLocaleString()}</td>
                <td>{m.outcome ?? "in progress"}</td>
                <td>{m.duration_minutes != null ? `${m.duration_minutes} min` : "—"}</td>
                <td>{m.area_sqft != null ? `${m.area_sqft} sqft` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
