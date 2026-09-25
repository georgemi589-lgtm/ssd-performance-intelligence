"""Run or dry-run a single FIO experiment from a YAML config.

Usage
-----
Dry-run (default — no fio is executed, no files are written):

    python experiments/run_experiment.py --config configs/experiment_template.yaml

Actual execution (requires fio on PATH and an explicit flag):

    python experiments/run_experiment.py \\
        --config configs/experiment_template.yaml \\
        --execute

The script exits with code 0 on success and 1 on any error.  In dry-run mode
it prints the fio command that *would* be run without executing it.

Safety
------
* ``--execute`` must be supplied explicitly; it is never the default.
* The runner rejects block-device targets and destructive job options before
  assembling any command.  See ``src/ssd_performance_intelligence/data/runner.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the package is importable when this script is invoked directly from
# the repo root (the installed editable install already handles this, but the
# guard makes ``python experiments/run_experiment.py`` work without install).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from ssd_performance_intelligence.data.runner import (
    RunnerError,
    SafetyError,
    run_experiment,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_experiment.py",
        description=(
            "Run or dry-run a FIO experiment defined in a YAML config.\n"
            "Dry-run is the default; add --execute to actually invoke fio."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        required=True,
        metavar="CONFIG",
        help=(
            "Experiment config filename (looked up in configs/) "
            "or absolute path to a YAML file."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help=(
            "Actually invoke fio.  Without this flag the command is only "
            "built, validated, and printed (dry-run)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=None,
        help="Override the default output directory for raw JSON artifacts (data/raw/).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        metavar="SECONDS",
        help="Subprocess timeout when --execute is set (default: 120 s).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.execute:
        print("[run_experiment] Mode: EXECUTE — fio will be invoked")
    else:
        print("[run_experiment] Mode: DRY-RUN — fio will NOT be invoked")
        print("                 (Pass --execute to actually run the benchmark)")

    try:
        result = run_experiment(
            args.config,
            execute=args.execute,
            output_dir=output_dir,
            fio_timeout_s=args.timeout,
        )
    except SafetyError as exc:
        print(f"\n[SAFETY ERROR] {exc}", file=sys.stderr)
        print(
            "This experiment was blocked by the project safety contract.  "
            "See docs/research_notes.md.",
            file=sys.stderr,
        )
        return 1
    except RunnerError as exc:
        print(f"\n[RUNNER ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — surface unexpected errors cleanly
        print(f"\n[UNEXPECTED ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    # ---- print summary ---------------------------------------------------
    print(f"\nExperiment : {result['experiment_id']}")
    print(f"Timestamp  : {result['timestamp']}")
    print(f"Dry-run    : {result['dry_run']}")
    print(f"\nFIO command:")
    print(f"  {result['command_string']}")

    if result["dry_run"]:
        print(
            "\nDry-run complete.  No fio process was started; no files were written.\n"
            "To run the benchmark add --execute."
        )
    else:
        out_path = result["output_path"]
        parsed = result["parsed"]
        print(f"\nRaw JSON saved to : {out_path}")
        if parsed is not None:
            print(f"FIO version       : {parsed.fio_version}")
            print(f"Jobs parsed       : {len(parsed.jobs)}")
            for job in parsed.jobs:
                r = job.read
                print(
                    f"  [{job.metadata.jobname}] "
                    f"IOPS={r.iops.iops:.1f}  "
                    f"BW={r.throughput.bw_bytes_per_sec:.0f} B/s  "
                    f"lat_mean={r.total_latency.mean_us:.1f} µs"
                    if r.iops.iops is not None and r.throughput.bw_bytes_per_sec is not None
                    and r.total_latency.mean_us is not None
                    else f"  [{job.metadata.jobname}] (metrics not available)"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
