# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-08-01

Initial release. Local-network telemetry and control dashboard for WiFi-enabled
Roombas, built on the reverse-engineered local MQTT API.

### Added

- `collector`: local MQTT/TLS connection to the robot, normalization of raw
  state payloads into a stable schema, SQLite persistence, and a BLID/password
  pairing helper with both the local handshake and an iRobot-cloud-login
  fallback (the local handshake is known to be silently ignored on some
  firmware — see `docs/model-differences.md`)
- `api`: FastAPI service exposing `/status`, `/missions`, `/errors`, a `/live`
  WebSocket, and mission-control commands (`start`/`stop`/`pause`/`resume`/
  `dock`/`find`/`spot`) over local MQTT, plus a backend-only room-targeted
  clean endpoint for mapping-capable robots
- `web`: a live-updating dashboard — Command Center (status + controls),
  battery trend, mission history, weekly schedule, device info, cleaning
  preferences, and an error log. Mapping-only views (live position) render
  only when the connected robot reports mapping capability
- Roombie: an original mood-driven mascot reflecting real robot state and
  command outcomes throughout the dashboard
- Fixture-first development: sample payloads for both non-mapping and mapping
  models let the whole stack run via `scripts/replay.py` with no physical
  robot required
- CI: automated tests (collector, api, web) and linting on every push/PR

### Fixed

- A real bug where sending a mission command could hang the entire page
  indefinitely if the MQTT connection ended up in a bad state — command sends
  now run under a hard wall-clock timeout so a stuck connection can never again
  block the UI
- pytest imports for `collector`/`api` failing when run from the repo root, due
  to an editable-install ordering quirk — fixed via `pythonpath` pytest config
  rather than depending on a fragile install mechanism

[Unreleased]: https://github.com/roberjo/roomba-telemetry/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/roberjo/roomba-telemetry/releases/tag/v0.1.0
