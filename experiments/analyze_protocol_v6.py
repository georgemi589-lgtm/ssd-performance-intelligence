"""Audited analysis of the Protocol v6 4 KiB sequential-read QD4/QD8 study.

Run from the repository root:
    python experiments/analyze_protocol_v6.py
    python experiments/analyze_protocol_v6.py --write-report

This script reads existing configuration, metadata, and raw FIO files only. It
never invokes FIO, changes benchmark artifacts, or edits the observations ledger.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "configs"
RAW_DIR = REPO_ROOT / "data" / "raw"
REPORT_PATH = REPO_ROOT / "reports" / "PROTOCOL_V6_CONFIRMATION_ANALYSIS.md"
TARGET_FILE = r"C:\fio-lab\exp001_testfile.bin"
SCHEDULE_ID = "v6-4k-seq-qd4-qd8-paired-5block-v1"

# experiment number: condition, replicate, block, within-block position
SCHEDULE: dict[int, tuple[str, int, int, int]] = {
    47: ("QD8", 1, 1, 1), 48: ("QD4", 1, 1, 2),
    49: ("QD4", 2, 2, 1), 50: ("QD8", 2, 2, 2),
    51: ("QD4", 3, 3, 1), 52: ("QD8", 3, 3, 2),
    53: ("QD8", 4, 4, 1), 54: ("QD4", 4, 4, 2),
    55: ("QD4", 5, 5, 1), 56: ("QD8", 5, 5, 2),
}


class AuditError(RuntimeError):
    """Raised when a Protocol v6 artifact fails validation."""


@dataclass(frozen=True)
class Observation:
    experiment_id: str
    run_order: int
    condition: str
    replicate: int
    block_id: int
    position: int
    iops: float
    bandwidth_bps: float
    mean_total_latency_us: float
    clat_mean_us: float | None
    slat_mean_us: float | None
    clat_p50_us: float | None
    clat_p95_us: float | None
    clat_p99_us: float | None
    clat_p999_us: float | None
    iodepth_level: dict[str, float]
    fio_version: str
    power_state: str
    background_activity: str
    system_update_state: str
    cpu_count: str
    target_free_bytes: str


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot parse {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError(f"Expected a JSON object in {path}")
    return payload


def finite_number(value: Any, field: str, experiment_id: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise AuditError(f"{experiment_id}: {field} is missing or non-numeric") from exc
    if not math.isfinite(result):
        raise AuditError(f"{experiment_id}: {field} is not finite")
    return result


def optional_finite(value: Any, field: str, experiment_id: str) -> float | None:
    return None if value is None else finite_number(value, field, experiment_id)


def summarize(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("Cannot summarize an empty sequence")
    average = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "n": float(len(values)),
        "mean": average,
        "median": statistics.median(values),
        "sd": sd,
        "cv_pct": sd / average * 100.0 if average else 0.0,
        "min": min(values),
        "max": max(values),
    }


def paired_differences(rows: list[Observation], field: str = "iops") -> list[tuple[int, float]]:
    """Return QD4 minus QD8 for each block, preserving block order."""
    paired: list[tuple[int, float]] = []
    for block in range(1, 6):
        group = [row for row in rows if row.block_id == block]
        by_condition = {row.condition: row for row in group}
        if len(group) != 2 or set(by_condition) != {"QD4", "QD8"}:
            raise ValueError(f"Block {block} must contain exactly one QD4 and one QD8 observation")
        paired.append((
            block,
            float(getattr(by_condition["QD4"], field)) - float(getattr(by_condition["QD8"], field)),
        ))
    return paired


def load_observations() -> list[Observation]:
    from ssd_performance_intelligence.data.fio_parser import FioParseError, parse_fio_file

    errors: list[str] = []
    observations: list[Observation] = []
    for number, expected in SCHEDULE.items():
        experiment_id = f"EXP{number:03d}"
        config_path = CONFIG_DIR / f"exp{number:03d}.yaml"
        raw_path = RAW_DIR / f"exp{number:03d}.json"
        metadata_path = RAW_DIR / f"exp{number:03d}.metadata.json"
        condition, replicate, block, position = expected
        expected_protocol = {
            "version": "6",
            "replicate_index": replicate,
            "run_order": number - 46,
            "block_id": block,
            "within_block_order": position,
            "condition": condition,
            "schedule_id": SCHEDULE_ID,
        }
        try:
            for artifact in (config_path, raw_path, metadata_path):
                if not artifact.is_file():
                    raise AuditError(f"Missing artifact: {artifact.relative_to(REPO_ROOT)}")

            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if not isinstance(config, dict) or config.get("experiment_id") != experiment_id:
                raise AuditError(f"{experiment_id}: invalid config or experiment_id")
            protocol = config.get("protocol")
            if not isinstance(protocol, dict):
                raise AuditError(f"{experiment_id}: config protocol block is missing")
            for key, value in expected_protocol.items():
                if str(protocol.get(key)) != str(value):
                    raise AuditError(
                        f"{experiment_id}: config protocol.{key}={protocol.get(key)!r}, expected {value!r}"
                    )

            fio = config.get("fio")
            depth = int(condition[2:])
            if not isinstance(fio, dict):
                raise AuditError(f"{experiment_id}: config fio block is missing")
            required_fio = {
                "rw": "read", "bs": "4k", "size": "256M", "iodepth": depth,
                "ioengine": "windowsaio", "direct": 1, "runtime": 10,
                "time_based": 1, "thread": 1,
            }
            for key, value in required_fio.items():
                if fio.get(key) != value:
                    raise AuditError(
                        f"{experiment_id}: fio.{key}={fio.get(key)!r}, expected {value!r}"
                    )
            normalize_path = lambda value: str(value).replace("/", "\\").casefold()
            if normalize_path(fio.get("filename", "")) != normalize_path(TARGET_FILE):
                raise AuditError(f"{experiment_id}: target differs from the Protocol v6 file target")
            safety = config.get("safety")
            if not isinstance(safety, dict) or safety.get("allow_destructive_benchmarks") is not False:
                raise AuditError(f"{experiment_id}: destructive benchmarks are not explicitly disabled")
            if safety.get("allow_system_disk_tests") is not False:
                raise AuditError(f"{experiment_id}: system-disk tests are not explicitly disabled")
            if fio.get("name") != f"exp{number:03d}-seq-read-{condition.casefold()}":
                raise AuditError(f"{experiment_id}: FIO job name does not match its scheduled condition")

            metadata = read_json(metadata_path)
            if metadata.get("experiment_id") != experiment_id:
                raise AuditError(f"{experiment_id}: metadata experiment_id mismatch")
            metadata_protocol = metadata.get("protocol")
            if not isinstance(metadata_protocol, dict):
                raise AuditError(f"{experiment_id}: metadata protocol block is missing")
            for key, value in expected_protocol.items():
                if str(metadata_protocol.get(key)) != str(value):
                    raise AuditError(f"{experiment_id}: metadata protocol.{key} mismatch")
            host = metadata.get("host_state")
            if not isinstance(host, dict):
                raise AuditError(f"{experiment_id}: metadata host_state block is missing")
            for key in ("power_state", "background_activity", "system_update_state"):
                value = host.get(key)
                if (not isinstance(value, str) or not value.strip()
                        or value.strip().upper().startswith("REPLACE_")):
                    raise AuditError(f"{experiment_id}: host_state.{key} is blank or a placeholder")

            try:
                parsed = parse_fio_file(raw_path)
            except FioParseError as exc:
                raise AuditError(f"{experiment_id}: FIO parser rejected raw JSON: {exc}") from exc
            if len(parsed.jobs) != 1:
                raise AuditError(f"{experiment_id}: expected one FIO job; found {len(parsed.jobs)}")
            job = parsed.jobs[0]
            if job.metadata.jobname != fio.get("name"):
                raise AuditError(f"{experiment_id}: raw FIO jobname does not match config")
            if job.metadata.error not in (None, 0):
                raise AuditError(f"{experiment_id}: FIO job reported error {job.metadata.error}")
            if job.iodepth.requested_iodepth != depth:
                raise AuditError(f"{experiment_id}: raw JSON requested queue depth does not match config")
            if job.write.total_ios not in (None, 0):
                raise AuditError(f"{experiment_id}: raw JSON reports write I/O in the read-only protocol")

            snapshot = metadata.get("host_snapshot") or {}
            read = job.read
            observations.append(Observation(
                experiment_id=experiment_id,
                run_order=number - 46,
                condition=condition,
                replicate=replicate,
                block_id=block,
                position=position,
                iops=finite_number(read.iops.iops, "read IOPS", experiment_id),
                bandwidth_bps=finite_number(read.throughput.bw_bytes_per_sec, "read bandwidth", experiment_id),
                mean_total_latency_us=finite_number(read.total_latency.mean_us, "mean total latency", experiment_id),
                clat_mean_us=optional_finite(read.completion_latency.mean_us, "mean completion latency", experiment_id),
                slat_mean_us=optional_finite(read.submission_latency.mean_us, "mean submission latency", experiment_id),
                clat_p50_us=optional_finite(read.completion_latency.p50_us, "clat p50", experiment_id),
                clat_p95_us=optional_finite(read.completion_latency.p95_us, "clat p95", experiment_id),
                clat_p99_us=optional_finite(read.completion_latency.p99_us, "clat p99", experiment_id),
                clat_p999_us=optional_finite(read.completion_latency.p999_us, "clat p99.9", experiment_id),
                iodepth_level=dict(job.iodepth.level_percent or {}),
                fio_version=parsed.fio_version or "unknown",
                power_state=host["power_state"].strip(),
                background_activity=host["background_activity"].strip(),
                system_update_state=host["system_update_state"].strip(),
                cpu_count=str(snapshot.get("cpu_count", "")),
                target_free_bytes=str(snapshot.get("target_volume_free_bytes_before_run", "")),
            ))
        except (AuditError, OSError, ValueError, TypeError, AttributeError) as exc:
            errors.append(str(exc))

    if errors:
        raise AuditError("Protocol v6 artifact audit failed:\n- " + "\n- ".join(errors))
    if len(observations) != 10:
        raise AuditError(f"Expected 10 observations, found {len(observations)}")
    return observations


def fmt(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def condition_mean(rows: list[Observation], condition: str, field: str) -> float | None:
    values = [getattr(row, field) for row in rows if row.condition == condition]
    available = [float(value) for value in values if value is not None]
    return statistics.mean(available) if available else None


def make_report(rows: list[Observation]) -> str:
    versions = sorted({row.fio_version for row in rows})
    version_text = (
        f"All ten raw artifacts report FIO {versions[0]}."
        if len(versions) == 1
        else "FIO versions differ across this study: " + ", ".join(versions) +
             ". Treat version variation as a possible confound."
    )
    qd4_rows = [row for row in rows if row.condition == "QD4"]
    qd8_rows = [row for row in rows if row.condition == "QD8"]
    qd4_mean_iops = statistics.mean(row.iops for row in qd4_rows)
    qd8_mean_iops = statistics.mean(row.iops for row in qd8_rows)
    qd4_mean_total = statistics.mean(row.mean_total_latency_us for row in qd4_rows)
    qd8_mean_total = statistics.mean(row.mean_total_latency_us for row in qd8_rows)
    iops_uplift_pct = (qd8_mean_iops / qd4_mean_iops - 1.0) * 100.0
    latency_uplift_pct = (qd8_mean_total / qd4_mean_total - 1.0) * 100.0
    qd4_depth2 = statistics.mean(row.iodepth_level.get("2", 0.0) for row in qd4_rows)
    qd4_depth4 = statistics.mean(row.iodepth_level.get("4", 0.0) for row in qd4_rows)
    qd8_depth4 = statistics.mean(row.iodepth_level.get("4", 0.0) for row in qd8_rows)
    qd8_depth8 = statistics.mean(row.iodepth_level.get("8", 0.0) for row in qd8_rows)
    lines = [
        "# Protocol v6 — 4 KiB Sequential-Read QD4/QD8 Analysis",
        "",
        "## Artifact audit",
        "",
        "All ten scheduled configs, raw JSON files, and metadata sidecars passed the local audit. The project parser accepted each artifact; each run has one job with the expected job name and requested queue depth, no reported job error, and no reported write I/O.",
        "",
        f"- Scheduled runs validated: {len(rows)}/10",
        f"- FIO versions: {', '.join(versions)}",
        version_text,
        "",
        "## Design and workload",
        "",
        "Five paired blocks compare QD4 and QD8 at 4 KiB sequential reads against the same file-based target. Configured size is 256 MiB; runtime is 10 seconds; direct I/O is enabled; the engine is Windowsaio; and thread=1. The condition order is prespecified and counterbalanced, not randomized.",
        "",
        "## Findings at a glance",
        "",
        f"QD8 averaged {qd8_mean_iops:.1f} IOPS versus {qd4_mean_iops:.1f} at QD4, a {iops_uplift_pct:.1f}% higher mean; QD8 had higher IOPS in {sum(value < 0 for _, value in paired_differences(rows))}/5 paired blocks. This is a descriptive result for the configured settings on this host.",
        f"Mean total latency averaged {qd8_mean_total:.1f} µs at QD8 and {qd4_mean_total:.1f} µs at QD4 ({latency_uplift_pct:.1f}% higher at QD8). Latency percentiles do not show a uniform condition winner and are sensitive to the high-tail EXP052 and EXP055 runs.",
        f"The mean FIO depth-bucket shares were QD4: {qd4_depth4:.1f}% in bucket 4 and {qd4_depth2:.1f}% in bucket 2; QD8: {qd8_depth8:.1f}% in bucket 8 and {qd8_depth4:.1f}% in bucket 4. Therefore, describe this as a comparison of requested iodepth settings; the histogram does not show every I/O being issued at the requested maximum depth.",
        "All findings are specific to these five pairs, this host, and this file-based workload. The order was counterbalanced but not randomized; no population-level or device-internal causal inference is justified.",
        "",
        "## Scheduled observations",
        "",
        "| Run | Experiment | Block | Position | Condition | FIO | IOPS | Bandwidth (B/s) | Mean total latency (µs) | Mean clat (µs) | Mean slat (µs) |",
        "|---:|---|---:|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.run_order} | {row.experiment_id} | {row.block_id} | {row.position} | {row.condition} | "
            f"{row.fio_version} | {row.iops:.1f} | {row.bandwidth_bps:.0f} | {row.mean_total_latency_us:.1f} | "
            f"{fmt(row.clat_mean_us)} | {fmt(row.slat_mean_us)} |"
        )

    lines += [
        "",
        "## Condition-level descriptive statistics",
        "",
        "| Condition | n | Mean IOPS | Median IOPS | Sample SD IOPS | IOPS CV | Mean BW (MB/s) | Mean total latency (µs) | Mean clat (µs) | Mean slat (µs) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in ("QD4", "QD8"):
        group = [row for row in rows if row.condition == condition]
        iops = summarize([row.iops for row in group])
        bw = statistics.mean(row.bandwidth_bps for row in group) / 1_000_000
        total = statistics.mean(row.mean_total_latency_us for row in group)
        lines.append(
            f"| {condition} | 5 | {iops['mean']:.1f} | {iops['median']:.1f} | {iops['sd']:.1f} | "
            f"{iops['cv_pct']:.2f}% | {bw:.2f} | {total:.1f} | "
            f"{fmt(condition_mean(rows, condition, 'clat_mean_us'))} | "
            f"{fmt(condition_mean(rows, condition, 'slat_mean_us'))} |"
        )

    diffs = paired_differences(rows, "iops")
    diff_values = [value for _, value in diffs]
    diff_summary = summarize(diff_values)
    lines += [
        "",
        "## Paired IOPS comparison",
        "",
        "The prespecified primary outcome is D_b = IOPS(QD4)_b − IOPS(QD8)_b. Negative differences favor QD8 for observed throughput; positive differences favor QD4.",
        "",
        "| Block | QD4 run | QD4 IOPS | QD8 run | QD8 IOPS | D = QD4 − QD8 | Difference relative to QD8 |",
        "|---:|---|---:|---|---:|---:|---:|",
    ]
    for block, diff in diffs:
        group = {row.condition: row for row in rows if row.block_id == block}
        qd4, qd8 = group["QD4"], group["QD8"]
        relative = diff / qd8.iops * 100 if qd8.iops else float("nan")
        lines.append(
            f"| {block} | {qd4.experiment_id} | {qd4.iops:.1f} | {qd8.experiment_id} | "
            f"{qd8.iops:.1f} | {diff:+.1f} | {relative:+.2f}% |"
        )

    bw_diffs = paired_differences(rows, "bandwidth_bps")
    lat_diffs = paired_differences(rows, "mean_total_latency_us")
    lines += [
        "",
        f"- Mean paired IOPS difference: **{diff_summary['mean']:+.1f}**; median: **{diff_summary['median']:+.1f}**; sample SD: **{diff_summary['sd']:.1f}**.",
        f"- Blocks with QD4 higher IOPS than QD8: **{sum(value > 0 for _, value in diffs)}/5**.",
        f"- Mean paired bandwidth difference (QD4 − QD8): **{statistics.mean(value for _, value in bw_diffs) / 1_000_000:+.2f} MB/s**.",
        f"- Mean paired total-latency difference (QD4 − QD8): **{statistics.mean(value for _, value in lat_diffs):+.1f} µs**.",
        "",
        "## Completion-latency percentiles",
        "",
        "These are arithmetic means of five per-run FIO completion-latency percentiles (clat), not percentiles calculated from all requests pooled together. Completion latency (clat), submission latency (slat), and total latency (lat) are distinct measurements.",
        "",
        "| Condition | Mean per-run clat p50 (µs) | p95 (µs) | p99 (µs) | p99.9 (µs) |",
        "|---|---:|---:|---:|---:|",
    ]
    for condition in ("QD4", "QD8"):
        group = [row for row in rows if row.condition == condition]
        vals = []
        for field in ("clat_p50_us", "clat_p95_us", "clat_p99_us", "clat_p999_us"):
            available = [getattr(row, field) for row in group if getattr(row, field) is not None]
            vals.append(fmt(statistics.mean(available) if available else None))
        lines.append(f"| {condition} | " + " | ".join(vals) + " |")

    lines += [
        "",
        "## Per-run completion latency and achieved queue depth",
        "",
        "FIO depth histograms report percentages in depth buckets, not percentages of wall-clock time. Read the histogram alongside requested queue depth; it does not prove every request ran at the requested depth.",
        "",
        "| Experiment | Condition | clat p50 (µs) | p95 (µs) | p99 (µs) | p99.9 (µs) | Achieved-depth histogram |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        hist = json.dumps(row.iodepth_level, sort_keys=True, ensure_ascii=True)
        lines.append(
            f"| {row.experiment_id} | {row.condition} | {fmt(row.clat_p50_us)} | {fmt(row.clat_p95_us)} | "
            f"{fmt(row.clat_p99_us)} | {fmt(row.clat_p999_us)} | {hist} |"
        )

    lines += [
        "",
        "## Recorded host state",
        "",
        "| Experiment | Power | Background activity | Update state | CPU count | Free bytes before run |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.experiment_id} | {row.power_state} | {row.background_activity} | "
            f"{row.system_update_state} | {row.cpu_count} | {row.target_free_bytes} |"
        )

    qd4_all = [row.iops for row in rows if row.condition == "QD4"]
    qd4_without_exp055 = [
        row.iops for row in rows if row.condition == "QD4" and row.experiment_id != "EXP055"
    ]
    qd4_rows_without_exp055 = [
        row for row in rows if row.condition == "QD4" and row.experiment_id != "EXP055"
    ]
    first_four_diffs = [value for block, value in diffs if block != 5]
    exp055_iops = next(row.iops for row in rows if row.experiment_id == "EXP055")
    qd4_latency_without_exp055 = statistics.mean(
        row.mean_total_latency_us for row in qd4_rows_without_exp055
    )
    qd8_latency_all = statistics.mean(
        row.mean_total_latency_us for row in rows if row.condition == "QD8"
    )
    sensitivity_percentiles = {}
    for field in ("clat_p50_us", "clat_p95_us", "clat_p99_us", "clat_p999_us"):
        available = [getattr(row, field) for row in qd4_rows_without_exp055
                     if getattr(row, field) is not None]
        sensitivity_percentiles[field] = statistics.mean(available) if available else None
    qd8_percentiles = {}
    for field in ("clat_p50_us", "clat_p95_us", "clat_p99_us", "clat_p999_us"):
        available = [getattr(row, field) for row in rows
                     if row.condition == "QD8" and getattr(row, field) is not None]
        qd8_percentiles[field] = statistics.mean(available) if available else None
    lines += [
        "",
        "## Sensitivity check: EXP055",
        "",
        f"EXP055 is retained in every primary result. Its QD4 IOPS is {exp055_iops:.1f}, versus a mean of {statistics.mean(qd4_without_exp055):.1f} IOPS for the other four QD4 runs. As a descriptive sensitivity check only, the QD4 mean is {statistics.mean(qd4_all):.1f} IOPS with all five observations and {statistics.mean(qd4_without_exp055):.1f} without EXP055. The mean paired difference is {diff_summary['mean']:+.1f} IOPS across all five blocks and {statistics.mean(first_four_diffs):+.1f} across Blocks 1–4.",
        f"EXP055 also has a high latency tail (clat p95/p99/p99.9: {fmt(next(row.clat_p95_us for row in rows if row.experiment_id == 'EXP055'))}/{fmt(next(row.clat_p99_us for row in rows if row.experiment_id == 'EXP055'))}/{fmt(next(row.clat_p999_us for row in rows if row.experiment_id == 'EXP055'))} µs). Mean QD4 total latency is {statistics.mean(row.mean_total_latency_us for row in rows if row.condition == 'QD4'):.1f} µs with EXP055 and {qd4_latency_without_exp055:.1f} µs without it, compared with {qd8_latency_all:.1f} µs for QD8.",
        "Mean per-run clat percentiles with EXP055 removed from the QD4 sensitivity calculation (not the primary analysis) are "
        f"p50={fmt(sensitivity_percentiles['clat_p50_us'])}, p95={fmt(sensitivity_percentiles['clat_p95_us'])}, "
        f"p99={fmt(sensitivity_percentiles['clat_p99_us'])}, p99.9={fmt(sensitivity_percentiles['clat_p999_us'])} µs; "
        f"the corresponding all-five-run QD8 means are p50={fmt(qd8_percentiles['clat_p50_us'])}, "
        f"p95={fmt(qd8_percentiles['clat_p95_us'])}, p99={fmt(qd8_percentiles['clat_p99_us'])}, "
        f"p99.9={fmt(qd8_percentiles['clat_p999_us'])} µs. This check shows how tail-latency rankings depend on EXP055; it is not grounds to delete or replace that observation.",
        "",
        "## Interpretation and limitations",
        "",
        "The primary paired IOPS differences and latency diagnostics should be interpreted together. A low-throughput or high-latency observation is preserved and investigated, not silently removed. Five blocks are a small descriptive study on one host and one file-based target; the fixed order is counterbalanced but not randomized. These results do not establish population-level effects or generalize to other devices, block sizes, access patterns, or production workloads.",
        "",
        "Protocol v5 used 128 KiB requests while Protocol v6 uses 4 KiB requests. Absolute results across protocols are not a like-for-like comparison because block size changed. Do not infer NAND service time, controller limits, saturation, firmware behavior, thermal throttling, or production readiness from these host-level FIO measurements.",
        "",
        "Do not train a predictive model on these ten runs alone. Treat this as a controlled exploratory comparison and consider the paired pattern, latency tails, FIO versions, achieved-depth distributions, and host state before designing any follow-up experiment.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-report", action="store_true",
        help="Write reports/PROTOCOL_V6_CONFIRMATION_ANALYSIS.md after the audit passes.",
    )
    args = parser.parse_args()
    try:
        rows = load_observations()
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        print("No report was written.", file=sys.stderr)
        return 1

    versions = sorted({row.fio_version for row in rows})
    print("PROTOCOL V6 ARTIFACT AUDIT PASSED")
    print("Validated scheduled runs: 10/10")
    print("FIO version(s): " + ", ".join(versions))
    if len(versions) > 1:
        print("WARNING: FIO versions differ; inspect the report before interpreting paired effects.")
    print()
    print("Experiment Condition Block IOPS Bandwidth(B/s) MeanTotalLat(us) clat_p50 clat_p95 clat_p99 clat_p99.9")
    for row in rows:
        print(
            f"{row.experiment_id} {row.condition} {row.block_id} {row.iops:.1f} "
            f"{row.bandwidth_bps:.0f} {row.mean_total_latency_us:.1f} "
            f"{fmt(row.clat_p50_us)} {fmt(row.clat_p95_us)} {fmt(row.clat_p99_us)} {fmt(row.clat_p999_us)}"
        )
    print()
    for condition in ("QD4", "QD8"):
        group = [row for row in rows if row.condition == condition]
        iops = summarize([row.iops for row in group])
        mean_bw = statistics.mean(row.bandwidth_bps for row in group) / 1_000_000
        mean_lat = statistics.mean(row.mean_total_latency_us for row in group)
        print(
            f"{condition}: mean IOPS={iops['mean']:.1f}; median={iops['median']:.1f}; "
            f"sample SD={iops['sd']:.1f}; CV={iops['cv_pct']:.2f}%; "
            f"mean BW={mean_bw:.2f} MB/s; mean total latency={mean_lat:.1f} us"
        )
    differences = paired_differences(rows)
    print("Paired IOPS differences QD4-QD8: " + ", ".join(f"B{block}={diff:+.1f}" for block, diff in differences))
    print(f"Blocks with QD4 > QD8: {sum(diff > 0 for _, diff in differences)}/5")

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(make_report(rows), encoding="utf-8")
        print(f"\nReport written: {REPORT_PATH.relative_to(REPO_ROOT)}")
    else:
        print("\nNo files were written. Add --write-report to save the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
