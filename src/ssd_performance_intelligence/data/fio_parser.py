"""Safe parsing of FIO JSON output (targets FIO 3.42's ``--output-format=json``).

This module only reads text or files that already exist; it never invokes
``fio`` and never writes anything. Execution lives in
``ssd_performance_intelligence.data.runner``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ssd_performance_intelligence.data.schema import FioSchemaError, ParsedFioOutput


class FioParseError(ValueError):
    """Raised when FIO output text cannot be safely parsed as FIO JSON."""


def _split_leading_non_json(text: str) -> tuple[str | None, str]:
    """Split off any warning/log text FIO prints before the JSON body.

    FIO sometimes prints a plain-text line before its JSON payload (for
    example, the Windows "this platform does not support process shared
    mutexes" notice seen in ``data/raw/exp001.json``). This finds the
    first ``{`` in the text and treats everything before it as a separate,
    non-JSON preamble rather than trying to parse it as JSON.
    """
    start = text.find("{")
    if start == -1:
        raise FioParseError("No JSON object found in FIO output text")
    preamble = text[:start].strip()
    body = text[start:]
    return (preamble or None), body


def parse_fio_json_text(text: str) -> tuple[dict, str | None]:
    """Safely parse raw FIO output text into ``(json_dict, leading_text)``.

    Raises :class:`FioParseError` on malformed input. Never executes fio.
    """
    if not isinstance(text, str):
        raise FioParseError(f"Expected str input, got {type(text).__name__}")
    preamble, body = _split_leading_non_json(text)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise FioParseError(f"FIO output is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise FioParseError(f"Top-level FIO JSON must be an object, got {type(payload).__name__}")
    return payload, preamble


def parse_fio_output(text: str) -> ParsedFioOutput:
    """Parse FIO JSON text into a normalized, validated :class:`ParsedFioOutput`.

    The raw JSON payload is preserved unmodified on the result's ``.raw``
    attribute; every other field is derived, typed, and validated.
    """
    payload, preamble = parse_fio_json_text(text)
    try:
        return ParsedFioOutput.from_raw(payload, leading_non_json_text=preamble)
    except FioSchemaError as exc:
        raise FioParseError(str(exc)) from exc


def parse_fio_file(path: str | Path) -> ParsedFioOutput:
    """Read a FIO JSON artifact from disk and parse it.

    Only reads the given path; never invokes fio and never writes to disk.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FioParseError(f"FIO output file not found: {file_path}")
    text = file_path.read_text(encoding="utf-8")
    return parse_fio_output(text)
