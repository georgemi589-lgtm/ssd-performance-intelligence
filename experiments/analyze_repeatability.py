"""Descriptive repeatability analysis for documented benchmark observations.

This script works on a small CSV of documented observations rather than pretending
overwritten raw FIO artifacts still exist. It computes descriptive statistics only;
it does not perform population-level inference or causal testing.
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
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "stdev": None,
            "cv_pct": None,
            "min": None,
            "max": None,
        }
    avg = mean(values)
    sd = stdev(values) if len(values) >= 2 else None
    cv = (sd / avg * 100.0) if sd is not None and avg != 0 else None
    return {
        "n": len(values),
        "mean": avg,
        "median": median(values),
        "stdev": sd,
        "cv_pct": cv,
        "min": min(values),
        "max": max(values),
    }


def render_markdown(rows: list[dict[str, str]]) -> str:
    conditions = sorted({row["condition"] for row in rows})
    lines = [
        "# SSD benchmark repeatability analysis",
        "",
        "Descriptive inventory of sequential-read observations across legacy and Protocol v2-v4 runs. Because these observations use different protocols and run designs, pooled condition summaries are not protocol-specific estimates and must not be used to infer a queue-depth effect. This report does not estimate population parameters or establish causality.",
        "",
        "## Observation provenance",
        "",
        "| Experiment | Condition | Source | Raw artifact available |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['experiment_id']} | {row['condition']} | "
            f"{row['source_type']} | {row['raw_artifact_available']} |"
        )

    for metric, label in METRICS.items():
        lines += [
            "",
            f"## {label}",
            "",
            "| Condition | n | Mean | Median | Sample SD | CV | Min | Max |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        grouped = grouped_values(rows, metric)
        for condition in conditions:
            s = stats(grouped.get(condition, []))

            def fmt(x: object) -> str:
                if x is None:
                    return "—"
                return f"{x:.3f}" if isinstance(x, float) else str(x)

            lines.append(
                f"| {condition} | {s['n']} | {fmt(s['mean'])} | "
                f"{fmt(s['median'])} | {fmt(s['stdev'])} | "
                f"{fmt(s['cv_pct'])}% | {fmt(s['min'])} | {fmt(s['max'])} |"
            )

    lines += [
        "",
        "## Current interpretation",
        "",
        "- These observations are descriptive measurements from this host under the documented protocol.",
        "- The ledger now includes QD1, QD2, QD4, and QD8 observations from different protocols; pooled values mix protocol designs and are an inventory summary only.
- Use protocol-specific reports for queue-depth comparisons. The Protocol v4 report contains the dedicated QD1/QD2/QD4/QD8 screening analysis.",
        "- No population-level inference, causal claim, or production-readiness conclusion is drawn.",
        "",
        "## Missing values",
        "",
        "- Missing latency percentiles remain blank when they are not available in the retained source record; no values are imputed.",
        "",
        "## Next decision",
        "",
        "Audit local raw JSON and metadata sidecars, then pursue the planned QD4-versus-QD8 confirmation. Do not build predictive models from this screening ledger alone.",
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
