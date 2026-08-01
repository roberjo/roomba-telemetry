"""Normalizes raw Roomba MQTT state payloads into one stable internal schema.

The local API reports a `state.reported` JSON blob whose shape varies by firmware
and hardware generation. This module is the single place that knows how to read
that mess defensively — every other part of the system (storage, API, frontend)
should only ever see the normalized shape produced here.

Core fields are always present (or explicitly `None`) for every supported model.
Mapping-only fields (pose) are only populated when the payload actually contains
them — never assume they exist just because `model_class == "mapping"`, since a
mapping robot mid-charge may not report a pose.

Field selection here is grounded in a real captured payload from a Roomba 692
(firmware 3.5.17+we+21, SKU R692020), not just community docs — see
../../shared/schema.md for the field-by-field reference and provenance notes.
Notably, `signal.rssi`/`signal.snr` (sometimes mentioned in community docs) were
NOT present in that payload, so we don't extract them here rather than ship a
field that would just always read `None` on real hardware.

See ../../shared/schema.md for the field-by-field reference.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any

WEEKDAYS = ("sun", "mon", "tue", "wed", "thu", "fri", "sat")


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

    # -- device identity, static but re-sent with every state update --
    robot_name: str | None = None
    sku: str | None = None
    software_version: str | None = None

    # -- last command provenance (who/what triggered the most recent action) --
    last_command: str | None = None
    last_command_initiator: str | None = None
    last_command_time: int | None = None

    # -- cleaning preferences (read-only here; see shared/schema.md) --
    pref_carpet_boost: bool | None = None
    pref_vac_high: bool | None = None
    pref_two_pass: bool | None = None
    pref_eco_charge: bool | None = None
    pref_bin_pause: bool | None = None

    # -- weekly schedule, JSON-encoded {"cycle": [...7], "hour": [...7], "minute": [...7]}
    # index 0 = Sunday, matching the robot's own convention.
    schedule_json: str | None = None

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
    last_command = _get(raw, "lastCommand", default={})
    schedule = _get(raw, "cleanSchedule")

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
        robot_name=_get(raw, "name"),
        sku=_get(raw, "sku"),
        software_version=_get(raw, "softwareVer"),
        last_command=_get(last_command, "command"),
        last_command_initiator=_get(last_command, "initiator"),
        last_command_time=_get(last_command, "time"),
        pref_carpet_boost=_get(raw, "carpetBoost"),
        pref_vac_high=_get(raw, "vacHigh"),
        pref_two_pass=_get(raw, "twoPass"),
        pref_eco_charge=_get(raw, "ecoCharge"),
        pref_bin_pause=_get(raw, "binPause"),
    )

    if isinstance(schedule, dict) and "cycle" in schedule:
        state.schedule_json = json.dumps(
            {"cycle": schedule.get("cycle"), "hour": schedule.get("h"), "minute": schedule.get("m")}
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
