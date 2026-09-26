"""Descriptive repeatability analysis for documented benchmark observations.

This script works on a small CSV of documented observations rather than pretending
overwritten raw FIO artifacts still exist. It computes descriptive statistics only;
with two observations per condition it does not perform inference.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean, median, stdev

DEFAULT_INPUT = Path("data/analysis/observations.csv")
METRICS = {
    "iops": "IOPS",
    "bw_bytes_per_sec": "Bandwidth (B/s)",
    "mean_total_latency_us": "Mean total latency (µs)",
}

def _float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)

def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"No observations found in {path}")
    return rows

def grouped_values(rows: list[dict[str, str]], metric: str) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        value = _float_or_none(row.get(metric))
        if value is None:
            continue
        grouped.setdefault(row["condition"], []).append(value)
    return grouped

def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "stdev": None, "cv_pct": None, "min": None, "max": None}
    avg = mean(values)
    sd = stdev(values) if len(values) >= 2 else None
    cv = (sd / avg * 100.0) if sd is not None and avg != 0 else None
    return {"n": len(values), "mean": avg, "median": median(values), "stdev": sd, "cv_pct": cv, "min": min(values), "max": max(values)}

def render_markdown(rows: list[dict[str, str]]) -> str:
    conditions = sorted({row["condition"] for row in rows})
    lines = [
        "# QD1/QD2 repeatability analysis",
        "",
        "Descriptive analysis of the documented sequential-read observations. This does not estimate population parameters or establish causality.",
        "",
        "## Observation provenance",
        "",
        "| Experiment | Condition | Source | Raw artifact available |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row["experiment_id"]} | {row["condition"]} | {row["source_type"]} | {row["raw_artifact_available"]} |")
    for metric, label in METRICS.items():
        lines += ["", f"## {label}", "", "| Condition | n | Mean | Median | Sample SD | CV | Min | Max |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        grouped = grouped_values(rows, metric)
        for condition in conditions:
            s = stats(grouped.get(condition, []))
            def fmt(x: object) -> str:
                if x is None:
                    return "—"
                return f"{x:.3f}" if isinstance(x, float) else str(x)
            lines.append(f"| {condition} | {s["n"]} | {fmt(s["mean"])} | {fmt(s["median"])} | {fmt(s["stdev"])} | {fmt(s["cv_pct"])}% | {fmt(s["min"])} | {fmt(s["max"])} |")
    lines += [
        "",
        "## Current interpretation",
        "",
        "- The two QD1 observations differ substantially, while the two QD2 observations are much closer.",
        "- Run-to-run variability is large enough to confound a one-run QD1-versus-QD2 comparison on this host.",
        "- The current data are not sufficient to attribute observed differences to queue depth alone.",
        "- Missing latency percentiles for EXP003/EXP004 are left blank; no values are imputed.",
        "",
        "## Next decision",
        "",
        "Tighten the baseline protocol and collect multiple repeats per condition before expanding to QD4/QD8.",
    ]
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze documented SSD benchmark observations.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=None, help="Optional Markdown output path.")
    args = parser.parse_args()
    rows = load_rows(Path(args.input))
    report = render_markdown(rows)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
