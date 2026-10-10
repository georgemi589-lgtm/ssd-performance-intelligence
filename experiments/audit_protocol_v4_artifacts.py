"""Audit locally preserved artifacts for Protocol v4 experiments EXP025-EXP036.

Run from the repository root:
    python experiments/audit_protocol_v4_artifacts.py

This script is read-only. It does not modify the raw JSON, metadata sidecars,
or observations ledger.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
LEDGER_PATH = REPO_ROOT / "data" / "analysis" / "observations.csv"
EXPERIMENT_IDS = [f"EXP{number:03d}" for number in range(25, 37)]


def main() -> int:
    issues: list[str] = []

    if not LEDGER_PATH.is_file():
        print(f"[FAIL] Missing observations ledger: {LEDGER_PATH}")
        return 1

    with LEDGER_PATH.open("r", newline="", encoding="utf-8-sig") as handle:
        ledger_rows = {
            row.get("experiment_id", ""): row
            for row in csv.DictReader(handle)
        }

    for experiment_id in EXPERIMENT_IDS:
        stem = experiment_id.lower()
        raw_path = RAW_DIR / f"{stem}.json"
        metadata_path = RAW_DIR / f"{stem}.metadata.json"
        run_issues: list[str] = []

        if not raw_path.is_file():
            run_issues.append(f"missing raw JSON ({raw_path.name})")
        else:
            try:
                with raw_path.open("r", encoding="utf-8") as handle:
                    raw_payload = json.load(handle)
                if not isinstance(raw_payload, dict):
                    run_issues.append("raw JSON top-level value is not an object")
                elif not isinstance(raw_payload.get("jobs"), list) or not raw_payload["jobs"]:
                    run_issues.append("raw JSON does not contain a non-empty jobs list")
            except (OSError, json.JSONDecodeError) as exc:
                run_issues.append(f"raw JSON cannot be parsed ({exc})")

        if not metadata_path.is_file():
            run_issues.append(f"missing metadata sidecar ({metadata_path.name})")
        else:
            try:
                with metadata_path.open("r", encoding="utf-8") as handle:
                    metadata = json.load(handle)
                if not isinstance(metadata, dict):
                    run_issues.append("metadata top-level value is not an object")
                else:
                    if metadata.get("experiment_id") != experiment_id:
                        run_issues.append(
                            "metadata experiment_id does not match the artifact name"
                        )
                    protocol = metadata.get("protocol")
                    if not isinstance(protocol, dict) or str(protocol.get("version")) != "4":
                        run_issues.append("metadata protocol version is not 4")
            except (OSError, json.JSONDecodeError) as exc:
                run_issues.append(f"metadata sidecar cannot be parsed ({exc})")

        row = ledger_rows.get(experiment_id)
        if row is None:
            run_issues.append("no matching row in observations.csv")
        elif row.get("raw_artifact_available", "").strip().lower() != "true":
            run_issues.append("ledger raw_artifact_available is not true")

        if run_issues:
            issues.extend(f"{experiment_id}: {issue}" for issue in run_issues)
            print(f"[FAIL] {experiment_id}: " + "; ".join(run_issues))
        else:
            print(f"[OK]   {experiment_id}: raw JSON, metadata, and ledger row verified")

    if issues:
        print(f"\nAUDIT FAILED: {len(issues)} issue(s) found.")
        print("Preserve the artifacts; investigate each issue before analysis.")
        return 1

    print(
        f"\nAUDIT PASSED: all {len(EXPERIMENT_IDS)} scheduled Protocol v4 "
        "experiments have parseable raw JSON, matching Protocol v4 metadata, "
        "and a ledger row."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
