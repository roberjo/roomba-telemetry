import { useEffect, useState } from "react";
import { api, type ModelClass } from "./lib/api";
import CommandCenter from "./components/CommandCenter";
import MissionHistoryTable from "./components/MissionHistoryTable";
import BatteryChart from "./components/BatteryChart";
import ScheduleCard from "./components/ScheduleCard";
import ErrorLog from "./components/ErrorLog";
import DeviceInfo from "./components/DeviceInfo";
import PreferencesCard from "./components/PreferencesCard";
import MapView from "./components/MapView";
import "./App.css";

export default function App() {
  const [modelClass, setModelClass] = useState<ModelClass | null>(null);
  const [robotName, setRobotName] = useState<string | null>(null);

  useEffect(() => {
    api
      .getStatus()
      .then((s) => {
        setModelClass(s.model_class);
        setRobotName(s.robot_name);
      })
      .catch(() => {});
  }, []);

  return (
    <main>
      <header className="hero">
        <div className="hero-brand">
          <svg className="brand-mark" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="brand-grad" x1="4" y1="4" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#2dd4ee" />
                <stop offset="60%" stopColor="#7c8cf8" />
                <stop offset="100%" stopColor="#b083f7" />
              </linearGradient>
            </defs>
            <circle cx="26" cy="26" r="23" stroke="url(#brand-grad)" strokeWidth="2.5" />
            <circle cx="26" cy="26" r="14.5" stroke="url(#brand-grad)" strokeWidth="1.5" opacity="0.55" />
            <circle cx="26" cy="26" r="4.5" fill="url(#brand-grad)" />
            <circle cx="26" cy="8.5" r="2.2" fill="url(#brand-grad)" />
          </svg>
          <div>
            <h1>Roomba Telemetry</h1>
            <p className="hero-tagline">
              {robotName ? `Connected to "${robotName}"` : "Local-first robotics monitoring & control"}
            </p>
          </div>
        </div>
        <span className="hero-badge">
          <span className="dot dot-live" />
          Local network
        </span>
      </header>

      {/* Everything you'd act on right now: live status + controls together. */}
      <CommandCenter />

      {/* Spatial context is high-value live data when available — features it
       * right under the command center rather than burying it in the grid below. */}
      {modelClass === "mapping" && <MapView />}

      {/* History & diagnostics: trend/log data grouped separately from the live
       * section above, main column + a narrower side rail instead of one long
       * single-column scroll. */}
      <div className="insights-grid">
        <div className="insights-main">
          <BatteryChart />
          <MissionHistoryTable />
          <ScheduleCard />
        </div>
        <div className="insights-side">
          <DeviceInfo />
          <PreferencesCard />
          <ErrorLog />
        </div>
      </div>
    </main>
  );
}
