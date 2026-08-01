// Fetch + WebSocket client for the FastAPI backend (see ../../../api).
// Mirrors api/api/schemas.py — mapping-only fields are always optional and
// must be null-checked before rendering (see PROJECT.md's core design principle).

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export type ModelClass = "non-mapping" | "mapping";

export interface Status {
  received_at: number;
  model_class: ModelClass;

  battery_pct: number | null;
  bin_present: boolean | null;
  bin_full: boolean | null;
  cycle: string | null;
  phase: string | null;
  error_code: number | null;
  not_ready_code: number | null;
  mission_minutes: number | null;
  mission_sqft: number | null;
  mission_initiator: string | null;

  // mapping-model-only — always check for null, even if model_class === "mapping"
  pose_x: number | null;
  pose_y: number | null;
  pose_theta: number | null;
}

export interface Mission {
  id: number;
  started_at: number;
  ended_at: number | null;
  initiator: string | null;
  outcome: string | null;
  duration_minutes: number | null;
  area_sqft: number | null;
  battery_start_pct: number | null;
  battery_end_pct: number | null;
}

export interface ErrorEvent {
  id: number;
  occurred_at: number;
  error_code: number;
  mission_id: number | null;
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export const api = {
  getStatus: () => getJSON<Status>("/status"),
  listMissions: (limit = 50, offset = 0) =>
    getJSON<Mission[]>(`/missions?limit=${limit}&offset=${offset}`),
  getMission: (id: number) => getJSON<Mission>(`/missions/${id}`),
  listErrors: (limit = 50, offset = 0) =>
    getJSON<ErrorEvent[]>(`/errors?limit=${limit}&offset=${offset}`),
};

/** Subscribes to /live; returns an unsubscribe function. */
export function subscribeLiveStatus(
  onStatus: (status: Status) => void,
  onError?: (event: Event) => void,
): () => void {
  const ws = new WebSocket(`${WS_BASE_URL}/live`);

  ws.onmessage = (event) => {
    onStatus(JSON.parse(event.data) as Status);
  };
  if (onError) {
    ws.onerror = onError;
  }

  return () => ws.close();
}
