"""Tests for Protocol v2 runner validation."""
from __future__ import annotations

import pytest

from ssd_performance_intelligence.data.runner import RunnerError, _validate_protocol_v2


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
