# Normalized state schema

This is the stable internal schema produced by `collector/collector/normalize.py`
from a raw `state.reported` MQTT payload, stored by `collector/collector/storage.py`,
and served by the API (`api/api/schemas.py`). Every consumer — API routes, the
frontend, future experiments — should read this document rather than the raw
vendor payload shape, which varies by firmware and hardware generation.

**Design principle:** core fields are present (or explicitly `null`) for every
supported model. Mapping-only fields are always optional, even on a mapping-capable
robot — a docked robot mid-charge may not report a pose. Always null-check before
rendering. See `docs/model-differences.md` for the underlying raw-payload rationale.

## Core fields (all models)

| Field | Type | Meaning |
|---|---|---|
| `received_at` | float (unix timestamp) | When the collector received this update |
| `model_class` | `"non-mapping"` \| `"mapping"` | From `ROOMBA_MODEL_CLASS` env var |
| `battery_pct` | int 0–100 or null | Battery charge percentage |
| `bin_present` | bool or null | Whether the bin is physically inserted |
| `bin_full` | bool or null | Bin-full sensor state |
| `cycle` | string or null | e.g. `"clean"`, `"none"` |
| `phase` | string or null | e.g. `"run"`, `"charge"`, `"stop"`, `"hmUsrDock"` |
| `error_code` | int or null | 0 (or null) means no error; see `docs/model-differences.md` for known codes |
| `not_ready_code` | int or null | Non-zero when the robot refuses to start a mission |
| `mission_minutes` | int or null | Elapsed minutes in the current/last mission |
| `mission_sqft` | float or null | Estimated area cleaned (coarse on 600-series, precise on mapping models) |
| `mission_initiator` | string or null | e.g. `"manual"`, `"schedule"`, `"localApp"` |

## Mapping-only fields (900-series w/ vSLAM)

| Field | Type | Meaning |
|---|---|---|
| `pose_x` | float or null | Position, mm, relative to the dock |
| `pose_y` | float or null | Position, mm, relative to the dock |
| `pose_theta` | float or null | Heading, degrees |

## Derived tables

`missions` and `errors` (see `collector/collector/storage.py`'s `SCHEMA`) are
derived from sequences of state snapshots — a mission is a contiguous run of
`phase == "run"` snapshots, bounded by dock/charge/stop transitions. That
derivation logic is still a TODO (Phase 2/3 boundary); today the collector writes
raw snapshots and error rows only.
