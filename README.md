# Roomba Telemetry Platform

A local-network dashboard and data platform for iRobot Roomba WiFi models, built on
the reverse-engineered local MQTT API. No cloud dependency, no iRobot account needed
after the initial pairing handshake.

See [PROJECT.md](PROJECT.md) for the full architecture, repo layout, and roadmap.

## Status

Early scaffold — Phase 0 (pairing & raw capture). See PROJECT.md §4 for the phase plan.

## Quickstart

### 1. Pair with your Roomba

You'll need the robot's IP address and its BLID/password, obtained via the local
handshake (hold the robot's Home button for a few seconds to enter pairing mode, then):

```bash
cd collector
pip install -e .
python -m collector.pairing --ip <ROOMBA_IP>
```

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
python scripts/replay.py --fixture collector/tests/fixtures/900-series-mapping.json
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

New to the project? `docs/model-differences.md` and `shared/schema.md` are the best
starting points for understanding the data model. `docs/experiments/` has a list of
small, self-contained feature ideas (bin-full notifier, error code decoder, etc.) that
are good first contributions — see PROJECT.md §5.

## License

MIT — see [LICENSE](LICENSE).
