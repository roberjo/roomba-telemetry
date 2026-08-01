"""WS /live — pushes each new state snapshot to connected clients as it's written.

Implemented as a short poll against SQLite rather than a pubsub layer — simple,
and plenty fast enough for a single local robot's update cadence (PROJECT.md
deliberately avoids over-engineering the storage layer for this project's scale).
"""

from __future__ import annotations

import asyncio
import sqlite3

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..db import get_connection
from ..schemas import status_response_from_row

router = APIRouter()

POLL_INTERVAL_S = 1.0


@router.websocket("/live")
async def live(websocket: WebSocket) -> None:
    await websocket.accept()
    conn: sqlite3.Connection = get_connection()
    last_received_at = 0.0

    try:
        while True:
            row = conn.execute(
                "SELECT * FROM state_snapshots WHERE received_at > ? "
                "ORDER BY received_at DESC LIMIT 1",
                (last_received_at,),
            ).fetchone()
            if row is not None:
                last_received_at = row["received_at"]
                status = status_response_from_row(row)
                await websocket.send_json(status.model_dump())
            await asyncio.sleep(POLL_INTERVAL_S)
    except WebSocketDisconnect:
        pass
    finally:
        conn.close()
