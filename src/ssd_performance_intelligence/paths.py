"""Repository-relative paths for reproducible local research."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = SRC_ROOT.parent

CONFIGS_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
REPORTS_DIR = REPO_ROOT / "reports"


def require_existing(path: Path, *, kind: str = "path") -> Path:
    """Return ``path`` if it exists; otherwise raise a clear error."""
    if not path.exists():
        raise FileNotFoundError(f"Expected {kind} at {path}")
    return path
