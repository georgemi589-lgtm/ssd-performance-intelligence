"""Tests for Protocol v6 summary and paired-analysis helpers."""
from __future__ import annotations

from experiments.analyze_protocol_v6 import (
    SCHEDULE,
    Observation,
    make_report,
    paired_differences,
    summarize,
)


def make_observation(
    experiment_id: str,
    condition: str,
    block: int,
    iops: float,
) -> Observation:
    return Observation(
        experiment_id=experiment_id,
        run_order=int(experiment_id[-3:]) - 46,
        condition=condition,
        replicate=block,
        block_id=block,
        position=1 if condition == "QD4" else 2,
        iops=iops,
        bandwidth_bps=iops * 4096,
        mean_total_latency_us=100.0,
        clat_mean_us=90.0,
        slat_mean_us=10.0,
        clat_p50_us=80.0,
        clat_p95_us=150.0,
        clat_p99_us=200.0,
        clat_p999_us=300.0,
        iodepth_level={},
        fio_version="test",
        power_state="AC",
        background_activity="idle",
        system_update_state="none observed",
        cpu_count="8",
        target_free_bytes="1000",
    )


def test_summary_reports_sample_standard_deviation_and_cv() -> None:
    result = summarize([10.0, 20.0, 30.0])
    assert result["n"] == 3
    assert result["mean"] == 20.0
    assert result["median"] == 20.0
    assert result["sd"] == 10.0
    assert result["cv_pct"] == 50.0


def test_paired_differences_are_qd4_minus_qd8_in_block_order() -> None:
    rows = []
    for block, qd4, qd8 in (
        (1, 90.0, 100.0),
        (2, 110.0, 100.0),
        (3, 95.0, 95.0),
        (4, 80.0, 120.0),
        (5, 105.0, 100.0),
    ):
        qd4_id, qd8_id = {
            1: ("EXP048", "EXP047"),
            2: ("EXP049", "EXP050"),
            3: ("EXP051", "EXP052"),
            4: ("EXP054", "EXP053"),
            5: ("EXP055", "EXP056"),
        }[block]
        rows.append(make_observation(qd4_id, "QD4", block, qd4))
        rows.append(make_observation(qd8_id, "QD8", block, qd8))
    assert paired_differences(rows) == [
        (1, -10.0), (2, 10.0), (3, 0.0), (4, -40.0), (5, 5.0)
    ]


def test_schedule_contains_ten_prespecified_runs_in_five_pairs() -> None:
    assert list(SCHEDULE) == list(range(47, 57))
    assert SCHEDULE[47] == ("QD8", 1, 1, 1)
    assert SCHEDULE[48] == ("QD4", 1, 1, 2)
    assert SCHEDULE[55] == ("QD4", 5, 5, 1)
    assert SCHEDULE[56] == ("QD8", 5, 5, 2)


def test_report_highlights_findings_depth_histogram_and_latency_sensitivity() -> None:
    rows = []
    for block, qd4, qd8 in (
        (1, 90.0, 100.0),
        (2, 110.0, 120.0),
        (3, 95.0, 105.0),
        (4, 80.0, 115.0),
        (5, 50.0, 125.0),
    ):
        qd4_id, qd8_id = {
            1: ("EXP048", "EXP047"),
            2: ("EXP049", "EXP050"),
            3: ("EXP051", "EXP052"),
            4: ("EXP054", "EXP053"),
            5: ("EXP055", "EXP056"),
        }[block]
        rows.append(make_observation(qd4_id, "QD4", block, qd4))
        rows.append(make_observation(qd8_id, "QD8", block, qd8))

    report = make_report(rows)
    assert "Findings at a glance" in report
    assert "requested iodepth settings" in report
    assert "Sensitivity check: EXP055" in report
    assert "high latency tail" in report
