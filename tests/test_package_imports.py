"""Tests that the installable package layout imports cleanly."""

from __future__ import annotations

import importlib

import ssd_performance_intelligence
from ssd_performance_intelligence.config import load_config
from ssd_performance_intelligence.paths import CONFIGS_DIR, REPO_ROOT


SUBPACKAGES = (
    "ssd_performance_intelligence.data",
    "ssd_performance_intelligence.features",
    "ssd_performance_intelligence.models",
    "ssd_performance_intelligence.evaluation",
    "ssd_performance_intelligence.inference",
)


def test_package_version_is_defined() -> None:
    assert ssd_performance_intelligence.__version__ == "0.1.0"


def test_research_subpackages_import() -> None:
    for name in SUBPACKAGES:
        module = importlib.import_module(name)
        assert module.__name__ == name


def test_default_config_loads() -> None:
    config = load_config("default.yaml")
    assert config["project"]["name"] == "ssd-performance-intelligence"
    assert config["safety"]["allow_destructive_benchmarks"] is False
    assert config["models"]["enabled"] is False
    assert (CONFIGS_DIR / "default.yaml").is_file()
    assert (REPO_ROOT / "pyproject.toml").is_file()
