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
