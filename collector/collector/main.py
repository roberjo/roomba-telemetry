"""Entry point: connect to the Roomba, normalize each state update, persist it."""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

from .connection import RoombaConnection, RoombaCredentials
from .normalize import normalize
from .storage import Storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    load_dotenv()

    ip = os.environ.get("ROOMBA_IP")
    blid = os.environ.get("ROOMBA_BLID")
    password = os.environ.get("ROOMBA_PASSWORD")
    model_class = os.environ.get("ROOMBA_MODEL_CLASS", "non-mapping")
    db_path = os.environ.get("ROOMBA_DB_PATH", "./data/roomba.db")

    missing = [
        name
        for name, val in [("ROOMBA_IP", ip), ("ROOMBA_BLID", blid), ("ROOMBA_PASSWORD", password)]
        if not val
    ]
    if missing:
        logger.error(
            "missing required env vars: %s (see .env.example, run `python -m collector.pairing`)",
            ", ".join(missing),
        )
        return 1

    storage = Storage(db_path)

    def on_state(raw: dict) -> None:
        state = normalize(raw, model_class)
        storage.write_snapshot(state)
        logger.debug("snapshot: %s", state.to_dict())

    creds = RoombaCredentials(ip=ip, blid=blid, password=password)
    conn = RoombaConnection(creds, on_state=on_state)

    try:
        conn.connect()
        conn.loop_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        conn.disconnect()
        storage.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
