"""Tests for Protocol v2 and Protocol v3 runner validation."""
from __future__ import annotations

import pytest

from ssd_performance_intelligence.data.runner import RunnerError, _validate_protocol_v2, _validate_protocol_v3, _validate_protocol_v4


def _config() -> dict:
    return {
        "experiment_id": "EXP005",
        "protocol": {"version": "2", "replicate_index": 1, "run_order": 1},
        "fio": {
            "name": "exp005-seq-read-qd1",
            "thread": 1,
        },
        "notes": {"objective": "repeatability baseline"},
    }


def test_protocol_v2_accepts_valid_metadata() -> None:
    _validate_protocol_v2(_config())


@pytest.mark.parametrize(
    "change",
    [
        {"experiment_id": "EXP_TEMPLATE"},
        {"protocol": {"version": "1", "replicate_index": 1, "run_order": 1}},
        {"protocol": {"version": "2", "replicate_index": 0, "run_order": 1}},
        {"protocol": {"version": "2", "replicate_index": 1, "run_order": 0}},
        {"fio": {"name": "wrong-job", "thread": 1}},
        {"fio": {"name": "exp005-seq-read-qd1"}},
    ],
)
def test_protocol_v2_rejects_missing_or_mismatched_metadata(change: dict) -> None:
    config = _config()
    config.update(change)
    with pytest.raises(RunnerError):
        _validate_protocol_v2(config)


def _config_v3() -> dict:
    return {
        "experiment_id": "EXP015",
        "protocol": {
            "version": "3",
            "replicate_index": 1,
            "run_order": 1,
            "block_id": 1,
            "within_block_order": 1,
            "condition": "QD2",
            "schedule_seed": "2026-10-06-balanced-v1",
        },
        "host_state": {
            "power_state": "plugged_in",
            "background_activity": "idle",
            "system_update_state": "none_observed",
        },
        "fio": {
            "name": "exp015-seq-read-qd2",
            "thread": 1,
            "iodepth": 2,
        },
    }


def test_protocol_v3_accepts_valid_metadata() -> None:
    _validate_protocol_v3(_config_v3())


@pytest.mark.parametrize(
    "change",
    [
        {"protocol": {"version": "3", "replicate_index": 1, "run_order": 1, "block_id": 1, "within_block_order": 1, "condition": "QD1", "schedule_seed": "seed"}},
        {"protocol": {"version": "3", "replicate_index": 6, "run_order": 1, "block_id": 1, "within_block_order": 1, "condition": "QD2", "schedule_seed": "seed"}},
        {"protocol": {"version": "3", "replicate_index": 1, "run_order": 1, "block_id": 1, "within_block_order": 3, "condition": "QD2", "schedule_seed": "seed"}},
        {"protocol": {"version": "3", "replicate_index": 1, "run_order": 1, "block_id": 1, "within_block_order": 1, "condition": "QD1", "schedule_seed": "seed"}},
        {"host_state": {"power_state": "", "background_activity": "idle", "system_update_state": "none_observed"}},
        {"host_state": {"power_state": "REPLACE_WITH_ACTUAL_STATE", "background_activity": "idle", "system_update_state": "none_observed"}},
        {"fio": {"name": "exp015-seq-read-qd1", "thread": 1, "iodepth": 1}},
    ],
)
def test_protocol_v3_rejects_mismatched_metadata(change: dict) -> None:
    config = _config_v3()
    config.update(change)
    with pytest.raises(RunnerError):
        _validate_protocol_v3(config)


def _config_v4() -> dict:
    return {
        "experiment_id": "EXP025",
        "protocol": {
            "version": "4",
            "replicate_index": 1,
            "run_order": 1,
            "block_id": 1,
            "within_block_order": 1,
            "condition": "QD2",
            "schedule_id": "v4-balanced-3rep-v1",
        },
        "host_state": {
            "power_state": "plugged_in",
            "background_activity": "idle",
            "system_update_state": "none_observed",
        },
        "fio": {
            "name": "exp025-seq-read-qd2",
            "thread": 1,
            "iodepth": 2,
        },
    }


def test_protocol_v4_accepts_valid_metadata() -> None:
    _validate_protocol_v4(_config_v4())


@pytest.mark.parametrize(
    "change",
    [
        {"protocol": {"version": "4", "replicate_index": 4, "run_order": 1, "block_id": 1, "within_block_order": 1, "condition": "QD2", "schedule_id": "seed"}},
        {"protocol": {"version": "4", "replicate_index": 1, "run_order": 13, "block_id": 1, "within_block_order": 1, "condition": "QD2", "schedule_id": "seed"}},
        {"protocol": {"version": "4", "replicate_index": 1, "run_order": 1, "block_id": 4, "within_block_order": 1, "condition": "QD2", "schedule_id": "seed"}},
        {"protocol": {"version": "4", "replicate_index": 1, "run_order": 1, "block_id": 1, "within_block_order": 5, "condition": "QD2", "schedule_id": "seed"}},
        {"protocol": {"version": "4", "replicate_index": 1, "run_order": 1, "block_id": 1, "within_block_order": 1, "condition": "QD3", "schedule_id": "seed"}},
        {"fio": {"name": "exp025-seq-read-qd8", "thread": 1, "iodepth": 8}},
        {"host_state": {"power_state": "REPLACE_WITH_ACTUAL_STATE", "background_activity": "idle", "system_update_state": "none_observed"}},
    ],
)
def test_protocol_v4_rejects_invalid_metadata(change: dict) -> None:
    config = _config_v4()
    config.update(change)
    with pytest.raises(RunnerError):
        _validate_protocol_v4(config)
