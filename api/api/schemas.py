"""Pydantic response models. Mirrors collector/collector/normalize.py's NormalizedState —
mapping-only fields are always Optional and must be null-checked by consumers."""

from __future__ import annotations

import json
import sqlite3

from pydantic import BaseModel


class WeeklySchedule(BaseModel):
    # index 0 = Sunday, matching the robot's own convention (see cleanSchedule
    # in a raw payload — h/m are local start times, cycle is "clean" or "none")
    cycle: list[str | None]
    hour: list[int | None]
    minute: list[int | None]


class StatusResponse(BaseModel):
    received_at: float
    model_class: str

    battery_pct: int | None = None
    bin_present: bool | None = None
    bin_full: bool | None = None
    cycle: str | None = None
    phase: str | None = None
    error_code: int | None = None
    not_ready_code: int | None = None
    mission_minutes: int | None = None
    mission_sqft: float | None = None
    mission_initiator: str | None = None

    # device identity — static, but re-sent with every state update
    robot_name: str | None = None
    sku: str | None = None
    software_version: str | None = None

    # last command provenance
    last_command: str | None = None
    last_command_initiator: str | None = None
    last_command_time: int | None = None

    # cleaning preferences (read-only)
    pref_carpet_boost: bool | None = None
    pref_vac_high: bool | None = None
    pref_two_pass: bool | None = None
    pref_eco_charge: bool | None = None
    pref_bin_pause: bool | None = None

    schedule: WeeklySchedule | None = None

    # mapping-model-only
    pose_x: float | None = None
    pose_y: float | None = None
    pose_theta: float | None = None


class Mission(BaseModel):
    id: int
    started_at: float
    ended_at: float | None = None
    initiator: str | None = None
    outcome: str | None = None
    duration_minutes: int | None = None
    area_sqft: float | None = None
    battery_start_pct: int | None = None
    battery_end_pct: int | None = None


class ErrorEvent(BaseModel):
    id: int
    occurred_at: float
    error_code: int
    mission_id: int | None = None


def status_response_from_row(row: sqlite3.Row) -> StatusResponse:
    """Builds a StatusResponse from a state_snapshots row, decoding the
    JSON-encoded schedule column into a structured field."""
    d = dict(row)
    schedule_json = d.pop("schedule_json", None)
    if schedule_json:
        raw = json.loads(schedule_json)
        d["schedule"] = WeeklySchedule(cycle=raw["cycle"], hour=raw["hour"], minute=raw["minute"])
    return StatusResponse(**d)
