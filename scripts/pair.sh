#!/usr/bin/env bash
# Convenience wrapper for collector/collector/pairing.py.
# Usage: scripts/pair.sh [--ip <ip>]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/collector"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -e .
fi

exec .venv/bin/python -m collector.pairing "$@"
