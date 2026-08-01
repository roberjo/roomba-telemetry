"""GET /errors — recorded non-zero error codes, most recent first."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db import get_db
from ..schemas import ErrorEvent

router = APIRouter()


@router.get("/errors", response_model=list[ErrorEvent])
def list_errors(
    limit: int = 50,
    offset: int = 0,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[ErrorEvent]:
    rows = conn.execute(
        "SELECT * FROM errors ORDER BY occurred_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [ErrorEvent(**dict(row)) for row in rows]
