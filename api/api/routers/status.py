"""GET /status — most recent normalized state snapshot."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..schemas import StatusResponse, status_response_from_row

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
def get_status(conn: sqlite3.Connection = Depends(get_db)) -> StatusResponse:
    row = conn.execute(
        "SELECT * FROM state_snapshots ORDER BY received_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="no state snapshots recorded yet")
    return status_response_from_row(row)
