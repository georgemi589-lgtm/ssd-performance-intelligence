"""Regression tests for guarding existing experiment artifacts before FIO runs."""
from __future__ import annotations

import yaml
import pytest

from ssd_performance_intelligence.data import runner
from ssd_performance_intelligence.data.runner import RunnerError


def _write_valid_config(tmp_path):
    config_path = tmp_path / "exp901.yaml"
    config = {
        "experiment_id": "EXP901",
        "protocol": {
            "version": "2",
            "replicate_index": 1,
            "run_order": 1,
        },
        "fio": {
            "name": "exp901-seq-read",
            "filename": str(tmp_path / "target.bin"),
            "rw": "read",
            "bs": "128k",
            "iodepth": 1,
            "ioengine": "windowsaio",
            "direct": 1,
            "runtime": 1,
            "size": "1M",
            "thread": 1,
        },
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_existing_raw_artifact_blocks_fio_before_execution(tmp_path, monkeypatch):
    config_path = _write_valid_config(tmp_path)
    output_dir = tmp_path / "raw"
    output_dir.mkdir()
    raw_path = output_dir / "exp901.json"
    raw_path.write_text('{"existing": true}', encoding="utf-8")
    invoked = []

    def fake_invoke(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("FIO must not run when a raw artifact already exists")

    monkeypatch.setattr(runner, "_invoke_fio", fake_invoke)

    with pytest.raises(RunnerError, match="Raw output already exists"):
        runner.run_experiment(
            str(config_path), execute=True, output_dir=output_dir
        )

    assert invoked == []
    assert raw_path.read_text(encoding="utf-8") == '{"existing": true}'


def test_existing_metadata_sidecar_blocks_fio_before_execution(tmp_path, monkeypatch):
    config_path = _write_valid_config(tmp_path)
    output_dir = tmp_path / "raw"
    output_dir.mkdir()
    metadata_path = output_dir / "exp901.metadata.json"
    metadata_path.write_text('{"existing": true}', encoding="utf-8")
    invoked = []

    def fake_invoke(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("FIO must not run when a metadata sidecar already exists")

    monkeypatch.setattr(runner, "_invoke_fio", fake_invoke)

    with pytest.raises(RunnerError, match="Protocol metadata already exists"):
        runner.run_experiment(
            str(config_path), execute=True, output_dir=output_dir
        )

    assert invoked == []
    assert metadata_path.read_text(encoding="utf-8") == '{"existing": true}'
