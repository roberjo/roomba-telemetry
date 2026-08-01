def test_unknown_command_rejected(client, monkeypatch):
    monkeypatch.setenv("ROOMBA_IP", "192.168.1.99")
    monkeypatch.setenv("ROOMBA_BLID", "test-blid")
    monkeypatch.setenv("ROOMBA_PASSWORD", "test-password")

    resp = client.post("/commands/reboot-the-house")
    assert resp.status_code == 400
    assert "unsupported command" in resp.json()["detail"]


def test_command_without_credentials_rejected(client, monkeypatch):
    monkeypatch.delenv("ROOMBA_IP", raising=False)
    monkeypatch.delenv("ROOMBA_BLID", raising=False)
    monkeypatch.delenv("ROOMBA_PASSWORD", raising=False)

    resp = client.post("/commands/start")
    assert resp.status_code == 400
    assert "ROOMBA_IP" in resp.json()["detail"]


def test_find_and_spot_are_allowed_commands(monkeypatch):
    from api.mqtt_commands import ALLOWED_COMMANDS

    assert "find" in ALLOWED_COMMANDS
    assert "spot" in ALLOWED_COMMANDS


def test_stuck_mqtt_client_cannot_hang_the_request(monkeypatch):
    """Regression test for a real bug: a stuck paho-mqtt client (loop_stop()/
    disconnect() blocking forever) used to hang the whole request indefinitely,
    since it was joined synchronously inside a `finally` block. _publish() now
    runs that on a daemon thread with a hard wall-clock cap — verify it actually
    gives up and raises within that cap instead of hanging, using a fake worker
    that never returns to simulate the stuck case."""
    import time

    from api import mqtt_commands

    monkeypatch.setenv("ROOMBA_IP", "192.168.1.99")
    monkeypatch.setenv("ROOMBA_BLID", "test-blid")
    monkeypatch.setenv("ROOMBA_PASSWORD", "test-password")
    monkeypatch.setattr(mqtt_commands, "OVERALL_TIMEOUT_S", 0.3)

    def stuck_forever(ip, blid, password, payload, result):
        time.sleep(3600)

    monkeypatch.setattr(mqtt_commands, "_publish_blocking", stuck_forever)

    start = time.monotonic()
    try:
        mqtt_commands.send_command("start")
        raised = False
    except mqtt_commands.CommandError as exc:
        raised = True
        message = str(exc)
    elapsed = time.monotonic() - start

    assert raised
    assert "stuck" in message
    assert elapsed < 2, f"took {elapsed:.2f}s — should give up around OVERALL_TIMEOUT_S (0.3s)"


def test_clean_room_route_not_swallowed_by_command_catchall(client, monkeypatch):
    """Regression test: /commands/{command} is registered after /commands/clean-room
    specifically so this exact collision doesn't happen — verify it via a real
    request rather than just trusting route declaration order."""
    monkeypatch.delenv("ROOMBA_IP", raising=False)

    resp = client.post(
        "/commands/clean-room",
        json={
            "pmap_id": "map1",
            "user_pmapv_id": "v1",
            "regions": [{"region_id": "1", "region_name": "Kitchen", "region_type": "kitchen"}],
        },
    )
    # No credentials set, so this should fail on that specific check (400 with
    # ROOMBA_IP in the message) — NOT the generic "unsupported command:
    # 'clean-room'" error the {command} catch-all would produce if it had
    # matched instead.
    assert resp.status_code == 400
    assert "ROOMBA_IP" in resp.json()["detail"]
