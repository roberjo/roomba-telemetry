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
firmware versions before. As of firmware in the 3.x range (2023+), dorita980's own
docs report this local handshake no longer works at all on many robots — iRobot's
TLS service still completes the handshake and accepts the magic packet, but never
sends a password back. If that happens to you, use `--cloud` instead (see below),
which retrieves the same BLID/password pairs through iRobot's official cloud login
API using your iRobot app account.

Usage:
    python -m collector.pairing --ip 192.168.1.50
    python -m collector.pairing --cloud
"""

from __future__ import annotations

import argparse
import getpass
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

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

# Cloud fallback (see dorita980's bin/getPasswordCloud.js) — used when the local
# handshake above gets silently ignored by the robot's firmware. app_id is a fixed
# constant dorita980 uses to identify itself as the (unofficial) Android app.
DISCOVERY_ENDPOINTS_URL = "https://disc-prod.iot.irobotapi.com/v1/discover/endpoints?country_code=US"
IROBOT_APP_ID = "ANDROID-C7FB240E-DF34-42D7-AE4E-A8C17079A294"
HTTP_TIMEOUT_S = 15


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


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Connection": "close"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
        return json.loads(resp.read())


def _http_post_form(url: str, fields: dict) -> dict:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Connection": "close", "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
        return json.loads(resp.read())


def _http_post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Connection": "close", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"iRobot login request failed: HTTP {exc.code} {exc.reason}") from exc


def get_password_cloud(username: str, password: str) -> dict[str, str]:
    """Retrieve {blid: local_mqtt_password} for every robot on this iRobot account,
    via the same official cloud login flow the iRobot mobile app uses. Fallback for
    firmware where the local handshake in get_password() is silently ignored."""
    discovery = _http_get_json(DISCOVERY_ENDPOINTS_URL)
    api_key = discovery["gigya"]["api_key"]
    gigya_base = f"https://accounts.{discovery['gigya']['datacenter_domain']}"
    http_base = discovery["deployments"][discovery["current_deployment"]]["httpBase"]

    gigya_resp = _http_post_form(
        f"{gigya_base}/accounts.login",
        {
            "apiKey": api_key,
            "loginID": username,
            "password": password,
            "targetEnv": "mobile",
            "format": "json",
        },
    )
    if gigya_resp.get("errorCode"):
        raise RuntimeError(f"iRobot login failed: {gigya_resp.get('errorMessage', gigya_resp)}")

    login_resp = _http_post_json(
        f"{http_base}/v2/login",
        {
            "app_id": IROBOT_APP_ID,
            "assume_robot_ownership": 0,
            "gigya": {
                "signature": gigya_resp["UIDSignature"],
                "timestamp": gigya_resp["signatureTimestamp"],
                "uid": gigya_resp["UID"],
            },
        },
    )
    robots = login_resp.get("robots") or {}
    if not robots:
        raise RuntimeError(f"login succeeded but no robots were returned: {login_resp}")
    return {blid: info["password"] for blid, info in robots.items()}


def _main_local(args: argparse.Namespace) -> int:
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
        print("If this keeps happening, try `--cloud` instead.", file=sys.stderr)
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


def _main_cloud(args: argparse.Namespace) -> int:
    username = input("iRobot account email: ")
    password = getpass.getpass("iRobot account password (hidden, sent only to iRobot's servers): ")

    try:
        robots = get_password_cloud(username, password)
    except (TimeoutError, OSError, RuntimeError, KeyError) as exc:
        print(f"Failed to retrieve password via cloud: {exc}", file=sys.stderr)
        return 1

    print(f"\nFound {len(robots)} robot(s) on this account:\n")
    for blid, robot_password in robots.items():
        print(f"ROOMBA_BLID={blid}")
        print(f"ROOMBA_PASSWORD={robot_password}")
        if args.ip and len(robots) == 1:
            print(f"ROOMBA_IP={args.ip}")
        print()
    if not args.ip:
        print("Set ROOMBA_IP to this robot's LAN IP (see `python -m collector.pairing` "
              "discovery output, or your router's client list).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ip", help="Roomba IP address (skips discovery if given)")
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="use the iRobot cloud login instead of the local handshake (fallback for "
        "firmware where the local method is silently ignored)",
    )
    args = parser.parse_args()

    return _main_cloud(args) if args.cloud else _main_local(args)


if __name__ == "__main__":
    raise SystemExit(main())
