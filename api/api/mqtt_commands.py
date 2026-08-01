"""Publishes mission-control commands to the robot over local MQTT.

Same reverse-engineered local API used for reading state (see
collector/collector/connection.py for the read-side counterpart) — topic "cmd",
JSON payload — verified against the current dorita980 reference implementation.
Unlike the rest of the API, this has a real-world side effect: it makes the
physical robot move. Restricted to a small allowlist of standard commands.

`start`/`stop`/`pause`/`resume`/`dock` are verified against a real robot (see
docs/model-differences.md and the pairing.py handshake work). `find` and `spot`
use the same "cmd" topic/shape — `spot` is additionally confirmed by having
observed `lastCommand: {"command": "spot", ...}` in a real captured payload after
triggering a spot-clean from the iRobot app.
"""

from __future__ import annotations

import json
import os
import ssl
import time
from typing import Any

import paho.mqtt.client as mqtt

MQTT_PORT = 8883
PUBLISH_TIMEOUT_S = 5

ALLOWED_COMMANDS = {"start", "stop", "pause", "resume", "dock", "find", "spot"}


class CommandError(Exception):
    pass


def _get_credentials() -> tuple[str, str, str]:
    ip = os.environ.get("ROOMBA_IP")
    blid = os.environ.get("ROOMBA_BLID")
    password = os.environ.get("ROOMBA_PASSWORD")
    if not (ip and blid and password):
        raise CommandError("ROOMBA_IP/ROOMBA_BLID/ROOMBA_PASSWORD must be set to send commands")
    return ip, blid, password


def _publish(payload: dict[str, Any]) -> None:
    ip, blid, password = _get_credentials()

    client = mqtt.Client(client_id=blid, protocol=mqtt.MQTTv311)
    client.username_pw_set(blid, password)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    client.connect(ip, MQTT_PORT, keepalive=10)
    client.loop_start()
    try:
        info = client.publish("cmd", json.dumps(payload), qos=1)
        info.wait_for_publish(timeout=PUBLISH_TIMEOUT_S)
        if not info.is_published():
            raise CommandError("timed out waiting for the robot to acknowledge the command")
    finally:
        client.loop_stop()
        client.disconnect()


def send_command(command: str) -> None:
    if command not in ALLOWED_COMMANDS:
        raise CommandError(f"unsupported command: {command!r} (allowed: {sorted(ALLOWED_COMMANDS)})")
    _publish({"command": command, "time": int(time.time()), "initiator": "localApp"})


def send_room_clean(pmap_id: str, regions: list[dict], user_pmapv_id: str, ordered: bool = False) -> None:
    """Mapping-only, room-targeted clean. UNVERIFIED against real hardware — this
    project's only real test robot (a 692) has no vSLAM/room data to test with.

    Shape is taken from dorita980's documented cleanRoom(args): the command is
    "start" with pmap_id/regions/user_pmapv_id merged in — iRobot's app is the
    documented source for what pmap_id/region_id values are valid for a given
    robot; there's no way to discover them from this API alone. See
    docs/experiments/ for how to wire a room picker once real map data exists.
    """
    payload: dict[str, Any] = {
        "command": "start",
        "time": int(time.time()),
        "initiator": "localApp",
        "pmap_id": pmap_id,
        "regions": regions,
        "user_pmapv_id": user_pmapv_id,
    }
    if ordered:
        payload["ordered"] = 1
    _publish(payload)
