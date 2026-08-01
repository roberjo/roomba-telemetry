import { useEffect, useState } from "react";
import { subscribeLiveStatus, type Status } from "../lib/api";

const SIZE = 320;
// Roomba pose units are millimeters, origin at the dock. Scale down to fit the
// view — tune once real fixture data shows a typical room's coordinate range.
const SCALE = 0.08;

/** Only meaningful for mapping-capable robots — callers should not render this
 * unless `status.model_class === "mapping"` (see PROJECT.md's capability matrix).
 * Even then, pose may be briefly absent (e.g. mid-charge), so this still
 * null-checks before drawing anything. */
export default function MapView() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => subscribeLiveStatus(setStatus), []);

  const hasPose = status?.pose_x != null && status?.pose_y != null;

  return (
    <section className="card">
      <h2>Live position</h2>
      {!hasPose ? (
        <p>No pose data (robot may be docked or between missions).</p>
      ) : (
        <svg className="map-frame" viewBox={`0 0 ${SIZE} ${SIZE}`} width="100%" height={SIZE} role="img">
          <circle
            className="map-blip-ring"
            cx={SIZE / 2 + (status!.pose_x as number) * SCALE}
            cy={SIZE / 2 - (status!.pose_y as number) * SCALE}
            r={6}
          />
          <circle
            className="map-blip"
            cx={SIZE / 2 + (status!.pose_x as number) * SCALE}
            cy={SIZE / 2 - (status!.pose_y as number) * SCALE}
            r={5}
          />
        </svg>
      )}
    </section>
  );
}
