# Roomba Telemetry Platform

A local-network dashboard and data platform for iRobot Roomba WiFi models, built on
the reverse-engineered local MQTT API. Supports both **non-mapping models (600/900-series
without vSLAM, e.g. Roomba 690/692)** and **mapping models (900-series with vSLAM, e.g.
960/980)**.

This document is the single source of truth for how the project is structured and how
it evolves. It's written so a stranger can clone the repo, read this file, and understand
both *what* to build next and *why* the repo is laid out the way it is.

---

## 1. Supported Models & Capability Matrix

The local API returns different fields depending on hardware generation. Design the
data layer to be additive — every model gets the "core" fields; mapping models get
extra fields layered on top.

| Feature | 600-series (e.g. 690/692) | 900-series w/ vSLAM (e.g. 960/980) |
|---|---|---|
| Mission phase / cycle | ✅ | ✅ |
| Battery %, charging state | ✅ | ✅ |
| Bin full sensor | ✅ | ✅ |
| Error codes | ✅ | ✅ |
| Run time / area estimate | ✅ (coarse) | ✅ (precise) |
| Map / room data | ❌ | ✅ |
| Room-by-room cleaning stats | ❌ | ✅ |
| Position/pose data | ❌ | ✅ |

Design principle: **never assume a field exists.** Every consumer of the state payload
should check for presence before rendering it, so the same frontend works unmodified
across both model classes.

---

## 2. Architecture Overview

```
┌─────────────┐      MQTT/TLS       ┌──────────────────┐
│   Roomba    │ ◄─────────────────► │  collector service │
│ (LAN, 8883) │                     │   (Python/asyncio)  │
└─────────────┘                     └─────────┬─────────┘
                                               │ writes
                                               ▼
                                        ┌─────────────┐
                                        │   SQLite    │
                                        └──────┬──────┘
                                               │ reads
                                               ▼
                                        ┌─────────────┐
                                        │  API layer  │  FastAPI (REST + WS)
                                        └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Web frontend │
                                        └─────────────┘
```

Everything runs locally — no cloud dependency, no iRobot account needed after the
initial BLID/password handshake. This is a deliberate choice: it keeps the whole stack
free, privacy-respecting, and resilient to iRobot server outages.

---

## 3. Repository Structure

```
roomba-telemetry/
├── README.md                     # quickstart, install, screenshots
├── PROJECT.md                    # this file
├── LICENSE
├── .env.example                  # ROOMBA_IP, ROOMBA_BLID, ROOMBA_PASSWORD, ROOMBA_MODEL_CLASS
├── docker-compose.yml            # optional one-command spin-up
│
├── collector/                    # talks to the Roomba, normalizes data
│   ├── pyproject.toml
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── connection.py         # MQTT client wrapper (dorita980/roomba980-python)
│   │   ├── pairing.py            # BLID/password handshake helper (CLI entry point)
│   │   ├── normalize.py          # maps raw payloads → common schema, per model class
│   │   ├── storage.py            # SQLite writer
│   │   └── main.py               # entry point: connect, stream, persist
│   └── tests/
│       ├── fixtures/             # sample raw payloads, 600-series and 900-series
│       └── test_normalize.py
│
├── api/                          # FastAPI service
│   ├── pyproject.toml
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # app factory, mounts routers
│   │   ├── routers/
│   │   │   ├── status.py         # GET /status
│   │   │   ├── missions.py       # GET /missions, /missions/{id}
│   │   │   ├── errors.py         # GET /errors
│   │   │   └── live.py           # WS /live
│   │   ├── db.py                 # SQLite session/connection
│   │   └── schemas.py            # Pydantic models (core + model-specific)
│   └── tests/
│
├── web/                          # frontend (React + Vite, or plain HTML/JS)
│   ├── package.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── LiveStatusCard.tsx
│   │   │   ├── MissionHistoryTable.tsx
│   │   │   ├── BatteryChart.tsx
│   │   │   ├── ErrorLog.tsx
│   │   │   └── MapView.tsx       # only rendered if model_class == "mapping"
│   │   └── lib/api.ts            # fetch + WS client
│   └── public/
│
├── shared/                       # cross-language schema/docs shared by collector+api
│   └── schema.md                 # documents every field, which models emit it
│
├── scripts/
│   ├── pair.sh                   # convenience wrapper for pairing.py
│   └── replay.py                 # replay recorded fixture data through the API for demos
│
├── docs/
│   ├── architecture.md
│   ├── model-differences.md      # deep dive on 600 vs 900-series payloads
│   ├── experiments/              # write-ups for each "fun project" below
│   └── images/
│
└── .github/
    └── workflows/
        ├── test.yml               # run collector + api test suites
        └── lint.yml
```

**Why this layout:** each top-level folder is independently runnable and testable
(`collector`, `api`, `web`), which is what makes it approachable for someone forking
the repo to experiment with just one piece — e.g., someone could ignore `web/` entirely
and just use `collector/` to log their own Roomba to CSV.

---

## 4. Development Phases

### Phase 0 — Pairing & raw capture
- Build `collector/pairing.py`: CLI tool to run the BLID/password handshake.
- Build a minimal raw logger that dumps every MQTT payload to a JSONL file.
- Capture and commit a handful of **anonymized sample payloads** from both model
  classes into `collector/tests/fixtures/` — this is what makes the repo usable by
  people who don't own a Roomba yet.

### Phase 1 — Normalization layer
- Write `normalize.py`: converts raw vendor payloads (which differ across firmware
  versions) into one stable internal schema, with optional fields for mapping models.
- Unit tests against the fixture payloads from Phase 0 — this is the core "learnable"
  part of the repo, since it's a clean example of defensive parsing against messy
  real-world device data.

### Phase 2 — Storage
- SQLite schema: `missions`, `state_snapshots`, `errors` tables.
- Migration approach: keep it simple, a single `schema.sql` applied on startup is
  fine for a project this size — don't over-engineer with a migration framework.

### Phase 3 — API
- FastAPI app exposing `/status`, `/missions`, `/errors`, and a `/live` WebSocket.
- `scripts/replay.py` lets contributors run the whole API/frontend stack against
  recorded fixture data with no physical Roomba required — important for making the
  project experiment-friendly.

### Phase 4 — Frontend
- Live status view, mission history, error log.
- Conditionally render map/room views only when connected to a mapping-model robot.

### Phase 5 — Packaging & docs
- `docker-compose.yml` for one-command local spin-up.
- `README.md` quickstart with screenshots/GIFs.
- `docs/model-differences.md` written up in detail — genuinely useful reference
  since this isn't well documented anywhere official.

### Phase 6 — Experiments (ongoing, see below)
- Each experiment lives in `docs/experiments/<name>.md` with its own optional code
  under `experiments/<name>/` so the core app stays uncluttered.

---

## 5. Fun Functionality & Experiment Ideas

Grouped by effort level, so contributors can pick something that fits their time budget.

**Small / weekend-scale**
- **Bin-full notifier** — webhook/email/push when bin-full is detected.
- **Error code decoder** — human-readable explanations + suggested fixes for each
  numeric error code, sourced from community wikis.
- **Cleaning streak tracker** — "days since last clean," longest streak, etc.
- **CSV/JSON export** of mission history for spreadsheet nerds.

**Medium**
- **Battery health tracker** — chart battery-at-start-of-mission over months to spot
  degrading battery health before the robot starts dying mid-clean.
- **"Roomba is stuck" detector** — flag missions that ended in error vs. completed,
  correlate with time of day / day of week to spot recurring problem spots.
- **Voice/chat integration** — expose `/status` via a simple webhook so you can ask
  a home assistant "is the Roomba done?"
- **Multi-robot support** — extend schema to track multiple robots on one dashboard.

**Larger / more experimental**
- **Cleaning heatmap (mapping models only)** — accumulate pose data across missions
  to build a "coverage heatmap" of your floor plan showing frequently-missed spots.
- **Predictive scheduling** — use historical mission duration/battery-use data to
  predict optimal run times or estimate remaining battery life before a mission.
- **Cross-device correlation** — combine with smart-home occupancy sensors to
  auto-schedule cleaning for empty-house windows.
- **"Digital twin" replay viewer** — for mapping models, animate a past mission's
  path on the floor plan using recorded pose data.
- **Anomaly detection** — simple statistical model flagging missions that deviate
  from the robot's normal duration/battery-use pattern (early warning for a
  clogged brush or failing sensor).

Each of these is a good candidate for a first-timer's contribution because it's
additive — it consumes the existing normalized schema without touching the core
collector/API.

---

## 6. Design Principles (for contributors)

1. **Model-agnostic core, model-aware extras.** Core schema fields must be present
   for every supported model; mapping-only fields are always optional and
   null-checked.
2. **No cloud dependency required.** Everything must work fully offline/local-only;
   cloud integrations (notifications, etc.) are opt-in extras, never required.
3. **Fixture-first development.** New features should be testable against recorded
   fixture payloads, not just a live robot — this is what lets people without a
   Roomba still contribute meaningfully.
4. **Small, readable modules.** This repo is meant to be read by people learning
   how to reverse-engineer and work with a local IoT device API — prefer clarity
   over cleverness.

---

## 7. Open Questions / To Decide Early

- SQLite vs. a lightweight time-series store (e.g. `duckdb`) for the snapshot table,
  if state-update volume gets high.
- Whether `web/` should be React or kept dependency-free as plain HTML/JS for
  maximum approachability.
- How to anonymize/share fixture payloads safely (strip BLID/serial/location data).
