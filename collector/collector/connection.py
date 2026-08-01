"""Thin wrapper around the Roomba local MQTT API.

Roomba WiFi models run a Mosquitto broker on-device (port 8883, TLS with a
self-signed cert, username = BLID, password = the local password obtained via
`pairing.py`). The robot publishes its full state on connect and on every change
under topic `#`. This wrapper hides that connection plumbing behind a small
callback-based interface; it intentionally does not know anything about the
state schema — that's `normalize.py`'s job.
"""

from __future__ import annotations

import json
import logging
import ssl
from collections.abc import Callable
from dataclasses import dataclass

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

MQTT_PORT = 8883
STATE_TOPIC = "#"


@dataclass
class RoombaCredentials:
    ip: str
    blid: str
    password: str


class RoombaConnection:
    """Maintains a persistent MQTT connection to one Roomba and dispatches state updates."""

    def __init__(self, creds: RoombaCredentials, on_state: Callable[[dict], None]):
        self._creds = creds
        self._on_state = on_state
        self._client = mqtt.Client(client_id=creds.blid, protocol=mqtt.MQTTv311)
        self._client.username_pw_set(creds.blid, creds.password)

        # The robot presents a self-signed cert with no shared CA, so we can only
        # verify transport encryption, not the cert chain itself.
        self._client.tls_set(cert_reqs=ssl.CERT_NONE)
        self._client.tls_insecure_set(True)

        self._client.on_connect = self._handle_connect
        self._client.on_message = self._handle_message
        self._client.on_disconnect = self._handle_disconnect

    def connect(self) -> None:
        logger.info("connecting to Roomba at %s", self._creds.ip)
        self._client.connect(self._creds.ip, MQTT_PORT, keepalive=30)

    def loop_forever(self) -> None:
        self._client.loop_forever()

    def disconnect(self) -> None:
        self._client.disconnect()

    def _handle_connect(self, client: mqtt.Client, userdata, flags, rc: int) -> None:
        if rc != 0:
            logger.error("MQTT connect failed with code %s", rc)
            return
        logger.info("connected, subscribing to %s", STATE_TOPIC)
        client.subscribe(STATE_TOPIC)

    def _handle_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("dropping non-JSON message on topic %s", msg.topic)
            return

        reported = payload.get("state", {}).get("reported")
        if reported is None:
            return
        self._on_state(reported)

    def _handle_disconnect(self, client: mqtt.Client, userdata, rc: int) -> None:
        if rc != 0:
            logger.warning("unexpected disconnect (code %s), paho will auto-reconnect", rc)
