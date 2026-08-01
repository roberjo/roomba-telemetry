"""Spins up a throwaway SQLite DB with the collector's schema so API tests don't
need a running collector or a real robot."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

SCHEMA = """
CREATE TABLE state_snapshots (
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
    robot_name TEXT,
    sku TEXT,
    software_version TEXT,
    last_command TEXT,
    last_command_initiator TEXT,
    last_command_time INTEGER,
    pref_carpet_boost INTEGER,
    pref_vac_high INTEGER,
    pref_two_pass INTEGER,
    pref_eco_charge INTEGER,
    pref_bin_pause INTEGER,
    schedule_json TEXT,
    pose_x REAL,
    pose_y REAL,
    pose_theta REAL
);

CREATE TABLE missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at REAL NOT NULL,
    ended_at REAL,
    initiator TEXT,
    outcome TEXT,
    duration_minutes INTEGER,
    area_sqft REAL,
    battery_start_pct INTEGER,
    battery_end_pct INTEGER
);

CREATE TABLE errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at REAL NOT NULL,
    error_code INTEGER NOT NULL,
    mission_id INTEGER REFERENCES missions (id)
);
"""


@pytest.fixture()
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "roomba-test.db"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    monkeypatch.setenv("ROOMBA_DB_PATH", str(path))
    return path


@pytest.fixture()
def client(db_path: Path):
    # Imported after ROOMBA_DB_PATH is set, since api.db reads it at call time
    # via get_connection() — safe either way, but keep the dependency explicit.
    from fastapi.testclient import TestClient

    from api.main import create_app

    return TestClient(create_app())
