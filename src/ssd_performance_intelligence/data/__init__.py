"""Data ingest and FIO parsing utilities.

Submodules
----------
fio_parser
    Safe parsing of FIO 3.42 JSON output.  Never invokes fio.
schema
    Typed, validated dataclasses for normalized FIO job output.
runner
    Dry-run-first experiment runner.  Actual FIO execution requires
    the caller to pass ``execute=True`` explicitly.

Do not download datasets from this package.
"""

from __future__ import annotations

__all__ = [
    "fio_parser",
    "schema",
    "runner",
]
