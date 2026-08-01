import { useEffect, useState } from "react";
import { api, type ModelClass } from "./lib/api";
import Roombie from "./components/Roombie";
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
          <Roombie mood="happy" size={52} className="brand-mark" />
          <div>
            <h1>Roomba Telemetry</h1>
            <p className="hero-tagline">
              {robotName ? `Roombie is watching over "${robotName}"` : "Local-first robotics monitoring & control"}
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
