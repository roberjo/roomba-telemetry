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

Two hard-won lessons baked in here (found by watching a real request hang the
frontend indefinitely on this exact robot's flaky WiFi):

1. Each call uses its own randomized MQTT client ID rather than reusing the
   robot's BLID as the client ID. The collector holds a long-lived connection
   using the BLID as its client ID; a second simultaneous connection with the
   *same* client ID can make the robot's broker misbehave (the two sessions
   collide). Username/password (the actual auth) still has to be the BLID/local
   password — only the client ID is randomized.
2. The whole connect/publish/cleanup sequence runs in a background thread with
   a hard wall-clock timeout. paho-mqtt's `loop_stop()`/`disconnect()` can block
   indefinitely if the connection is in a bad state (observed directly: a failed
   publish followed by a `loop_stop()` that never returned) — since that was
   called from a `finally` block, it silently ate the request forever with no
   way for the caller to time out. Running it on a daemon thread means a stuck
   MQTT client can never again block the HTTP response.
"""

from __future__ import annotations

import json
import os
import ssl
import threading
import time
import uuid
from typing import Any

import paho.mqtt.client as mqtt

MQTT_PORT = 8883
PUBLISH_TIMEOUT_S = 5
# Must exceed PUBLISH_TIMEOUT_S plus room for connect() and cleanup — this is
# the hard cap on how long an API request will ever wait, regardless of what
# the underlying MQTT client does.
OVERALL_TIMEOUT_S = 9

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


def _publish_blocking(ip: str, blid: str, password: str, payload: dict[str, Any], result: dict[str, Any]) -> None:
    """Runs on a background (daemon) thread — see module docstring for why."""
    client_id = f"{blid}-cmd-{uuid.uuid4().hex[:8]}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    client.username_pw_set(blid, password)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    try:
        client.connect(ip, MQTT_PORT, keepalive=10)
        client.loop_start()
        try:
            info = client.publish("cmd", json.dumps(payload), qos=1)
            info.wait_for_publish(timeout=PUBLISH_TIMEOUT_S)
            result["published"] = info.is_published()
        finally:
            client.loop_stop()
            client.disconnect()
    except Exception as exc:  # noqa: BLE001 — surfaced to the caller via `result`
        result["error"] = exc


def _publish(payload: dict[str, Any]) -> None:
    ip, blid, password = _get_credentials()

    result: dict[str, Any] = {}
    thread = threading.Thread(
        target=_publish_blocking, args=(ip, blid, password, payload, result), daemon=True
    )
    thread.start()
    thread.join(timeout=OVERALL_TIMEOUT_S)

    if thread.is_alive():
        raise CommandError(
            "the connection to the robot got stuck and did not respond in time — "
            "the command may or may not have gone through"
        )
    if "error" in result:
        raise CommandError(f"failed to send command: {result['error']}")
    if not result.get("published"):
        raise CommandError("timed out waiting for the robot to acknowledge the command")


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
