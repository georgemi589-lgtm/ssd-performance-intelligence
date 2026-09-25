"""Unit tests for :mod:`ssd_performance_intelligence.data.schema`.

All assertions use the small synthetic fixture from
``tests/fixtures/fio_fixtures.py``.  No real FIO is invoked and no files
are read from ``data/raw/``.
"""

from __future__ import annotations

import json

import pytest

from ssd_performance_intelligence.data.schema import (
    DirectionStats,
    FioJobRecord,
    FioSchemaError,
    IODepthDistribution,
    IOPSStats,
    JobMetadata,
    LatencyStats,
    ParsedFioOutput,
    ThroughputStats,
)

from tests.fixtures.fio_fixtures import FIXTURE_SEQ_READ


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raw() -> dict:
    # Deep copy via JSON round-trip so tests can mutate without side effects.
    return json.loads(json.dumps(FIXTURE_SEQ_READ))


def _job_dict() -> dict:
    return _raw()["jobs"][0]


def _read_block() -> dict:
    return _job_dict()["read"]


# ---------------------------------------------------------------------------
# LatencyStats
# ---------------------------------------------------------------------------

class TestLatencyStats:
    def test_from_none_gives_empty_stats(self) -> None:
        stats = LatencyStats.from_dict(None, field="test")
        assert stats.min_ns is None
        assert stats.mean_ns is None
        assert stats.percentiles_ns == {}

    def test_from_dict_fields(self) -> None:
        block = {"min": 1000, "max": 9000, "mean": 5000.0, "stddev": 100.0, "N": 50}
        stats = LatencyStats.from_dict(block, field="test")
        assert stats.min_ns == pytest.approx(1000.0)
        assert stats.max_ns == pytest.approx(9000.0)
        assert stats.mean_ns == pytest.approx(5000.0)
        assert stats.stddev_ns == pytest.approx(100.0)
        assert stats.samples == 50

    def test_us_properties(self) -> None:
        block = {"min": 1_000, "max": 2_000, "mean": 1_500.0, "stddev": 50.0, "N": 10}
        stats = LatencyStats.from_dict(block, field="test")
        assert stats.min_us == pytest.approx(1.0)
        assert stats.max_us == pytest.approx(2.0)
        assert stats.mean_us == pytest.approx(1.5)
        assert stats.stddev_us == pytest.approx(0.05)

    def test_percentile_lookup(self) -> None:
        block = {
            "min": 1000,
            "max": 2000,
            "mean": 1500.0,
            "stddev": 50.0,
            "N": 10,
            "percentile": {"50.000000": 1500, "99.000000": 1900},
        }
        stats = LatencyStats.from_dict(block, field="test")
        assert stats.p50_us == pytest.approx(1.5)
        assert stats.p99_us == pytest.approx(1.9)

    def test_missing_percentile_returns_none(self) -> None:
        block = {"min": 1000, "max": 2000, "mean": 1500.0, "stddev": 50.0, "N": 10}
        stats = LatencyStats.from_dict(block, field="test")
        assert stats.p50_us is None
        assert stats.p999_us is None

    def test_unit_is_always_ns(self) -> None:
        stats = LatencyStats.from_dict({}, field="test")
        assert stats.unit == "ns"

    def test_non_numeric_field_raises(self) -> None:
        block = {"min": "not_a_number", "max": 2000, "mean": 1500.0, "stddev": 50.0, "N": 10}
        with pytest.raises(FioSchemaError, match="not numeric"):
            LatencyStats.from_dict(block, field="test")

    def test_frozen(self) -> None:
        stats = LatencyStats.from_dict({}, field="test")
        with pytest.raises(Exception):
            stats.unit = "µs"  # type: ignore[misc]

    def test_none_us_when_ns_is_none(self) -> None:
        stats = LatencyStats.from_dict(None, field="test")
        assert stats.min_us is None
        assert stats.max_us is None
        assert stats.mean_us is None
        assert stats.stddev_us is None


# ---------------------------------------------------------------------------
# ThroughputStats
# ---------------------------------------------------------------------------

class TestThroughputStats:
    def test_from_read_block(self) -> None:
        block = _read_block()
        stats = ThroughputStats.from_dict(block, field="read")
        assert stats.bw_bytes_per_sec == pytest.approx(131_072_000.0)
        assert stats.bw_kib_s == pytest.approx(128_000.0)
        assert stats.bw_min_kib_s == pytest.approx(120_000.0)
        assert stats.bw_max_kib_s == pytest.approx(135_000.0)
        assert stats.bw_samples == 10

    def test_empty_block(self) -> None:
        stats = ThroughputStats.from_dict({}, field="read")
        assert stats.bw_bytes_per_sec is None

    def test_from_none(self) -> None:
        stats = ThroughputStats.from_dict(None, field="read")
        assert stats.bw_bytes_per_sec is None

    def test_frozen(self) -> None:
        stats = ThroughputStats.from_dict({}, field="read")
        with pytest.raises(Exception):
            stats.bw_kib_s = 9999  # type: ignore[misc]


# ---------------------------------------------------------------------------
# IOPSStats
# ---------------------------------------------------------------------------

class TestIOPSStats:
    def test_from_read_block(self) -> None:
        block = _read_block()
        stats = IOPSStats.from_dict(block, field="read")
        assert stats.iops == pytest.approx(1_000.0)
        assert stats.iops_min == pytest.approx(937.0)
        assert stats.iops_max == pytest.approx(1_054.0)
        assert stats.iops_mean == pytest.approx(992.0)
        assert stats.iops_samples == 10

    def test_empty_block(self) -> None:
        stats = IOPSStats.from_dict({}, field="read")
        assert stats.iops is None

    def test_frozen(self) -> None:
        stats = IOPSStats.from_dict({}, field="read")
        with pytest.raises(Exception):
            stats.iops = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DirectionStats
# ---------------------------------------------------------------------------

class TestDirectionStats:
    def test_read_direction(self) -> None:
        block = _read_block()
        stats = DirectionStats.from_dict(block, direction="read")
        assert stats.direction == "read"
        assert stats.total_ios == 10_000
        assert stats.io_bytes == 1_310_720_000
        assert stats.runtime_ms == pytest.approx(10_000.0)

    def test_write_zero(self) -> None:
        block = _job_dict()["write"]
        stats = DirectionStats.from_dict(block, direction="write")
        assert stats.total_ios == 0

    def test_none_block_gives_empty(self) -> None:
        stats = DirectionStats.from_dict(None, direction="trim")
        assert stats.direction == "trim"
        assert stats.total_ios is None

    def test_latency_sub_records(self) -> None:
        block = _read_block()
        stats = DirectionStats.from_dict(block, direction="read")
        assert isinstance(stats.submission_latency, LatencyStats)
        assert isinstance(stats.completion_latency, LatencyStats)
        assert isinstance(stats.total_latency, LatencyStats)

    def test_frozen(self) -> None:
        stats = DirectionStats.from_dict(None, direction="read")
        with pytest.raises(Exception):
            stats.direction = "write"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# JobMetadata
# ---------------------------------------------------------------------------

class TestJobMetadata:
    def test_basic_fields(self) -> None:
        job = _job_dict()
        meta = JobMetadata.from_dict(job)
        assert meta.jobname == "fixture-seq-read"
        assert meta.groupid == 0
        assert meta.error == 0
        assert meta.elapsed_s == pytest.approx(11.0)

    def test_job_options_copied(self) -> None:
        job = _job_dict()
        meta = JobMetadata.from_dict(job)
        assert meta.job_options["rw"] == "read"
        assert meta.job_options["bs"] == "128k"

    def test_missing_jobname_raises(self) -> None:
        job = _job_dict()
        del job["jobname"]
        with pytest.raises(FioSchemaError, match="jobname"):
            JobMetadata.from_dict(job)

    def test_empty_jobname_raises(self) -> None:
        job = _job_dict()
        job["jobname"] = ""
        with pytest.raises(FioSchemaError, match="jobname"):
            JobMetadata.from_dict(job)

    def test_frozen(self) -> None:
        meta = JobMetadata.from_dict(_job_dict())
        with pytest.raises(Exception):
            meta.jobname = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# IODepthDistribution
# ---------------------------------------------------------------------------

class TestIODepthDistribution:
    def test_from_job_dict(self) -> None:
        dist = IODepthDistribution.from_job_dict(_job_dict())
        assert dist.requested_iodepth == 1
        assert dist.latency_depth == 1

    def test_level_percent(self) -> None:
        dist = IODepthDistribution.from_job_dict(_job_dict())
        assert dist.level_percent["1"] == pytest.approx(100.0)
        assert dist.level_percent["2"] == pytest.approx(0.0)

    def test_submit_percent(self) -> None:
        dist = IODepthDistribution.from_job_dict(_job_dict())
        assert dist.submit_percent["4"] == pytest.approx(100.0)

    def test_complete_percent(self) -> None:
        dist = IODepthDistribution.from_job_dict(_job_dict())
        assert dist.complete_percent["4"] == pytest.approx(100.0)

    def test_frozen(self) -> None:
        dist = IODepthDistribution.from_job_dict(_job_dict())
        with pytest.raises(Exception):
            dist.requested_iodepth = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FioJobRecord
# ---------------------------------------------------------------------------

class TestFioJobRecord:
    def test_from_dict(self) -> None:
        record = FioJobRecord.from_dict(_job_dict())
        assert record.metadata.jobname == "fixture-seq-read"
        assert isinstance(record.read, DirectionStats)
        assert isinstance(record.write, DirectionStats)
        assert isinstance(record.iodepth, IODepthDistribution)

    def test_trim_none_when_absent(self) -> None:
        job = _job_dict()
        # fixture has trim=None
        record = FioJobRecord.from_dict(job)
        assert record.trim is None

    def test_non_dict_raises(self) -> None:
        with pytest.raises(FioSchemaError, match="mapping"):
            FioJobRecord.from_dict("not_a_dict")  # type: ignore[arg-type]

    def test_frozen(self) -> None:
        record = FioJobRecord.from_dict(_job_dict())
        with pytest.raises(Exception):
            record.metadata = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# ParsedFioOutput
# ---------------------------------------------------------------------------

class TestParsedFioOutput:
    def test_from_raw(self) -> None:
        raw = _raw()
        out = ParsedFioOutput.from_raw(raw)
        assert out.fio_version == "fio-3.42"
        assert len(out.jobs) == 1

    def test_raw_preserved_unmodified(self) -> None:
        raw = _raw()
        out = ParsedFioOutput.from_raw(raw)
        assert out.raw is raw  # same object — not a copy

    def test_leading_text_none_by_default(self) -> None:
        out = ParsedFioOutput.from_raw(_raw())
        assert out.leading_non_json_text is None

    def test_leading_text_passed_through(self) -> None:
        out = ParsedFioOutput.from_raw(_raw(), leading_non_json_text="warning line")
        assert out.leading_non_json_text == "warning line"

    def test_non_dict_raises(self) -> None:
        with pytest.raises(FioSchemaError, match="JSON object"):
            ParsedFioOutput.from_raw([1, 2, 3])  # type: ignore[arg-type]

    def test_missing_jobs_raises(self) -> None:
        raw = _raw()
        del raw["jobs"]
        with pytest.raises(FioSchemaError, match="jobs"):
            ParsedFioOutput.from_raw(raw)

    def test_empty_jobs_raises(self) -> None:
        raw = _raw()
        raw["jobs"] = []
        with pytest.raises(FioSchemaError, match="jobs"):
            ParsedFioOutput.from_raw(raw)

    def test_jobs_is_tuple(self) -> None:
        out = ParsedFioOutput.from_raw(_raw())
        assert isinstance(out.jobs, tuple)

    def test_global_options_empty_dict(self) -> None:
        out = ParsedFioOutput.from_raw(_raw())
        assert isinstance(out.global_options, dict)

    def test_frozen(self) -> None:
        out = ParsedFioOutput.from_raw(_raw())
        with pytest.raises(Exception):
            out.fio_version = "fio-99"  # type: ignore[misc]

    def test_timestamp_ms(self) -> None:
        out = ParsedFioOutput.from_raw(_raw())
        assert out.timestamp_ms == 1_000_000_000_000
