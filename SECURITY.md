# Security Policy

This project talks to a physical IoT device over your local network and stores
its local MQTT credentials in a `.env` file (never committed — see `.gitignore`).
Please report security issues responsibly rather than opening a public issue.

## Reporting a Vulnerability

**Preferred: GitHub Private Vulnerability Reporting.** Use the "Report a
vulnerability" button under this repo's **Security** tab. This keeps the report
private between you and the maintainers until a fix is available, and doesn't
require sharing an email address publicly.

If that's not available to you, open a regular issue with as few technical
details as possible and ask for a private channel to follow up.

Please include:

- A description of the issue and its potential impact
- Steps to reproduce (a fixture-based repro is ideal — see
  `collector/tests/fixtures/` — since not everyone reviewing has physical
  hardware)
- Affected version/commit

## Scope

In scope:
- The `collector`, `api`, and `web` packages in this repo
- Credential handling (`.env`, `pairing.py`'s cloud/local flows)
- The MQTT command surface (`api/api/mqtt_commands.py`) — anything that could
  let an unintended party issue commands to the robot

Out of scope:
- Vulnerabilities in the robot's own firmware or iRobot's cloud API — report
  those to iRobot directly
- The unofficial local/cloud protocol reverse-engineering itself being
  "insecure by design" (e.g., TLS certificate validation is intentionally
  disabled to talk to the robot's self-signed cert — this is inherent to how
  the local API works, not a bug in this project)

## Supported Versions

This project is pre-1.0 and doesn't yet maintain multiple release branches —
security fixes land on `main` and the latest tagged release. See
[CHANGELOG.md](CHANGELOG.md) for release history.
