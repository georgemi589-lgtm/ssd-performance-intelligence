"""Audit and analyze local Protocol v5 QD4/QD8 confirmation artifacts.

From repository root:
    python experiments/analyze_protocol_v5.py
    python experiments/analyze_protocol_v5.py --write-report

This script reads existing files only. It never invokes FIO and never modifies
the observations ledger or raw benchmark artifacts.
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
REPORT_PATH = REPO_ROOT / "reports" / "PROTOCOL_V5_CONFIRMATION_ANALYSIS.md"
TARGET_FILE = r"C:\fio-lab\exp001_testfile.bin"
SCHEDULE_ID = "v5-qd4-qd8-paired-5block-v1"

# experiment number: (condition, replicate, block, position)
SCHEDULE: dict[int, tuple[str, int, int, int]] = {
    37: ("QD8", 1, 1, 1), 38: ("QD4", 1, 1, 2),
    39: ("QD4", 2, 2, 1), 40: ("QD8", 2, 2, 2),
    41: ("QD4", 3, 3, 1), 42: ("QD8", 3, 3, 2),
    43: ("QD8", 4, 4, 1), 44: ("QD4", 4, 4, 2),
    45: ("QD4", 5, 5, 1), 46: ("QD8", 5, 5, 2),
}


class AuditError(RuntimeError):
    """Raised when a Protocol v5 artifact fails validation."""


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
    mean_latency_us: float
    fio_version: str


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
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


def load_observations() -> list[Observation]:
    from ssd_performance_intelligence.data.fio_parser import FioParseError, parse_fio_file

    errors: list[str] = []
    observations: list[Observation] = []

    for number, expected in SCHEDULE.items():
        experiment_id = f"EXP{number:03d}"
        config_path = CONFIG_DIR / f"exp{number:03d}.yaml"
        raw_path = RAW_DIR / f"exp{number:03d}.json"
        metadata_path = RAW_DIR / f"exp{number:03d}.metadata.json"

        try:
            for artifact in (config_path, raw_path, metadata_path):
                if not artifact.is_file():
                    raise AuditError(f"Missing artifact: {artifact.relative_to(REPO_ROOT)}")

            with config_path.open("r", encoding="utf-8") as handle:
                config = yaml.safe_load(handle)
            if not isinstance(config, dict) or config.get("experiment_id") != experiment_id:
                raise AuditError(f"{experiment_id}: invalid config or experiment_id")

            condition, replicate, block, position = expected
            protocol = config.get("protocol")
            if not isinstance(protocol, dict):
                raise AuditError(f"{experiment_id}: protocol block is missing")
            expected_protocol = {
                "version": "5",
                "replicate_index": replicate,
                "run_order": number - 36,
                "block_id": block,
                "within_block_order": position,
                "condition": condition,
                "schedule_id": SCHEDULE_ID,
            }
            for key, value in expected_protocol.items():
                if str(protocol.get(key)) != str(value):
                    raise AuditError(
                        f"{experiment_id}: config protocol.{key}={protocol.get(key)!r}, expected {value!r}"
                    )

            fio = config.get("fio")
            depth = int(condition[2:])
            if not isinstance(fio, dict):
                raise AuditError(f"{experiment_id}: fio block is missing")
            required = {
                "rw": "read", "bs": "128k", "size": "256M", "iodepth": depth,
                "ioengine": "windowsaio", "direct": 1, "runtime": 10, "thread": 1,
            }
            for key, value in required.items():
                if fio.get(key) != value:
                    raise AuditError(
                        f"{experiment_id}: fio.{key}={fio.get(key)!r}, expected {value!r}"
                    )
            normalized_filename = lambda value: str(value).replace("/", "\\").casefold()
            if normalized_filename(fio.get("filename", "")) != normalized_filename(TARGET_FILE):
                raise AuditError(f"{experiment_id}: target file differs from the protocol")

            metadata = read_json(metadata_path)
            if metadata.get("experiment_id") != experiment_id:
                raise AuditError(f"{experiment_id}: metadata experiment_id mismatch")
            metadata_protocol = metadata.get("protocol")
            if not isinstance(metadata_protocol, dict):
                raise AuditError(f"{experiment_id}: metadata protocol is missing")
            for key, value in expected_protocol.items():
                if str(metadata_protocol.get(key)) != str(value):
                    raise AuditError(f"{experiment_id}: metadata protocol.{key} mismatch")
            host_state = metadata.get("host_state")
            if not isinstance(host_state, dict):
                raise AuditError(f"{experiment_id}: metadata host_state is missing")
            for key in ("power_state", "background_activity", "system_update_state"):
                value = host_state.get(key)
                if not isinstance(value, str) or not value.strip() or value.strip().upper().startswith("REPLACE_"):
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
                raise AuditError(f"{experiment_id}: raw JSON includes write I/O in the read-only protocol")

            observations.append(Observation(
                experiment_id=experiment_id,
                run_order=number - 36,
                condition=condition,
                replicate=replicate,
                block_id=block,
                position=position,
                iops=finite_number(job.read.iops.iops, "read IOPS", experiment_id),
                bandwidth_bps=finite_number(job.read.throughput.bw_bytes_per_sec, "read bandwidth", experiment_id),
                mean_latency_us=finite_number(job.read.total_latency.mean_us, "mean total latency", experiment_id),
                fio_version=parsed.fio_version or "unknown",
            ))
        except (AuditError, OSError, ValueError, TypeError) as exc:
            errors.append(str(exc))

    if errors:
        raise AuditError("Protocol v5 artifact audit failed:\n- " + "\n- ".join(errors))
    if len(observations) != 10:
        raise AuditError(f"Expected 10 experiments, found {len(observations)}")
    return observations


def summarize(values: list[float]) -> dict[str, float]:
    average = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "mean": average,
        "median": statistics.median(values),
        "sd": sd,
        "cv": sd / average * 100.0 if average else 0.0,
        "min": min(values),
        "max": max(values),
    }


def make_report(rows: list[Observation]) -> str:
    versions = sorted({row.fio_version for row in rows})
    version_assessment = (
        f"All ten artifacts report {versions[0]}."
        if len(versions) == 1
        else "FIO versions differ across runs: " + ", ".join(versions) +
        ". Version is a potential confound and the paired comparison must be interpreted cautiously."
    )
    lines = [
        "# Protocol v5 — Paired QD4/QD8 Confirmation Analysis",
        "",
        "## Artifact audit",
        "",
        "All ten scheduled configs, raw JSON artifacts, and metadata sidecars passed validation. The repository FIO parser successfully parsed every raw artifact. Each run had one job, a matching job name and requested queue depth, no reported job error, and no write I/O reported.",
        "",
        "FIO versions: " + ", ".join(versions) + ".",
        version_assessment,
        "",
        "## Design and workload",
        "",
        "Five paired blocks compare QD4 with QD8 under a file-based sequential-read workload. The configured workload is 128 KiB block size, 256 MiB test size, 10-second timed run, direct I/O, Windowsaio, and thread=1, using the same test file. The condition order is prespecified and counterbalanced but not randomized.",
        "",
        "## Scheduled observations",
        "",
        "| Run | Experiment | Block | Position | Condition | FIO version | IOPS | Bandwidth (B/s) | Mean latency (µs) |",
        "|---:|---|---:|---:|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.run_order} | {row.experiment_id} | {row.block_id} | {row.position} | "
            f"{row.condition} | {row.fio_version} | {row.iops:.1f} | "
            f"{row.bandwidth_bps:.0f} | {row.mean_latency_us:.1f} |"
        )

    lines += [
        "",
        "## Condition-level descriptive statistics",
        "",
        "| Condition | n | Mean IOPS | Median IOPS | Sample SD IOPS | IOPS CV | Mean bandwidth (MB/s) | Mean latency (µs) | Latency CV |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in ("QD4", "QD8"):
        group = [row for row in rows if row.condition == condition]
        iops = summarize([row.iops for row in group])
        bandwidth = summarize([row.bandwidth_bps for row in group])
        latency = summarize([row.mean_latency_us for row in group])
        lines.append(
            f"| {condition} | {len(group)} | {iops['mean']:.1f} | {iops['median']:.1f} | "
            f"{iops['sd']:.1f} | {iops['cv']:.2f}% | {bandwidth['mean']/1_000_000:.2f} | "
            f"{latency['mean']:.1f} | {latency['cv']:.2f}% |"
        )

    paired: list[float] = []
    lines += [
        "",
        "## Paired comparison",
        "",
        "Primary outcome: D = IOPS(QD4) − IOPS(QD8). Positive values favor QD4; negative values favor QD8.",
        "",
        "| Block | QD4 experiment | QD4 IOPS | QD8 experiment | QD8 IOPS | D (QD4−QD8) | D relative to QD8 |",
        "|---:|---|---:|---|---:|---:|---:|",
    ]
    for block in range(1, 6):
        group = {row.condition: row for row in rows if row.block_id == block}
        if set(group) != {"QD4", "QD8"}:
            raise AuditError(f"Block {block} does not have exactly one QD4 and one QD8 run")
        qd4, qd8 = group["QD4"], group["QD8"]
        diff = qd4.iops - qd8.iops
        paired.append(diff)
        relative = diff / qd8.iops * 100.0 if qd8.iops else float("nan")
        lines.append(
            f"| {block} | {qd4.experiment_id} | {qd4.iops:.1f} | {qd8.experiment_id} | "
            f"{qd8.iops:.1f} | {diff:+.1f} | {relative:+.2f}% |"
        )
    pair_stats = summarize(paired)
    lines += [
        "",
        f"- Mean paired difference: **{pair_stats['mean']:+.1f} IOPS**.",
        f"- Median paired difference: **{pair_stats['median']:+.1f} IOPS**.",
        f"- Sample SD of paired differences: **{pair_stats['sd']:.1f} IOPS**.",
        f"- Blocks with QD4 higher than QD8: **{sum(value > 0 for value in paired)}/5**.",
        "",
        "## Interpretation and limitations",
        "",
        "These are descriptive results from one host and one file-based sequential-read workload. Five pairs are a small confirmation study, not population-level proof. The paired design helps compare nearby runs but cannot remove all time-varying host-state or environmental effects.",
        "",
        "Do not attribute the observed differences to NAND, controller behavior, firmware, saturation, thermal throttling, or production performance without direct evidence for those mechanisms.",
        "",
        "Two accidental duplicate commands occurred after the scheduled EXP034 artifact was saved during Protocol v4. Their unsaved results are excluded from the v4 ledger, but the extra reads may have affected the host state before subsequent v4 runs. This limitation remains documented in the v4 report.",
        "",
        "## Decision",
        "",
        "Use the paired direction, condition variability, latency, artifact metadata, and FIO version consistency to decide whether the Protocol v4 pattern was reproduced. If the paired direction is mixed or variability remains high, classify the result as inconclusive and gather further controlled observations. Do not train a predictive model from this small study alone.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true", help="Write the audited report to reports/PROTOCOL_V5_CONFIRMATION_ANALYSIS.md")
    args = parser.parse_args()

    try:
        rows = load_observations()
    except AuditError as exc:
        print(str(exc), file=sys.stderr)
        print("No report was written.", file=sys.stderr)
        return 1

    versions = sorted({row.fio_version for row in rows})
    print("PROTOCOL V5 ARTIFACT AUDIT PASSED")
    print("Validated scheduled runs: 10/10")
    print("FIO version(s): " + ", ".join(versions))
    if len(versions) > 1:
        print("WARNING: FIO version differs across runs; inspect the report before interpreting paired effects.")
    print()
    print("Experiment  Condition  Block   IOPS       Bandwidth (B/s)  Mean latency (us)  FIO")
    for row in rows:
        print(
            f"{row.experiment_id:<11} {row.condition:<10} {row.block_id:<5} "
            f"{row.iops:>8.1f} {row.bandwidth_bps:>17.0f} {row.mean_latency_us:>18.1f}  {row.fio_version}"
        )

    for condition in ("QD4", "QD8"):
        summary = summarize([row.iops for row in rows if row.condition == condition])
        print(
            f"{condition}: mean IOPS={summary['mean']:.1f}, sample SD={summary['sd']:.1f}, "
            f"CV={summary['cv']:.2f}%"
        )
    paired = []
    for block in range(1, 6):
        group = {row.condition: row for row in rows if row.block_id == block}
        paired.append(group["QD4"].iops - group["QD8"].iops)
    print("Paired IOPS differences QD4-QD8: " + ", ".join(f"{value:+.1f}" for value in paired))
    print(f"Blocks with QD4 > QD8: {sum(value > 0 for value in paired)}/5")

    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(make_report(rows), encoding="utf-8")
        print(f"\nReport written: {REPORT_PATH.relative_to(REPO_ROOT)}")
    else:
        print("\nNo files were written. Add --write-report after reviewing this audit and summary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
