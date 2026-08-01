"""Read-only SQLite access for the API layer.

The collector owns writes (see ../../collector/collector/storage.py, which defines
the schema). The API only ever reads from the same database file.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path


def db_path() -> Path:
    return Path(os.environ.get("ROOMBA_DB_PATH", "./data/roomba.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: yields a connection, closes it after the request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
