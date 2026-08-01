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
