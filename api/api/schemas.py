"""Pydantic response models. Mirrors collector/collector/normalize.py's NormalizedState —
mapping-only fields are always Optional and must be null-checked by consumers."""

from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from pydantic import BaseModel


class WeeklySchedule(BaseModel):
    # index 0 = Sunday, matching the robot's own convention (see cleanSchedule
    # in a raw payload — h/m are local start times, cycle is "clean" or "none")
    cycle: List[Optional[str]]
    hour: List[Optional[int]]
    minute: List[Optional[int]]


class StatusResponse(BaseModel):
    received_at: float
    model_class: str

    battery_pct: Optional[int] = None
    bin_present: Optional[bool] = None
    bin_full: Optional[bool] = None
    cycle: Optional[str] = None
    phase: Optional[str] = None
    error_code: Optional[int] = None
    not_ready_code: Optional[int] = None
    mission_minutes: Optional[int] = None
    mission_sqft: Optional[float] = None
    mission_initiator: Optional[str] = None

    # device identity — static, but re-sent with every state update
    robot_name: Optional[str] = None
    sku: Optional[str] = None
    software_version: Optional[str] = None

    # last command provenance
    last_command: Optional[str] = None
    last_command_initiator: Optional[str] = None
    last_command_time: Optional[int] = None

    # cleaning preferences (read-only)
    pref_carpet_boost: Optional[bool] = None
    pref_vac_high: Optional[bool] = None
    pref_two_pass: Optional[bool] = None
    pref_eco_charge: Optional[bool] = None
    pref_bin_pause: Optional[bool] = None

    schedule: Optional[WeeklySchedule] = None

    # mapping-model-only
    pose_x: Optional[float] = None
    pose_y: Optional[float] = None
    pose_theta: Optional[float] = None


class Mission(BaseModel):
    id: int
    started_at: float
    ended_at: Optional[float] = None
    initiator: Optional[str] = None
    outcome: Optional[str] = None
    duration_minutes: Optional[int] = None
    area_sqft: Optional[float] = None
    battery_start_pct: Optional[int] = None
    battery_end_pct: Optional[int] = None


class ErrorEvent(BaseModel):
    id: int
    occurred_at: float
    error_code: int
    mission_id: Optional[int] = None


def status_response_from_row(row: sqlite3.Row) -> StatusResponse:
    """Builds a StatusResponse from a state_snapshots row, decoding the
    JSON-encoded schedule column into a structured field."""
    d = dict(row)
    schedule_json = d.pop("schedule_json", None)
    if schedule_json:
        raw = json.loads(schedule_json)
        d["schedule"] = WeeklySchedule(cycle=raw["cycle"], hour=raw["hour"], minute=raw["minute"])
    return StatusResponse(**d)
