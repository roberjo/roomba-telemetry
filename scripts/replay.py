#!/usr/bin/env python3
"""Replays recorded fixture payloads into the SQLite DB the API reads from.

Lets contributors run the whole API + frontend stack against sample data with no
physical Roomba required (PROJECT.md Phase 3). Cycles through the given fixtures
repeatedly, re-timestamping each one to "now" so the `/live` WebSocket and
dashboard have something moving to show.

Usage:
    python scripts/replay.py collector/tests/fixtures/900-series-mapping.json
    python scripts/replay.py --loop --interval 3 collector/tests/fixtures/*.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import cycle
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "collector"))

from collector.normalize import normalize
from collector.storage import Storage


def infer_model_class(fixture_path: Path) -> str:
    return "mapping" if "mapping" in fixture_path.stem and "non-" not in fixture_path.stem else "non-mapping"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fixtures", nargs="+", type=Path, help="fixture JSON file(s) to replay")
    parser.add_argument("--db", default="./data/roomba.db", help="SQLite path (default: ./data/roomba.db)")
    parser.add_argument("--model-class", choices=["mapping", "non-mapping"], help="override auto-detection")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between writes")
    parser.add_argument("--loop", action="store_true", help="replay fixtures forever instead of once")
    args = parser.parse_args()

    for f in args.fixtures:
        if not f.exists():
            print(f"fixture not found: {f}", file=sys.stderr)
            return 1

    storage = Storage(args.db)
    fixtures = args.fixtures if not args.loop else cycle(args.fixtures)

    try:
        for fixture_path in fixtures:
            reported = json.loads(fixture_path.read_text())["state"]["reported"]
            model_class = args.model_class or infer_model_class(fixture_path)

            state = normalize(reported, model_class, received_at=time.time())
            storage.write_snapshot(state)
            print(f"wrote snapshot from {fixture_path.name} ({model_class}, phase={state.phase})")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        storage.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
