"""POST /commands/{command} — mission control (start/stop/pause/resume/dock/find/spot).

Unlike the rest of the API this has a real-world side effect: it makes the
physical robot move. See ../mqtt_commands.py for the allowlist and MQTT details.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..mqtt_commands import CommandError, send_command, send_room_clean

router = APIRouter()


class Region(BaseModel):
    region_id: str
    region_name: str
    region_type: str
    type: str = "rid"


class RoomCleanRequest(BaseModel):
    pmap_id: str
    user_pmapv_id: str
    regions: List[Region]
    ordered: bool = False


# NOTE: this must be declared before the /commands/{command} catch-all below —
# FastAPI matches path operations in registration order, and {command} would
# otherwise swallow "clean-room" as a literal (invalid) command name.
@router.post("/commands/clean-room")
def post_clean_room(body: RoomCleanRequest) -> dict:
    """Mapping-only. UNVERIFIED against real hardware — see mqtt_commands.py's
    send_room_clean docstring. No UI wires up to this endpoint yet since there's
    no real map/room data source to populate a room picker from."""
    try:
        send_room_clean(
            pmap_id=body.pmap_id,
            regions=[r.model_dump() for r in body.regions],
            user_pmapv_id=body.user_pmapv_id,
            ordered=body.ordered,
        )
    except CommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (TimeoutError, OSError) as exc:
        raise HTTPException(status_code=502, detail=f"failed to reach robot: {exc}") from exc
    return {"sent": True}


@router.post("/commands/{command}")
def post_command(command: str) -> dict:
    try:
        send_command(command)
    except CommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (TimeoutError, OSError) as exc:
        raise HTTPException(status_code=502, detail=f"failed to reach robot: {exc}") from exc
    return {"command": command, "sent": True}
