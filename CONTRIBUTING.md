# Contributing

Thanks for considering a contribution — this project is explicitly designed to be
approachable, including for people who don't own a Roomba. See [PROJECT.md](PROJECT.md)
for the full architecture and roadmap; this file covers the mechanics of contributing.

## Getting set up

Each of `collector/`, `api/`, and `web/` is independently runnable — you don't need a
physical robot, and you don't need all three pieces to work on one of them.

```bash
# Python packages (collector, api) — Python 3.11+
cd collector && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cd ../api && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Frontend — Node 20+
cd ../web && npm install
```

No robot? Use the bundled fixtures with `scripts/replay.py` to exercise the full
stack — see the [README](README.md#no-robot-yet).

## Running the checks locally

```bash
collector/.venv/bin/pytest collector/tests
api/.venv/bin/pytest api/tests
ruff check collector api scripts
cd web && npm run build && npm run lint
```

These are exactly what CI runs (`.github/workflows/test.yml`, `lint.yml`) — if they
pass locally, your PR's checks should too.

## Design principles (please read before large changes)

See [PROJECT.md §6](PROJECT.md#6-design-principles-for-contributors):

1. **Model-agnostic core, model-aware extras.** Core schema fields must exist for
   every supported model; mapping-only fields (pose, etc.) are always optional and
   null-checked — never assume they exist just because a robot is mapping-capable.
2. **No cloud dependency required.** Cloud integrations are opt-in extras, never
   required for core functionality.
3. **Fixture-first development.** New features should be testable against the
   fixtures in `collector/tests/fixtures/`, not just a live robot.
4. **Small, readable modules.** This repo is meant to be read by people learning
   to reverse-engineer and work with a local IoT device API — prefer clarity over
   cleverness.
5. **Verify claims about the local API against a real payload or the current
   upstream reference** (dorita980/roomba980-python), not memory or old docs —
   the protocol has drifted across firmware versions before, and guessing wrong
   costs real debugging time. See `docs/model-differences.md`.

## Making a change

1. Fork and branch off `main`.
2. Keep PRs focused — one logical change per PR is easier to review than a
   grab-bag.
3. Add or update tests for anything you touch. Fixture-based tests (no hardware
   needed) are strongly preferred over anything requiring a live robot.
4. Update `shared/schema.md` if you add/change a normalized field.
5. Open the PR against `main`. CI (tests, lint, CodeQL, dependency review) runs
   automatically — please get it green before requesting review.

## Good first contributions

`docs/experiments/` lists small, self-contained feature ideas (bin-full notifier,
error code decoder, etc.) — see [PROJECT.md §5](PROJECT.md#5-fun-functionality--experiment-ideas)
for the full list, grouped by effort. These are additive: they consume the
existing normalized schema without touching the core collector/API, which makes
them a good first PR.

## Reporting bugs / requesting features

Use the issue templates — they'll prompt for what's actually needed to act on a
report (firmware version, model, whether it's reproducible against a fixture, etc).

## Security issues

Please don't open a public issue for a security vulnerability — see
[SECURITY.md](SECURITY.md) instead.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating,
you're expected to uphold it.
