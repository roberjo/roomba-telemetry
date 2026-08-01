# Architecture

See [PROJECT.md §2](../PROJECT.md#2-architecture-overview) for the high-level diagram.
This doc goes one level deeper on how the three services fit together.

## Data flow

1. **collector** (`collector/`) opens a persistent MQTT/TLS connection directly to
   the Roomba on the local network (port 8883). The robot pushes its full state on
   connect and incremental updates on every change.
2. Each raw `state.reported` payload is passed through `collector/collector/normalize.py`,
   which converts vendor-specific, firmware-dependent field names into the stable
   schema documented in `shared/schema.md`.
3. Normalized snapshots are appended to SQLite (`collector/collector/storage.py`).
   The collector is the *only* writer to this database.
4. **api** (`api/`) is a read-only FastAPI service over the same SQLite file. It
   exposes `/status` (latest snapshot), `/missions`, `/errors`, and a `/live`
   WebSocket that polls for new snapshots and pushes them to connected clients.
5. **web** (`web/`) is a Vite + React dashboard that consumes the API — see
   `web/src/lib/api.ts` for the client, `web/src/components/` for the views.

## Why no message queue between collector and api?

At the scale of "one robot on one home network," a shared SQLite file plus a
short-poll WebSocket is simpler to run and debug than adding Redis/Kafka/etc.
Revisit only if the project grows to genuinely high-frequency multi-robot
telemetry (see PROJECT.md §7's open question on SQLite vs. a time-series store).

## Why is `collector` a separate connection from `api`?

So each piece is independently runnable and testable (PROJECT.md §3) — you can
run just the collector to log a robot to SQLite/CSV without ever touching the API
or frontend, which matters for a project that's explicitly meant to be forked and
experimented with piecemeal.
