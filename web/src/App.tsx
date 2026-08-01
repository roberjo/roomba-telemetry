import { useEffect, useState } from "react";
import { api, type ModelClass } from "./lib/api";
import LiveStatusCard from "./components/LiveStatusCard";
import MissionHistoryTable from "./components/MissionHistoryTable";
import BatteryChart from "./components/BatteryChart";
import ErrorLog from "./components/ErrorLog";
import MapView from "./components/MapView";
import "./App.css";

export default function App() {
  const [modelClass, setModelClass] = useState<ModelClass | null>(null);

  useEffect(() => {
    api
      .getStatus()
      .then((s) => setModelClass(s.model_class))
      .catch(() => {});
  }, []);

  return (
    <main>
      <h1>Roomba Telemetry</h1>
      <div className="grid">
        <LiveStatusCard />
        {modelClass === "mapping" && <MapView />}
        <BatteryChart />
        <MissionHistoryTable />
        <ErrorLog />
      </div>
    </main>
  );
}
