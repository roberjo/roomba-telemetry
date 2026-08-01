import json
from pathlib import Path

import pytest
from collector.normalize import WEEKDAYS, normalize

FIXTURES = Path(__file__).parent / "fixtures"


def _load_reported(fixture_name: str) -> dict:
    payload = json.loads((FIXTURES / fixture_name).read_text())
    return payload["state"]["reported"]


def test_normalize_non_mapping_has_no_pose():
    reported = _load_reported("600-series-non-mapping.json")
    state = normalize(reported, "non-mapping")

    assert state.battery_pct == 78
    assert state.bin_full is False
    assert state.phase == "run"
    assert state.error_code == 0
    assert state.pose_x is None
    assert state.pose_y is None
    assert state.pose_theta is None


def test_normalize_mapping_has_pose():
    reported = _load_reported("900-series-mapping.json")
    state = normalize(reported, "mapping")

    assert state.battery_pct == 91
    assert state.mission_sqft == 540
    assert state.pose_x == 1250
    assert state.pose_y == -430
    assert state.pose_theta == 42


def test_normalize_surfaces_error_code():
    reported = _load_reported("600-series-error.json")
    state = normalize(reported, "non-mapping")

    assert state.error_code == 16
    assert state.phase == "stop"


def test_normalize_missing_fields_default_to_none():
    state = normalize({}, "non-mapping")

    assert state.battery_pct is None
    assert state.bin_present is None
    assert state.cycle is None


def test_normalize_rejects_unknown_model_class():
    with pytest.raises(ValueError):
        normalize({}, "definitely-not-a-real-model-class")


def test_normalize_extracts_device_info_and_last_command():
    reported = _load_reported("600-series-full-state.json")
    state = normalize(reported, "non-mapping")

    assert state.robot_name == "Roomba"
    assert state.sku == "R692020"
    assert state.software_version == "3.5.17+we+21"
    assert state.last_command == "spot"
    assert state.last_command_initiator == "manual"
    assert state.last_command_time == 1785615551


def test_normalize_extracts_preferences():
    reported = _load_reported("600-series-full-state.json")
    state = normalize(reported, "non-mapping")

    assert state.pref_carpet_boost is False
    assert state.pref_vac_high is False
    assert state.pref_two_pass is False
    assert state.pref_eco_charge is False
    assert state.pref_bin_pause is False


def test_normalize_extracts_schedule():
    reported = _load_reported("600-series-full-state.json")
    state = normalize(reported, "non-mapping")

    assert state.schedule_json is not None
    schedule = json.loads(state.schedule_json)
    assert schedule["cycle"] == ["none"] * 7
    assert schedule["hour"][1] == 9
    assert len(WEEKDAYS) == 7


def test_normalize_without_device_info_defaults_to_none():
    state = normalize({}, "non-mapping")

    assert state.robot_name is None
    assert state.last_command is None
    assert state.schedule_json is None
    assert state.pref_carpet_boost is None
