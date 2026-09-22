"""Load YAML experiment configuration without executing any I/O benchmarks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ssd_performance_intelligence.paths import CONFIGS_DIR, require_existing


def load_config(name: str = "default.yaml") -> dict[str, Any]:
    """Load a YAML file from ``configs/`` by filename or absolute path."""
    path = Path(name)
    if not path.is_absolute():
        path = CONFIGS_DIR / name
    require_existing(path, kind="config file")
    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config {path} must be a mapping, got {type(payload).__name__}")
    return payload
