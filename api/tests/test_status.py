import sqlite3
from pathlib import Path


def test_status_404_when_no_snapshots(client):
    resp = client.get("/status")
    assert resp.status_code == 404


def test_status_returns_latest_snapshot(client, db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO state_snapshots (received_at, model_class, battery_pct, phase)
        VALUES (100.0, 'non-mapping', 55, 'run'),
               (200.0, 'non-mapping', 60, 'charge')
        """
    )
    conn.commit()
    conn.close()

    resp = client.get("/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["battery_pct"] == 60
    assert body["phase"] == "charge"
    assert body["pose_x"] is None


def test_missions_and_errors_empty_by_default(client):
    assert client.get("/missions").json() == []
    assert client.get("/errors").json() == []


def test_status_decodes_device_info_and_schedule(client, db_path: Path):
    import json

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO state_snapshots (
            received_at, model_class, robot_name, sku, software_version,
            last_command, last_command_initiator, last_command_time,
            pref_carpet_boost, schedule_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            100.0,
            "non-mapping",
            "Roomba",
            "R692020",
            "3.5.17+we+21",
            "spot",
            "manual",
            1785615551,
            0,
            json.dumps({"cycle": ["none"] * 7, "hour": [9] * 7, "minute": [0] * 7}),
        ),
    )
    conn.commit()
    conn.close()

    body = client.get("/status").json()
    assert body["robot_name"] == "Roomba"
    assert body["sku"] == "R692020"
    assert body["last_command"] == "spot"
    assert body["pref_carpet_boost"] is False
    assert body["schedule"]["hour"][0] == 9
