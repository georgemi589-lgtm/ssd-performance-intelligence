"""Typed, validated records for normalized FIO job output.

These dataclasses are the *normalized* representation of a parsed FIO run.
The untouched, original JSON payload is kept separately on
``ParsedFioOutput.raw`` and is never mutated by anything in this module;
everything else here is derived, typed, and validated from that payload.

Source units are preserved as named (``*_ns`` fields hold nanoseconds, as
FIO stores them). Normalized microsecond values are exposed alongside them
via ``*_us`` properties so callers do not have to remember FIO's unit
conventions or redo the conversion themselves.

This module does not read files, run FIO, or perform any I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

NS_PER_US = 1_000.0


class FioSchemaError(ValueError):
    """Raised when FIO JSON does not match the expected normalized schema."""


def _as_float(value: Any, *, field: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise FioSchemaError(f"Field {field!r} is not numeric: {value!r}") from exc


def _as_int(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise FioSchemaError(f"Field {field!r} is not an integer: {value!r}") from exc


def _as_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise FioSchemaError(f"Field {field!r} must be a mapping, got {type(value).__name__}")
    return value


@dataclass(frozen=True)
class LatencyStats:
    """One FIO latency block (``slat_ns``, ``clat_ns``, or ``lat_ns``).

    Values are stored exactly as FIO reports them, in nanoseconds
    (``unit`` records this). ``*_us`` properties expose the same values
    normalized to microseconds without altering the stored data.
    """

    unit: str
    min_ns: float | None
    max_ns: float | None
    mean_ns: float | None
    stddev_ns: float | None
    samples: int | None
    percentiles_ns: dict[str, float]

    @property
    def min_us(self) -> float | None:
        return None if self.min_ns is None else self.min_ns / NS_PER_US

    @property
    def max_us(self) -> float | None:
        return None if self.max_ns is None else self.max_ns / NS_PER_US

    @property
    def mean_us(self) -> float | None:
        return None if self.mean_ns is None else self.mean_ns / NS_PER_US

    @property
    def stddev_us(self) -> float | None:
        return None if self.stddev_ns is None else self.stddev_ns / NS_PER_US

    def percentile_us(self, label: str) -> float | None:
        """Return a stored percentile (looked up by FIO's own key), in µs."""
        value = self.percentiles_ns.get(label)
        return None if value is None else value / NS_PER_US

    def _nearest_percentile_us(self, pct: float) -> float | None:
        for label in (f"{pct:.6f}", f"{pct:.1f}", f"{pct:g}", str(pct)):
            if label in self.percentiles_ns:
                return self.percentile_us(label)
        return None

    @property
    def p50_us(self) -> float | None:
        return self._nearest_percentile_us(50)

    @property
    def p95_us(self) -> float | None:
        return self._nearest_percentile_us(95)

    @property
    def p99_us(self) -> float | None:
        return self._nearest_percentile_us(99)

    @property
    def p999_us(self) -> float | None:
        return self._nearest_percentile_us(99.9)

    @classmethod
    def from_dict(cls, block: dict[str, Any] | None, *, field: str) -> "LatencyStats":
        if block is None:
            return cls(
                unit="ns",
                min_ns=None,
                max_ns=None,
                mean_ns=None,
                stddev_ns=None,
                samples=None,
                percentiles_ns={},
            )
        block = _as_mapping(block, field=field)
        percentiles_raw = _as_mapping(block.get("percentile"), field=f"{field}.percentile")
        percentiles = {
            str(key): _as_float(value, field=f"{field}.percentile.{key}")
            for key, value in percentiles_raw.items()
        }
        return cls(
            unit="ns",
            min_ns=_as_float(block.get("min"), field=f"{field}.min"),
            max_ns=_as_float(block.get("max"), field=f"{field}.max"),
            mean_ns=_as_float(block.get("mean"), field=f"{field}.mean"),
            stddev_ns=_as_float(block.get("stddev"), field=f"{field}.stddev"),
            samples=_as_int(block.get("N"), field=f"{field}.N"),
            percentiles_ns=percentiles,
        )


@dataclass(frozen=True)
class ThroughputStats:
    """Bandwidth fields from a read/write/trim/sync block.

    ``bw_bytes_per_sec`` is FIO's ``bw_bytes`` (bytes/sec). The remaining
    ``bw*`` fields are FIO's ``bw`` family, stored in KiB/s as FIO reports
    them.
    """

    bw_bytes_per_sec: float | None
    bw_kib_s: float | None
    bw_min_kib_s: float | None
    bw_max_kib_s: float | None
    bw_mean_kib_s: float | None
    bw_dev_kib_s: float | None
    bw_samples: int | None
    bw_agg_percent: float | None

    @classmethod
    def from_dict(cls, block: dict[str, Any] | None, *, field: str) -> "ThroughputStats":
        block = _as_mapping(block, field=field)
        return cls(
            bw_bytes_per_sec=_as_float(block.get("bw_bytes"), field=f"{field}.bw_bytes"),
            bw_kib_s=_as_float(block.get("bw"), field=f"{field}.bw"),
            bw_min_kib_s=_as_float(block.get("bw_min"), field=f"{field}.bw_min"),
            bw_max_kib_s=_as_float(block.get("bw_max"), field=f"{field}.bw_max"),
            bw_mean_kib_s=_as_float(block.get("bw_mean"), field=f"{field}.bw_mean"),
            bw_dev_kib_s=_as_float(block.get("bw_dev"), field=f"{field}.bw_dev"),
            bw_samples=_as_int(block.get("bw_samples"), field=f"{field}.bw_samples"),
            bw_agg_percent=_as_float(block.get("bw_agg"), field=f"{field}.bw_agg"),
        )


@dataclass(frozen=True)
class IOPSStats:
    """IOPS fields from a read/write/trim/sync block."""

    iops: float | None
    iops_min: float | None
    iops_max: float | None
    iops_mean: float | None
    iops_stddev: float | None
    iops_samples: int | None

    @classmethod
    def from_dict(cls, block: dict[str, Any] | None, *, field: str) -> "IOPSStats":
        block = _as_mapping(block, field=field)
        return cls(
            iops=_as_float(block.get("iops"), field=f"{field}.iops"),
            iops_min=_as_float(block.get("iops_min"), field=f"{field}.iops_min"),
            iops_max=_as_float(block.get("iops_max"), field=f"{field}.iops_max"),
            iops_mean=_as_float(block.get("iops_mean"), field=f"{field}.iops_mean"),
            iops_stddev=_as_float(block.get("iops_stddev"), field=f"{field}.iops_stddev"),
            iops_samples=_as_int(block.get("iops_samples"), field=f"{field}.iops_samples"),
        )


@dataclass(frozen=True)
class DirectionStats:
    """One directional block (``read``, ``write``, ``trim``, or ``sync``)."""

    direction: str
    total_ios: int | None
    io_bytes: int | None
    io_kbytes: int | None
    runtime_ms: float | None
    throughput: ThroughputStats
    iops: IOPSStats
    submission_latency: LatencyStats
    completion_latency: LatencyStats
    total_latency: LatencyStats

    @classmethod
    def from_dict(cls, block: dict[str, Any] | None, *, direction: str) -> "DirectionStats":
        block = _as_mapping(block, field=direction)
        return cls(
            direction=direction,
            total_ios=_as_int(block.get("total_ios"), field=f"{direction}.total_ios"),
            io_bytes=_as_int(block.get("io_bytes"), field=f"{direction}.io_bytes"),
            io_kbytes=_as_int(block.get("io_kbytes"), field=f"{direction}.io_kbytes"),
            runtime_ms=_as_float(block.get("runtime"), field=f"{direction}.runtime"),
            throughput=ThroughputStats.from_dict(block, field=direction),
            iops=IOPSStats.from_dict(block, field=direction),
            submission_latency=LatencyStats.from_dict(block.get("slat_ns"), field=f"{direction}.slat_ns"),
            completion_latency=LatencyStats.from_dict(block.get("clat_ns"), field=f"{direction}.clat_ns"),
            total_latency=LatencyStats.from_dict(block.get("lat_ns"), field=f"{direction}.lat_ns"),
        )


@dataclass(frozen=True)
class IODepthDistribution:
    """Requested vs. achieved queue-depth distribution for one job.

    ``level_percent`` is FIO's ``iodepth_level`` (percent of samples that
    landed in each depth bucket — this is the *achieved* distribution).
    ``submit_percent``/``complete_percent`` are FIO's submit/complete
    histograms, which use FIO's own bucket labels and are not a second
    requested queue depth.
    """

    level_percent: dict[str, float]
    submit_percent: dict[str, float]
    complete_percent: dict[str, float]
    requested_iodepth: int | None
    latency_depth: int | None

    @classmethod
    def from_job_dict(cls, job: dict[str, Any]) -> "IODepthDistribution":
        def _percent_map(raw: Any, field: str) -> dict[str, float]:
            raw = _as_mapping(raw, field=field)
            return {str(key): _as_float(value, field=f"{field}.{key}") for key, value in raw.items()}

        job_options = _as_mapping(job.get("job options"), field="job options")
        requested = job_options.get("iodepth")
        return cls(
            level_percent=_percent_map(job.get("iodepth_level"), "iodepth_level"),
            submit_percent=_percent_map(job.get("iodepth_submit"), "iodepth_submit"),
            complete_percent=_percent_map(job.get("iodepth_complete"), "iodepth_complete"),
            requested_iodepth=_as_int(requested, field="job options.iodepth"),
            latency_depth=_as_int(job.get("latency_depth"), field="latency_depth"),
        )


@dataclass(frozen=True)
class JobMetadata:
    """Non-metric identifying fields for one FIO job."""

    jobname: str
    groupid: int | None
    error: int | None
    job_options: dict[str, Any]
    job_runtime_ms: float | None
    elapsed_s: float | None
    job_start_ms: float | None
    usr_cpu: float | None
    sys_cpu: float | None
    ctx: int | None
    majf: int | None
    minf: int | None

    @classmethod
    def from_dict(cls, job: dict[str, Any]) -> "JobMetadata":
        jobname = job.get("jobname")
        if not isinstance(jobname, str) or not jobname:
            raise FioSchemaError("Job is missing a required non-empty string 'jobname'")
        job_options = _as_mapping(job.get("job options"), field="job options")
        return cls(
            jobname=jobname,
            groupid=_as_int(job.get("groupid"), field="groupid"),
            error=_as_int(job.get("error"), field="error"),
            job_options=dict(job_options),
            job_runtime_ms=_as_float(job.get("job_runtime"), field="job_runtime"),
            elapsed_s=_as_float(job.get("elapsed"), field="elapsed"),
            job_start_ms=_as_float(job.get("job_start"), field="job_start"),
            usr_cpu=_as_float(job.get("usr_cpu"), field="usr_cpu"),
            sys_cpu=_as_float(job.get("sys_cpu"), field="sys_cpu"),
            ctx=_as_int(job.get("ctx"), field="ctx"),
            majf=_as_int(job.get("majf"), field="majf"),
            minf=_as_int(job.get("minf"), field="minf"),
        )


@dataclass(frozen=True)
class FioJobRecord:
    """One normalized, validated FIO job (one entry of the JSON ``jobs`` list)."""

    metadata: JobMetadata
    read: DirectionStats
    write: DirectionStats
    trim: DirectionStats | None
    sync: DirectionStats | None
    iodepth: IODepthDistribution

    @classmethod
    def from_dict(cls, job: dict[str, Any]) -> "FioJobRecord":
        if not isinstance(job, dict):
            raise FioSchemaError(f"Each FIO job entry must be a mapping, got {type(job).__name__}")
        return cls(
            metadata=JobMetadata.from_dict(job),
            read=DirectionStats.from_dict(job.get("read"), direction="read"),
            write=DirectionStats.from_dict(job.get("write"), direction="write"),
            trim=DirectionStats.from_dict(job.get("trim"), direction="trim") if job.get("trim") else None,
            sync=DirectionStats.from_dict(job.get("sync"), direction="sync") if job.get("sync") else None,
            iodepth=IODepthDistribution.from_job_dict(job),
        )


@dataclass(frozen=True)
class ParsedFioOutput:
    """A fully parsed FIO JSON artifact.

    ``raw`` is the untouched JSON payload (``dict``), preserved exactly as
    parsed. ``jobs`` holds the normalized, validated records derived from
    ``raw["jobs"]``. The two are kept as separate attributes on purpose so
    normalization never silently discards or mutates the original data.
    """

    raw: dict[str, Any]
    fio_version: str | None
    timestamp: int | None
    timestamp_ms: int | None
    time: str | None
    global_options: dict[str, Any]
    jobs: tuple[FioJobRecord, ...]
    leading_non_json_text: str | None

    @classmethod
    def from_raw(cls, raw: dict[str, Any], *, leading_non_json_text: str | None = None) -> "ParsedFioOutput":
        if not isinstance(raw, dict):
            raise FioSchemaError(f"Top-level FIO output must be a JSON object, got {type(raw).__name__}")
        jobs_raw = raw.get("jobs")
        if not isinstance(jobs_raw, list) or not jobs_raw:
            raise FioSchemaError("FIO output must contain a non-empty 'jobs' list")
        jobs = tuple(FioJobRecord.from_dict(job) for job in jobs_raw)
        global_options = _as_mapping(raw.get("global options"), field="global options")
        return cls(
            raw=raw,
            fio_version=raw.get("fio version"),
            timestamp=_as_int(raw.get("timestamp"), field="timestamp"),
            timestamp_ms=_as_int(raw.get("timestamp_ms"), field="timestamp_ms"),
            time=raw.get("time"),
            global_options=dict(global_options),
            jobs=jobs,
            leading_non_json_text=leading_non_json_text,
        )
