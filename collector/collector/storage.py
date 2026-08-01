"""SQLite writer for normalized Roomba state.

Schema is intentionally minimal (see PROJECT.md §7 — a single `schema.sql` applied
on startup, no migration framework). Three tables:

- `state_snapshots` — one row per normalized state update, append-only.
- `missions` — one row per completed mission, derived from phase transitions.
- `errors` — one row per non-zero error code observed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .normalize import NormalizedState

SCHEMA = """
CREATE TABLE IF NOT EXISTS state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at REAL NOT NULL,
    model_class TEXT NOT NULL,
    battery_pct INTEGER,
    bin_present INTEGER,
    bin_full INTEGER,
    cycle TEXT,
    phase TEXT,
    error_code INTEGER,
    not_ready_code INTEGER,
    mission_minutes INTEGER,
    mission_sqft REAL,
    mission_initiator TEXT,
    pose_x REAL,
    pose_y REAL,
    pose_theta REAL
);

CREATE INDEX IF NOT EXISTS idx_state_snapshots_received_at
    ON state_snapshots (received_at);

CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at REAL NOT NULL,
    ended_at REAL,
    initiator TEXT,
    outcome TEXT,           -- "completed" | "error" | "cancelled" | NULL (in progress)
    duration_minutes INTEGER,
    area_sqft REAL,
    battery_start_pct INTEGER,
    battery_end_pct INTEGER
);

CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at REAL NOT NULL,
    error_code INTEGER NOT NULL,
    mission_id INTEGER REFERENCES missions (id)
);
"""


class Storage:
    def __init__(self, db_path: str | Path):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def write_snapshot(self, state: NormalizedState) -> None:
        d = state.to_dict()
        self._conn.execute(
            """
            INSERT INTO state_snapshots (
                received_at, model_class, battery_pct, bin_present, bin_full,
                cycle, phase, error_code, not_ready_code, mission_minutes,
                mission_sqft, mission_initiator, pose_x, pose_y, pose_theta
            ) VALUES (
                :received_at, :model_class, :battery_pct, :bin_present, :bin_full,
                :cycle, :phase, :error_code, :not_ready_code, :mission_minutes,
                :mission_sqft, :mission_initiator, :pose_x, :pose_y, :pose_theta
            )
            """,
            d,
        )
        if d.get("error_code"):
            self._conn.execute(
                "INSERT INTO errors (occurred_at, error_code) VALUES (?, ?)",
                (d["received_at"], d["error_code"]),
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
