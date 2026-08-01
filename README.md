# Roomba Telemetry Platform

[![test](https://github.com/roberjo/roomba-telemetry/actions/workflows/test.yml/badge.svg)](https://github.com/roberjo/roomba-telemetry/actions/workflows/test.yml)
[![lint](https://github.com/roberjo/roomba-telemetry/actions/workflows/lint.yml/badge.svg)](https://github.com/roberjo/roomba-telemetry/actions/workflows/lint.yml)
[![CodeQL](https://github.com/roberjo/roomba-telemetry/actions/workflows/codeql.yml/badge.svg)](https://github.com/roberjo/roomba-telemetry/actions/workflows/codeql.yml)
[![security](https://github.com/roberjo/roomba-telemetry/actions/workflows/security.yml/badge.svg)](https://github.com/roberjo/roomba-telemetry/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A local-network dashboard and control platform for iRobot Roomba WiFi models, built on
the reverse-engineered local MQTT API. No cloud dependency, no iRobot account needed
after the initial pairing handshake.

See [PROJECT.md](PROJECT.md) for the full architecture, repo layout, and roadmap.

## What's here

- **Live status + control** — battery, phase, errors, bin state, and mission commands
  (start/stop/pause/resume/dock/find/spot), all reflected in real time via WebSocket.
- **Device data** most people don't realize is already in the local API: onboard weekly
  schedule, cleaning preferences, last-command provenance.
- **Model-agnostic core** — the same dashboard works unmodified across non-mapping
  (600-series) and mapping (vSLAM) models; mapping-only views appear automatically when
  the connected robot supports them.
- **Fixture-first** — the whole stack runs against recorded sample payloads with zero
  physical hardware required (`scripts/replay.py`).

Verified end-to-end against a real Roomba 692. See [docs/model-differences.md](docs/model-differences.md)
for what's confirmed against real hardware vs. community reference docs.

## Quickstart

### 1. Pair with your Roomba

You'll need the robot's IP address and its BLID/password. Try the local handshake
first (hold the robot's Home button for a few seconds to enter pairing mode, then):

```bash
cd collector
pip install -e .
python -m collector.pairing --ip <ROOMBA_IP>
```

If that hangs or fails — this has been observed to be silently ignored on some
firmware — use `python -m collector.pairing --cloud` instead, which logs in through
iRobot's own cloud API using your iRobot app account.

Copy the output into a `.env` file at the repo root (see `.env.example`).

### 2. Run the collector

```bash
cd collector
python -m collector.main
```

This connects to the robot over local MQTT/TLS and writes normalized state snapshots
to SQLite.

### 3. Run the API

```bash
cd api
pip install -e .
uvicorn api.main:app --reload
```

### 4. Run the frontend

```bash
cd web
npm install
npm run dev
```

### No robot yet?

Use the bundled fixture payloads to try the whole stack without hardware:

```bash
python scripts/replay.py collector/tests/fixtures/900-series-mapping.json
```

## Docker

```bash
cp .env.example .env   # fill in your Roomba's credentials
docker compose up
```

## Repository layout

See [PROJECT.md §3](PROJECT.md#3-repository-structure) for the annotated tree and the
reasoning behind it — each of `collector/`, `api/`, and `web/` is independently
runnable, so you can, for example, ignore `web/` entirely and just use `collector/`
to log your own Roomba to CSV.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup and how to run the test suite
locally. `docs/model-differences.md` and `shared/schema.md` are the best starting
points for understanding the data model. `docs/experiments/` has a list of small,
self-contained feature ideas (bin-full notifier, error code decoder, etc.) that are
good first contributions — see [PROJECT.md §5](PROJECT.md#5-fun-functionality--experiment-ideas).

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). Found a security issue?
See [SECURITY.md](SECURITY.md) rather than opening a public issue.

## License

MIT — see [LICENSE](LICENSE).
