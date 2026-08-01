"""Normalizes raw Roomba MQTT state payloads into one stable internal schema.

The local API reports a `state.reported` JSON blob whose shape varies by firmware
and hardware generation. This module is the single place that knows how to read
that mess defensively — every other part of the system (storage, API, frontend)
should only ever see the normalized shape produced here.

Core fields are always present (or explicitly `None`) for every supported model.
Mapping-only fields (pose) are only populated when the payload actually contains
them — never assume they exist just because `model_class == "mapping"`, since a
mapping robot mid-charge may not report a pose.

See ../../shared/schema.md for the field-by-field reference.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class NormalizedState:
    # -- identity / bookkeeping --
    received_at: float
    model_class: str  # "non-mapping" | "mapping"

    # -- core fields, present on every supported model --
    battery_pct: int | None
    bin_present: bool | None
    bin_full: bool | None
    cycle: str | None  # e.g. "clean", "none"
    phase: str | None  # e.g. "run", "charge", "stop", "hmUsrDock"
    error_code: int | None  # 0 (or None) means no error
    not_ready_code: int | None
    mission_minutes: int | None
    mission_sqft: float | None
    mission_initiator: str | None

    # -- mapping-model-only fields, always optional --
    pose_x: float | None = None
    pose_y: float | None = None
    pose_theta: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get(d: dict | None, *path: str, default: Any = None) -> Any:
    """Walk a chain of dict keys, returning `default` the moment anything is missing."""
    cur: Any = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def normalize(raw: dict, model_class: str, received_at: float | None = None) -> NormalizedState:
    """Convert one raw `state.reported` payload into a `NormalizedState`.

    `raw` is expected to be the `reported` object itself (i.e. already unwrapped
    from the outer `{"state": {"reported": {...}}}` MQTT envelope).
    """
    if model_class not in ("mapping", "non-mapping"):
        raise ValueError(f"unknown model_class: {model_class!r}")

    mission = _get(raw, "cleanMissionStatus", default={})

    state = NormalizedState(
        received_at=received_at if received_at is not None else time.time(),
        model_class=model_class,
        battery_pct=_get(raw, "batPct"),
        bin_present=_get(raw, "bin", "present"),
        bin_full=_get(raw, "bin", "full"),
        cycle=_get(mission, "cycle"),
        phase=_get(mission, "phase"),
        error_code=_get(mission, "error"),
        not_ready_code=_get(mission, "notReady"),
        mission_minutes=_get(mission, "mssnM"),
        mission_sqft=_get(mission, "sqft"),
        mission_initiator=_get(mission, "initiator"),
    )

    # Pose is only ever emitted by mapping-capable (vSLAM) robots, and only while
    # actively running a mission — treat its presence in the payload as the source
    # of truth rather than trusting model_class alone.
    pose = _get(raw, "pose")
    if isinstance(pose, dict):
        point = _get(pose, "point", default={})
        state.pose_theta = _get(pose, "theta")
        state.pose_x = _get(point, "x")
        state.pose_y = _get(point, "y")

    return state
