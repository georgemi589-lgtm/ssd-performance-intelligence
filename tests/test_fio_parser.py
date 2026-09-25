"""Unit tests for :mod:`ssd_performance_intelligence.data.fio_parser`.

These tests use only the small synthetic fixture defined in
``tests/fixtures/fio_fixtures.py``.  They never invoke fio, never read from
``data/raw/``, and never write any files to disk.
"""

from __future__ import annotations

import json

import pytest

from ssd_performance_intelligence.data.fio_parser import (
    FioParseError,
    _split_leading_non_json,
    parse_fio_file,
    parse_fio_json_text,
    parse_fio_output,
)
from ssd_performance_intelligence.data.schema import ParsedFioOutput

from tests.fixtures.fio_fixtures import (
    FIXTURE_P50_NS,
    FIXTURE_P50_US,
    FIXTURE_P95_NS,
    FIXTURE_P95_US,
    FIXTURE_P99_NS,
    FIXTURE_P99_US,
    FIXTURE_P999_NS,
    FIXTURE_P999_US,
    FIXTURE_SEQ_READ,
    FIXTURE_SEQ_READ_WITH_PREAMBLE_TEXT,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixture_json_text() -> str:
    """Return the fixture dict serialised as a JSON string."""
    return json.dumps(FIXTURE_SEQ_READ)


def _fixture_json_with_preamble() -> str:
    """Return the fixture with a leading non-JSON warning line, as exp001.json has."""
    return FIXTURE_SEQ_READ_WITH_PREAMBLE_TEXT + _fixture_json_text()


# ---------------------------------------------------------------------------
# _split_leading_non_json
# ---------------------------------------------------------------------------

class TestSplitLeadingNonJson:
    def test_no_preamble(self) -> None:
        preamble, body = _split_leading_non_json('{"a": 1}')
        assert preamble is None
        assert body.startswith("{")

    def test_with_preamble(self) -> None:
        text = "fio: some warning\n{}"
        preamble, body = _split_leading_non_json(text)
        assert preamble == "fio: some warning"
        assert body == "{}"

    def test_no_json_raises(self) -> None:
        with pytest.raises(FioParseError, match="No JSON object"):
            _split_leading_non_json("this is just a log line with no JSON")

    def test_multiline_preamble(self) -> None:
        text = "line one\nline two\n{}"
        preamble, body = _split_leading_non_json(text)
        assert "line one" in preamble
        assert body == "{}"


# ---------------------------------------------------------------------------
# parse_fio_json_text
# ---------------------------------------------------------------------------

class TestParseFioJsonText:
    def test_clean_json_returns_dict(self) -> None:
        payload, preamble = parse_fio_json_text(_fixture_json_text())
        assert isinstance(payload, dict)
        assert preamble is None

    def test_preamble_captured(self) -> None:
        payload, preamble = parse_fio_json_text(_fixture_json_with_preamble())
        assert isinstance(payload, dict)
        assert preamble is not None
        assert "mutexes" in preamble

    def test_invalid_json_raises(self) -> None:
        # "not json at all" contains no '{', so _split_leading_non_json fires first.
        with pytest.raises(FioParseError, match="No JSON object found"):
            parse_fio_json_text("not json at all")

    def test_invalid_json_with_brace_raises(self) -> None:
        # Text that starts a JSON object but is malformed triggers the JSON decoder error.
        with pytest.raises(FioParseError, match="not valid JSON"):
            parse_fio_json_text("{bad json: !!!}")

    def test_non_string_input_raises(self) -> None:
        with pytest.raises(FioParseError, match="Expected str"):
            parse_fio_json_text(b"bytes not str")  # type: ignore[arg-type]

    def test_json_array_raises(self) -> None:
        # A bare JSON array starts with '[', not '{', so the splitter fires.
        with pytest.raises(FioParseError, match="No JSON object found"):
            parse_fio_json_text("[1, 2, 3]")

    def test_json_array_with_preamble_raises(self) -> None:
        # The splitter takes the first '{' and finds '{}' as the JSON body,
        # then the decoder sees trailing ' prefix\n[1, 2, 3]' as extra data.
        with pytest.raises(FioParseError):
            parse_fio_json_text("{} prefix\n[1, 2, 3]")


# ---------------------------------------------------------------------------
# parse_fio_output
# ---------------------------------------------------------------------------

class TestParseFioOutput:
    def test_returns_parsed_fio_output(self) -> None:
        result = parse_fio_output(_fixture_json_text())
        assert isinstance(result, ParsedFioOutput)

    def test_fio_version(self) -> None:
        result = parse_fio_output(_fixture_json_text())
        assert result.fio_version == "fio-3.42"

    def test_timestamp_preserved(self) -> None:
        result = parse_fio_output(_fixture_json_text())
        assert result.timestamp == 1_000_000_000
        assert result.timestamp_ms == 1_000_000_000_000

    def test_raw_preserved(self) -> None:
        result = parse_fio_output(_fixture_json_text())
        assert result.raw is not None
        assert result.raw["fio version"] == "fio-3.42"
        # raw must be the original dict — spot-check a deeply nested field
        assert result.raw["jobs"][0]["jobname"] == "fixture-seq-read"

    def test_raw_is_separate_from_normalized(self) -> None:
        """Mutating raw must not affect the normalized job record."""
        result = parse_fio_output(_fixture_json_text())
        raw_bw = result.raw["jobs"][0]["read"]["bw_bytes"]
        normalized_bw = result.jobs[0].read.throughput.bw_bytes_per_sec
        assert raw_bw == normalized_bw
        # Mutate raw — normalized must be unaffected (it's frozen).
        result.raw["jobs"][0]["read"]["bw_bytes"] = 0
        assert result.jobs[0].read.throughput.bw_bytes_per_sec == normalized_bw

    def test_preamble_round_trip(self) -> None:
        result = parse_fio_output(_fixture_json_with_preamble())
        assert result.leading_non_json_text is not None
        assert "mutexes" in result.leading_non_json_text

    def test_jobs_count(self) -> None:
        result = parse_fio_output(_fixture_json_text())
        assert len(result.jobs) == 1

    def test_missing_jobs_raises(self) -> None:
        bad = dict(FIXTURE_SEQ_READ)
        bad.pop("jobs")
        with pytest.raises(FioParseError):
            parse_fio_output(json.dumps(bad))

    def test_empty_jobs_raises(self) -> None:
        bad = dict(FIXTURE_SEQ_READ)
        bad["jobs"] = []
        with pytest.raises(FioParseError):
            parse_fio_output(json.dumps(bad))


# ---------------------------------------------------------------------------
# Job metadata
# ---------------------------------------------------------------------------

class TestJobMetadata:
    def _job(self) -> object:
        return parse_fio_output(_fixture_json_text()).jobs[0]

    def test_jobname(self) -> None:
        assert self._job().metadata.jobname == "fixture-seq-read"

    def test_error_is_zero(self) -> None:
        assert self._job().metadata.error == 0

    def test_job_options_preserved(self) -> None:
        opts = self._job().metadata.job_options
        assert opts["rw"] == "read"
        assert opts["bs"] == "128k"
        assert opts["iodepth"] == "1"

    def test_job_runtime_ms(self) -> None:
        assert self._job().metadata.job_runtime_ms == 10_000


# ---------------------------------------------------------------------------
# Read direction: throughput and IOPS
# ---------------------------------------------------------------------------

class TestReadThroughputAndIOPS:
    def _read(self) -> object:
        return parse_fio_output(_fixture_json_text()).jobs[0].read

    def test_bw_bytes_per_sec(self) -> None:
        assert self._read().throughput.bw_bytes_per_sec == 131_072_000

    def test_bw_kib_s(self) -> None:
        assert self._read().throughput.bw_kib_s == 128_000

    def test_iops(self) -> None:
        assert self._read().iops.iops == pytest.approx(1_000.0)

    def test_total_ios(self) -> None:
        assert self._read().total_ios == 10_000

    def test_io_bytes(self) -> None:
        assert self._read().io_bytes == 1_310_720_000

    def test_runtime_ms(self) -> None:
        assert self._read().runtime_ms == 10_000


# ---------------------------------------------------------------------------
# Write direction: all-zero reads-only job
# ---------------------------------------------------------------------------

class TestWriteDirectionZero:
    def _write(self) -> object:
        return parse_fio_output(_fixture_json_text()).jobs[0].write

    def test_total_ios_is_zero(self) -> None:
        assert self._write().total_ios == 0

    def test_bw_bytes_is_zero(self) -> None:
        assert self._write().throughput.bw_bytes_per_sec == 0


# ---------------------------------------------------------------------------
# Latency — source units preserved, µs exposed
# ---------------------------------------------------------------------------

class TestLatencyStats:
    def _clat(self) -> object:
        return parse_fio_output(_fixture_json_text()).jobs[0].read.completion_latency

    def test_mean_ns_preserved(self) -> None:
        assert self._clat().mean_ns == pytest.approx(100_000.0)

    def test_mean_us_normalized(self) -> None:
        assert self._clat().mean_us == pytest.approx(100.0)

    def test_min_ns_preserved(self) -> None:
        assert self._clat().min_ns == pytest.approx(50_000.0)

    def test_min_us_normalized(self) -> None:
        assert self._clat().min_us == pytest.approx(50.0)

    def test_max_ns_preserved(self) -> None:
        assert self._clat().max_ns == pytest.approx(500_000.0)

    def test_max_us_normalized(self) -> None:
        assert self._clat().max_us == pytest.approx(500.0)

    def test_unit_is_ns(self) -> None:
        assert self._clat().unit == "ns"

    def test_percentiles_ns_keys_are_strings(self) -> None:
        pcts = self._clat().percentiles_ns
        assert all(isinstance(k, str) for k in pcts)

    def test_p50_ns_stored(self) -> None:
        pcts = self._clat().percentiles_ns
        assert pcts["50.000000"] == pytest.approx(FIXTURE_P50_NS)

    def test_p50_us_property(self) -> None:
        assert self._clat().p50_us == pytest.approx(FIXTURE_P50_US)

    def test_p95_us_property(self) -> None:
        assert self._clat().p95_us == pytest.approx(FIXTURE_P95_US)

    def test_p99_us_property(self) -> None:
        assert self._clat().p99_us == pytest.approx(FIXTURE_P99_US)

    def test_p999_us_property(self) -> None:
        assert self._clat().p999_us == pytest.approx(FIXTURE_P999_US)

    def test_ns_us_ratio(self) -> None:
        """µs value must be exactly 1/1000 of ns value for each percentile."""
        clat = self._clat()
        for ns_val, us_val in (
            (FIXTURE_P50_NS, clat.p50_us),
            (FIXTURE_P95_NS, clat.p95_us),
            (FIXTURE_P99_NS, clat.p99_us),
            (FIXTURE_P999_NS, clat.p999_us),
        ):
            assert us_val == pytest.approx(ns_val / 1_000.0)

    def test_submission_latency_mean_ns(self) -> None:
        slat = parse_fio_output(_fixture_json_text()).jobs[0].read.submission_latency
        assert slat.mean_ns == pytest.approx(2_000.0)

    def test_total_latency_mean_us(self) -> None:
        lat = parse_fio_output(_fixture_json_text()).jobs[0].read.total_latency
        assert lat.mean_us == pytest.approx(102.0)


# ---------------------------------------------------------------------------
# IODepth distribution
# ---------------------------------------------------------------------------

class TestIODepthDistribution:
    def _iodepth(self) -> object:
        return parse_fio_output(_fixture_json_text()).jobs[0].iodepth

    def test_requested_iodepth(self) -> None:
        assert self._iodepth().requested_iodepth == 1

    def test_latency_depth(self) -> None:
        assert self._iodepth().latency_depth == 1

    def test_level_percent_all_in_bucket_1(self) -> None:
        levels = self._iodepth().level_percent
        assert levels["1"] == pytest.approx(100.0)
        assert levels["2"] == pytest.approx(0.0)

    def test_submit_100pct_in_bucket_4(self) -> None:
        # FIO's submit histogram bucket "4" holds 100% in the fixture.
        submit = self._iodepth().submit_percent
        assert submit["4"] == pytest.approx(100.0)

    def test_level_percent_keys_are_strings(self) -> None:
        levels = self._iodepth().level_percent
        assert all(isinstance(k, str) for k in levels)


# ---------------------------------------------------------------------------
# parse_fio_file
# ---------------------------------------------------------------------------

class TestParseFioFile:
    def test_missing_file_raises(self, tmp_path) -> None:
        with pytest.raises(FioParseError, match="not found"):
            parse_fio_file(tmp_path / "nonexistent.json")

    def test_reads_file_correctly(self, tmp_path) -> None:
        p = tmp_path / "fixture.json"
        p.write_text(_fixture_json_text(), encoding="utf-8")
        result = parse_fio_output(p.read_text(encoding="utf-8"))
        assert result.fio_version == "fio-3.42"

    def test_reads_file_with_preamble(self, tmp_path) -> None:
        p = tmp_path / "fixture_with_warning.json"
        p.write_text(_fixture_json_with_preamble(), encoding="utf-8")
        result = parse_fio_file(p)
        assert result.leading_non_json_text is not None
        assert result.jobs[0].metadata.jobname == "fixture-seq-read"
