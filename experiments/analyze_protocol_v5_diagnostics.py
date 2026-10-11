"""Inspect Protocol v5 latency percentiles and achieved queue-depth distributions.

Run from the repository root:
    python experiments/analyze_protocol_v5_diagnostics.py

The script validates the same ten scheduled artifacts used by
analyze_protocol_v5.py, then reports per-run completion-latency percentiles,
submission/total latency, achieved iodepth histograms, and recorded host state.
It is strictly read-only.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from experiments.analyze_protocol_v5 import RAW_DIR, SCHEDULE, load_observations
from ssd_performance_intelligence.data.fio_parser import parse_fio_file

METRICS = (
    ("clat_p50_us", "p50 completion latency (us)"),
    ("clat_p95_us", "p95 completion latency (us)"),
    ("clat_p99_us", "p99 completion latency (us)"),
    ("clat_p999_us", "p99.9 completion latency (us)"),
    ("mean_slat_us", "mean submission latency (us)"),
    ("mean_clat_us", "mean completion latency (us)"),
    ("mean_total_lat_us", "mean total latency (us)"),
)


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}"


def main() -> int:
    # Reuse the strict config/metadata/raw-artifact audit before diagnostics.
    observations = load_observations()
    observed_by_id = {item.experiment_id: item for item in observations}
    diagnostic_rows: list[dict] = []

    for number, expected in SCHEDULE.items():
        experiment_id = f"EXP{number:03d}"
        parsed = parse_fio_file(RAW_DIR / f"exp{number:03d}.json")
        job = parsed.jobs[0]
        direction = job.read
        total = direction.total_latency
        completion = direction.completion_latency
        submission = direction.submission_latency
        row = {
            "id": experiment_id,
            "condition": expected[0],
            "block": expected[2],
            "iops": observed_by_id[experiment_id].iops,
            "fio": parsed.fio_version or "unknown",
            "clat_p50_us": completion.p50_us,
            "clat_p95_us": completion.p95_us,
            "clat_p99_us": completion.p99_us,
            "clat_p999_us": completion.p999_us,
            "mean_slat_us": submission.mean_us,
            "mean_clat_us": completion.mean_us,
            "mean_total_lat_us": total.mean_us,
            "iodepth_level": job.iodepth.level_percent,
        }
        diagnostic_rows.append(row)

    print("PROTOCOL V5 DIAGNOSTIC AUDIT PASSED")
    print("Latency percentiles below are FIO completion-latency percentiles (clat).")
    print("They are not the same metric as mean total latency (lat) used in the primary table.")
    print()
    headers = [
        "Experiment", "Cond.", "Block", "IOPS", "clat p50", "clat p95",
        "clat p99", "clat p99.9", "mean slat", "mean clat", "mean total lat",
    ]
    print(" | ".join(headers))
    print(" | ".join("---" for _ in headers))
    for row in diagnostic_rows:
        vals = [
            row["id"], row["condition"], str(row["block"]), f'{row["iops"]:.1f}',
            fmt(row["clat_p50_us"]), fmt(row["clat_p95_us"]), fmt(row["clat_p99_us"]),
            fmt(row["clat_p999_us"]), fmt(row["mean_slat_us"]), fmt(row["mean_clat_us"]),
            fmt(row["mean_total_lat_us"]),
        ]
        print(" | ".join(vals))

    print()
    print("ACHIEVED QUEUE-DEPTH DISTRIBUTIONS (FIO iodepth_level percentages)")
    print("The keys are FIO's own depth buckets; do not assume requested depth was fully achieved.")
    for row in diagnostic_rows:
        hist = row["iodepth_level"]
        print(f'{row["id"]} {row["condition"]}: {json.dumps(hist, sort_keys=True) if hist else "not reported"}')

    print()
    print("RECORDED HOST STATE")
    for number, expected in SCHEDULE.items():
        experiment_id = f"EXP{number:03d}"
        metadata_path = RAW_DIR / f"exp{number:03d}.metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        state = metadata.get("host_state", {})
        snap = metadata.get("host_snapshot", {})
        print(
            f'{experiment_id}: power={state.get("power_state")!r}; '
            f'background={state.get("background_activity")!r}; '
            f'updates={state.get("system_update_state")!r}; '
            f'cpu_count={snap.get("cpu_count")!r}; '
            f'target_free_before={snap.get("target_volume_free_bytes_before_run")!r}'
        )

    print()
    print("MEAN OF PER-RUN COMPLETION-LATENCY PERCENTILES BY CONDITION")
    print("These are descriptive averages of five per-run percentile values, not pooled request-level percentiles.")
    for condition in ("QD4", "QD8"):
        group = [row for row in diagnostic_rows if row["condition"] == condition]
        pieces = [condition]
        for key, label in METRICS[:4]:
            values = [row[key] for row in group if row[key] is not None]
            pieces.append(f"{label}={statistics.mean(values):.1f}" if values else f"{label}=n/a")
        print(" | ".join(pieces))

    print()
    print("No files were written. Use these diagnostics to decide whether another experiment is warranted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
