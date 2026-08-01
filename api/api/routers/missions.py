"""GET /missions, GET /missions/{id} — mission history."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..schemas import Mission

router = APIRouter()


@router.get("/missions", response_model=list[Mission])
def list_missions(
    limit: int = 50,
    offset: int = 0,
    conn: sqlite3.Connection = Depends(get_db),
) -> list[Mission]:
    rows = conn.execute(
        "SELECT * FROM missions ORDER BY started_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [Mission(**dict(row)) for row in rows]


@router.get("/missions/{mission_id}", response_model=Mission)
def get_mission(mission_id: int, conn: sqlite3.Connection = Depends(get_db)) -> Mission:
    row = conn.execute("SELECT * FROM missions WHERE id = ?", (mission_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"mission {mission_id} not found")
    return Mission(**dict(row))
