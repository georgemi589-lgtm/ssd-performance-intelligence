"""Minimal synthetic FIO 3.42 JSON fixtures for unit tests.

These fixtures are hand-crafted to match the FIO 3.42 JSON schema shape
observed in ``data/raw/exp001.json`` (and described in
``experiments/EXP001.md``).  All numeric values are synthetic and chosen
only for convenient arithmetic in assertions.  They do not represent any
real device measurement.

To add a new fixture, define a module-level dict or function below and
import it in your test module.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Minimal valid single-job sequential-read fixture
# ---------------------------------------------------------------------------
FIXTURE_SEQ_READ: dict[str, Any] = {
    "fio version": "fio-3.42",
    "timestamp": 1000000000,
    "timestamp_ms": 1000000000000,
    "time": "Thu Jan  1 00:00:00 2026",
    "global options": {},
    "jobs": [
        {
            "jobname": "fixture-seq-read",
            "groupid": 0,
            "error": 0,
            "job options": {
                "rw": "read",
                "bs": "128k",
                "iodepth": "1",
                "ioengine": "libaio",
                "direct": "1",
                "runtime": "10",
                "time_based": "1",
                "filename": "/tmp/fio-lab/fixture_testfile.bin",
            },
            "read": {
                "io_bytes": 1310720000,
                "io_kbytes": 1280000,
                "bw_bytes": 131072000,
                "bw": 128000,
                "iops": 1000.0,
                "runtime": 10000,
                "total_ios": 10000,
                "short_ios": 0,
                "drop_ios": 0,
                "slat_ns": {
                    "min": 1000,
                    "max": 5000,
                    "mean": 2000.0,
                    "stddev": 500.0,
                    "N": 10000,
                    "percentile": {},
                },
                "clat_ns": {
                    "min": 50000,
                    "max": 500000,
                    "mean": 100000.0,
                    "stddev": 20000.0,
                    "N": 10000,
                    "percentile": {
                        "1.000000": 60000,
                        "5.000000": 65000,
                        "10.000000": 70000,
                        "20.000000": 75000,
                        "30.000000": 80000,
                        "40.000000": 90000,
                        "50.000000": 100000,   # p50
                        "60.000000": 110000,
                        "70.000000": 120000,
                        "80.000000": 140000,
                        "90.000000": 160000,
                        "95.000000": 200000,   # p95
                        "99.000000": 300000,   # p99
                        "99.500000": 400000,
                        "99.900000": 480000,   # p99.9
                        "99.950000": 490000,
                        "99.990000": 500000,
                    },
                },
                "lat_ns": {
                    "min": 52000,
                    "max": 505000,
                    "mean": 102000.0,
                    "stddev": 20100.0,
                    "N": 10000,
                    "percentile": {},
                },
                "bw_min": 120000,
                "bw_max": 135000,
                "bw_agg": 99.5,
                "bw_mean": 127000.0,
                "bw_dev": 3000.0,
                "bw_samples": 10,
                "iops_min": 937,
                "iops_max": 1054,
                "iops_mean": 992.0,
                "iops_stddev": 23.0,
                "iops_samples": 10,
            },
            "write": {
                "io_bytes": 0,
                "io_kbytes": 0,
                "bw_bytes": 0,
                "bw": 0,
                "iops": 0.0,
                "runtime": 0,
                "total_ios": 0,
                "short_ios": 0,
                "drop_ios": 0,
                "slat_ns": {"min": 0, "max": 0, "mean": 0.0, "stddev": 0.0, "N": 0, "percentile": {}},
                "clat_ns": {"min": 0, "max": 0, "mean": 0.0, "stddev": 0.0, "N": 0, "percentile": {}},
                "lat_ns":  {"min": 0, "max": 0, "mean": 0.0, "stddev": 0.0, "N": 0, "percentile": {}},
                "bw_min": 0, "bw_max": 0, "bw_agg": 0.0,
                "bw_mean": 0.0, "bw_dev": 0.0, "bw_samples": 0,
                "iops_min": 0, "iops_max": 0, "iops_mean": 0.0,
                "iops_stddev": 0.0, "iops_samples": 0,
            },
            "trim": None,
            "sync": {
                "total_ios": 0,
                "lat_ns": {"min": 0, "max": 0, "mean": 0.0, "stddev": 0.0, "N": 0, "percentile": {}},
            },
            "job_runtime": 10000,
            "usr_cpu": 1.5,
            "sys_cpu": 0.5,
            "ctx": 10002,
            "majf": 0,
            "minf": 5,
            "iodepth_level": {
                "1": 100.000000,
                "2": 0.000000,
                "4": 0.000000,
                "8": 0.000000,
                "16": 0.000000,
                "32": 0.000000,
                ">=64": 0.000000,
            },
            "iodepth_submit": {
                "0": 0.000000,
                "4": 100.000000,
                "8": 0.000000,
                "16": 0.000000,
                "32": 0.000000,
                "64": 0.000000,
                ">=64": 0.000000,
            },
            "iodepth_complete": {
                "0": 0.000000,
                "4": 100.000000,
                "8": 0.000000,
                "16": 0.000000,
                "32": 0.000000,
                "64": 0.000000,
                ">=64": 0.000000,
            },
            "latency_depth": 1,
            "elapsed": 11,
            "job_start": 1000000000000,
        }
    ],
    "disk_util": [],
}

# FIO raw text with a leading non-JSON warning line, matching the artifact
# shape of data/raw/exp001.json (Windows platform warning prepended to JSON).
FIXTURE_SEQ_READ_WITH_PREAMBLE_TEXT: str = (
    "fio: this platform does not support process shared mutexes, "
    "forcing use of threads. Use the 'thread' option to get rid of this warning.\n"
)

# Convenience: the synthetic p50 clat in nanoseconds (as stored by FIO).
FIXTURE_P50_NS: int = 100_000
FIXTURE_P95_NS: int = 200_000
FIXTURE_P99_NS: int = 300_000
FIXTURE_P999_NS: int = 480_000

# The same values in microseconds (1 ns = 0.001 µs).
FIXTURE_P50_US: float = FIXTURE_P50_NS / 1_000.0
FIXTURE_P95_US: float = FIXTURE_P95_NS / 1_000.0
FIXTURE_P99_US: float = FIXTURE_P99_NS / 1_000.0
FIXTURE_P999_US: float = FIXTURE_P999_NS / 1_000.0
