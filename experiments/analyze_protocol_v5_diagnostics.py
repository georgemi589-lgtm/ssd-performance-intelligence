"""Inspect Protocol v5 latency percentiles and achieved queue-depth distributions.

Run from the repository root:
    python experiments/analyze_protocol_v5_diagnostics.py

The script validates the same ten scheduled artifacts used by
analyze_protocol_v5.py, then reports per-run completion-latency percentiles,
submission/total latency, achieved iodepth histograms, and recorded host state.
It is strictly read-only.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

# When launched as "python experiments/<script>.py", Python places the
# experiments directory—not necessarily the repository root—at sys.path[0].
# Add the repository root so imports between local project scripts resolve
# consistently from PowerShell and other working directories.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.analyze_protocol_v5 import RAW_DIR, SCHEDULE, load_observations
from ssd_performance_intelligence.data.fio_parser import parse_fio_file

REPORT_PATH = REPO_ROOT / "reports" / "PROTOCOL_V5_LATENCY_DIAGNOSTICS.md"

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


def build_markdown_report(rows: list[dict]) -> str:
    versions = sorted({str(row["fio"]) for row in rows})
    lines = [
        "# Protocol v5 — Latency and Achieved Queue-Depth Diagnostics",
        "",
        "## Provenance and audit",
        "",
        "This report is generated from the ten local Protocol v5 raw FIO JSON artifacts after the shared Protocol v5 audit passed. The script checks configuration, metadata, the FIO job schema, requested queue depth, and that the read-only job does not report write I/O.",
        "",
        f"- Scheduled runs validated: {len(rows)}/10",
        f"- FIO versions: {', '.join(versions)}",
        "- All runs in this study should use the same FIO version for direct within-study comparison.",
        "",
        "## Per-run latency details",
        "",
        "Completion latency (clat) percentiles are FIO per-run values. They are not pooled request-level percentiles. Submission latency (slat), completion latency (clat), and total latency (lat) are distinct measurements.",
        "",
        "| Experiment | Block | Condition | IOPS | clat p50 (us) | clat p95 (us) | clat p99 (us) | clat p99.9 (us) | mean slat (us) | mean clat (us) | mean total lat (us) |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['block']} | {row['condition']} | {row['iops']:.1f} | "
            f"{fmt(row['clat_p50_us'])} | {fmt(row['clat_p95_us'])} | {fmt(row['clat_p99_us'])} | "
            f"{fmt(row['clat_p999_us'])} | {fmt(row['mean_slat_us'])} | {fmt(row['mean_clat_us'])} | "
            f"{fmt(row['mean_total_lat_us'])} |"
        )

    lines += [
        "",
        "## Condition-level diagnostic summaries",
        "",
        "These are arithmetic means of five per-run summaries. The averages of p50/p95/p99/p99.9 values are not the percentile distribution of all requests pooled together.",
        "",
        "| Condition | Mean IOPS | Mean BW (MB/s) | Mean slat (us) | Mean clat (us) | Mean total lat (us) | Mean per-run clat p50 (us) | Mean per-run clat p95 (us) | Mean per-run clat p99 (us) | Mean per-run clat p99.9 (us) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in ("QD4", "QD8"):
        group = [row for row in rows if row["condition"] == condition]
        def avg(key: str) -> float | None:
            values = [row[key] for row in group if row[key] is not None]
            return statistics.mean(values) if values else None
        lines.append(
            f"| {condition} | {avg('iops'):.1f} | {avg('bandwidth_bps')/1_000_000:.2f} | "
            f"{fmt(avg('mean_slat_us'))} | {fmt(avg('mean_clat_us'))} | {fmt(avg('mean_total_lat_us'))} | "
            f"{fmt(avg('clat_p50_us'))} | {fmt(avg('clat_p95_us'))} | {fmt(avg('clat_p99_us'))} | {fmt(avg('clat_p999_us'))} |"
        )

    lines += [
        "",
        "## Achieved queue-depth distribution",
        "",
        "FIO iodepth_level values are percentages in FIO's depth buckets; they are not percentages of wall-clock time. Compare these with the configured depth, but do not assume the requested queue depth was achieved for every I/O.",
        "",
        "| Experiment | Condition | Requested depth | Depth bucket 2 (%) | Depth bucket 4 (%) | Depth bucket 8 (%) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        hist = row.get("iodepth_level") or {}
        requested = 4 if row["condition"] == "QD4" else 8
        lines.append(
            f"| {row['id']} | {row['condition']} | {requested} | "
            f"{hist.get('2', 0.0):.3f} | {hist.get('4', 0.0):.3f} | {hist.get('8', 0.0):.3f} |"
        )

    lines += [
        "",
        "## Recorded host state",
        "",
        "| Experiment | Power state | Background activity | System-update state | CPU count | Free bytes before run |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['power_state']} | {row['background_activity']} | "
            f"{row['system_update_state']} | {row['cpu_count']} | {row['target_free_bytes']} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "1. Throughput is very similar between conditions in Protocol v5, but the mean IOPS difference is small relative to the larger run-to-run variation observed in QD8. Do not claim a reliable throughput advantage for either condition from these five pairs.",
        "2. Mean submission latency is similar between conditions, while mean completion latency is substantially higher at QD8. The measured latency difference is chiefly in FIO's completion-latency component, not the submission-latency component. This does not identify an SSD-internal or operating-system mechanism.",
        "3. QD8's per-run p50, p95, p99, and p99.9 completion-latency values exceed QD4's in every paired block in this dataset. QD8's upper tail is particularly high in EXP046; preserve and investigate this result rather than excluding it.",
        "4. The achieved-depth histograms reflect the configured conditions: QD4 runs mostly occupy the depth-4 bucket, while QD8 runs mostly occupy the depth-8 bucket. Non-zero shares in adjacent buckets are not, by themselves, evidence of a failed configuration.",
        "5. Power/background/update labels and CPU count are stable across the runs. Minor wording differences in update-state metadata should be normalized for future conventions, not silently rewritten in historical records.",
        "",
        "## Limitations and next decision",
        "",
        "This is five pairs on one host and one file-based sequential-read workload. FIO latency metrics reflect the storage path observable by FIO; they do not isolate physical NAND service time or controller behavior. Averages of per-run percentile values are descriptive and are not pooled request-level percentiles.",
        "",
        "No additional QD4/QD8 runs are recommended immediately. Preserve these results and finalize the primary Protocol v5 report with the latency diagnostics. A next study should be designed only after defining a new question, such as whether this latency trade-off generalizes to a different read-only block size or access pattern. Do not claim generalization from this host alone.",
        "",
    ]
    return "\\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write reports/PROTOCOL_V5_LATENCY_DIAGNOSTICS.md after the audit passes.",
    )
    args = parser.parse_args()

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
        metadata_path = RAW_DIR / f"{experiment_id.lower()}.metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        host_state = metadata.get("host_state", {})
        host_snapshot = metadata.get("host_snapshot", {})
        row = {
            "id": experiment_id,
            "condition": expected[0],
            "block": expected[2],
            "position": expected[3],
            "iops": observed_by_id[experiment_id].iops,
            "bandwidth_bps": observed_by_id[experiment_id].bandwidth_bps,
            "fio": parsed.fio_version or "unknown",
            "clat_p50_us": completion.p50_us,
            "clat_p95_us": completion.p95_us,
            "clat_p99_us": completion.p99_us,
            "clat_p999_us": completion.p999_us,
            "mean_slat_us": submission.mean_us,
            "mean_clat_us": completion.mean_us,
            "mean_total_lat_us": total.mean_us,
            "iodepth_level": job.iodepth.level_percent,
            "power_state": host_state.get("power_state", ""),
            "background_activity": host_state.get("background_activity", ""),
            "system_update_state": host_state.get("system_update_state", ""),
            "cpu_count": host_snapshot.get("cpu_count", ""),
            "target_free_bytes": host_snapshot.get("target_volume_free_bytes_before_run", ""),
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

    if args.write_report:
        report = build_markdown_report(diagnostic_rows)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"\\nReport written: {REPORT_PATH.relative_to(REPO_ROOT)}")
    else:
        print()
        print("No files were written. Add --write-report to save the diagnostics report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
