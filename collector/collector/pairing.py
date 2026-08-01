"""BLID/password handshake helper.

Implements the community-documented (unofficial) local pairing protocol used by
tools like dorita980's `getpassword.js`:

1. **Discovery** — broadcast a UDP packet containing `irobotmcs` to port 5678.
   The robot answers with a small JSON payload that includes its BLID (as
   `hostname`, formatted `Roomba-<BLID>` or `iRobot-<BLID>`) and IP.
2. **Password retrieval** — open a TLS connection to the robot on port 8883 and
   write a fixed 7-byte "magic packet" (`f0 05 ef cc 3b 29 00`). While the robot's
   Home button is held down (LED ring pulses white, ~2s), it responds over the
   same TLS socket with a payload containing the local MQTT password.

This protocol is not officially documented by iRobot and has drifted across
firmware versions before — if the handshake doesn't work out of the box, cross-check
against the current dorita980/roomba980-python implementations before assuming your
robot is unsupported.

Usage:
    python -m collector.pairing --ip 192.168.1.50
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time

DISCOVERY_PORT = 5678
DISCOVERY_MESSAGE = b"irobotmcs"
DISCOVERY_TIMEOUT_S = 5

MQTT_PORT = 8883
GET_PASSWORD_MAGIC = bytes([0xF0, 0x05, 0xEF, 0xCC, 0x3B, 0x29, 0x00])
GET_PASSWORD_TIMEOUT_S = 10
# Observed response framing: a short header (message type + length) followed by
# the BLID and then the password. Adjust HEADER_LEN if your firmware's response
# doesn't parse cleanly — print the raw bytes and compare against dorita980.
HEADER_LEN = 2


def discover(broadcast_ip: str = "255.255.255.255") -> dict | None:
    """Broadcast for a Roomba on the local network. Returns {"ip", "blid"} or None."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(DISCOVERY_TIMEOUT_S)
    try:
        sock.sendto(DISCOVERY_MESSAGE, (broadcast_ip, DISCOVERY_PORT))
        data, addr = sock.recvfrom(4096)
    except socket.timeout:
        return None
    finally:
        sock.close()

    try:
        payload = json.loads(data.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return None

    hostname = payload.get("hostname", "")
    blid = hostname.split("-")[-1] if "-" in hostname else None
    return {"ip": payload.get("ip", addr[0]), "blid": blid}


def get_password(ip: str) -> bytes:
    """Retrieve the local MQTT password. Caller must be holding the robot's Home
    button down (or have just released it) so the robot is in pairing mode."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    raw_sock = socket.create_connection((ip, MQTT_PORT), timeout=GET_PASSWORD_TIMEOUT_S)
    with ctx.wrap_socket(raw_sock) as tls_sock:
        tls_sock.send(GET_PASSWORD_MAGIC)
        time.sleep(1)
        data = tls_sock.recv(4096)

    if len(data) <= HEADER_LEN:
        raise RuntimeError(
            f"unexpected response from robot ({len(data)} bytes) — "
            "was the Home button held down during pairing mode?"
        )
    return data[HEADER_LEN:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", help="Roomba IP address (skips discovery if given)")
    args = parser.parse_args()

    ip = args.ip
    blid = None

    if ip is None:
        print("Discovering Roomba on the local network...", file=sys.stderr)
        found = discover()
        if not found or not found.get("ip"):
            print("No robot found. Pass --ip explicitly.", file=sys.stderr)
            return 1
        ip, blid = found["ip"], found.get("blid")
        print(f"Found robot at {ip} (BLID: {blid})", file=sys.stderr)

    print(
        "Hold the CLEAN button (or Home button, depending on model) for ~2 seconds "
        "until the light ring spins white, then press Enter.",
        file=sys.stderr,
    )
    input()

    try:
        password_bytes = get_password(ip)
    except (TimeoutError, OSError, RuntimeError) as exc:
        print(f"Failed to retrieve password: {exc}", file=sys.stderr)
        return 1

    password = password_bytes.decode("utf-8", errors="replace").strip("\x00")

    print("\nAdd these to your .env file:\n")
    print(f"ROOMBA_IP={ip}")
    if blid:
        print(f"ROOMBA_BLID={blid}")
    else:
        print("ROOMBA_BLID=  # discovery didn't return a BLID, find it in the iRobot app")
    print(f"ROOMBA_PASSWORD={password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
