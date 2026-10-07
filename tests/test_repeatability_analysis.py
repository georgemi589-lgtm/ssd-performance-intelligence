"""Tests for the repeatability analysis helper."""

from pathlib import Path

from experiments.analyze_repeatability import load_rows, render_markdown, stats

def test_stats_two_observations() -> None:
    result = stats([10.0, 20.0])
    assert result["n"] == 2
    assert result["mean"] == 15.0
    assert result["median"] == 15.0
    assert result["stdev"] is not None
    assert result["cv_pct"] is not None

def test_stats_single_observation_has_no_sd() -> None:
    result = stats([10.0])
    assert result["n"] == 1
    assert result["stdev"] is None
    assert result["cv_pct"] is None

def test_repository_observations_render() -> None:
    rows = load_rows(Path("data/analysis/observations.csv"))
    assert len(rows) == 14
    report = render_markdown(rows)
    assert "QD1" in report
    assert "QD2" in report
    assert "Final Protocol v2 dataset" in report
    assert "EXP014" in report

def test_missing_percentiles_are_not_imputed() -> None:
    rows = load_rows(Path("data/analysis/observations.csv"))
    exp003 = next(row for row in rows if row["experiment_id"] == "EXP003")
    assert exp003["p50_clat_us"] == ""
