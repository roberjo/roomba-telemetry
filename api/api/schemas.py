"""Pydantic response models. Mirrors collector/collector/normalize.py's NormalizedState —
mapping-only fields are always Optional and must be null-checked by consumers."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


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
