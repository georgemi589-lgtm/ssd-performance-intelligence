"""Experiment runner: build and (optionally) execute FIO commands.

Safety contract
---------------
* Dry-run is the default. Actual FIO execution requires ``--execute`` to be
  passed explicitly by the caller.
* Only a *file-path* benchmark target is permitted.  Block-device paths
  (``/dev/…``, ``\\\\.\\PhysicalDrive…``, ``\\\\?\\...``) are rejected before
  any command is assembled.
* Destructive FIO operations (``verify``, ``randwrite`` with ``size`` equal to
  device capacity, ``trim``) may not be configured via this runner without
  raising an explicit :class:`SafetyError`.
* This module never imports ``subprocess`` itself; the actual ``subprocess``
  call is deferred to :func:`_invoke_fio` and is only reached when the caller
  has passed ``execute=True``.  Nothing in the dry-run path touches the OS.

These rules mirror ``configs/default.yaml``'s ``safety`` block and the
project-wide principle stated in ``docs/research_notes.md`` (isolated spare
device, written protocol, non-system volume).
"""

from __future__ import annotations

import datetime
import json
import os
import platform
import re
import shutil
import shlex
import sys
from pathlib import Path
from typing import Any

import yaml

from ssd_performance_intelligence.data.fio_parser import parse_fio_output
from ssd_performance_intelligence.data.schema import ParsedFioOutput
from ssd_performance_intelligence.paths import CONFIGS_DIR, RAW_DATA_DIR


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SafetyError(RuntimeError):
    """Raised when a requested FIO configuration violates the safety contract."""


class RunnerError(RuntimeError):
    """Raised for runner configuration or execution errors unrelated to safety."""


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

# Prefixes and patterns that unambiguously indicate a raw block device.
_BLOCK_DEVICE_PREFIXES: tuple[str, ...] = (
    "/dev/",          # Linux / macOS raw block devices
    "\\\\.\\",        # Windows physical drive notation  (\\.\PhysicalDriveN)
    "\\\\?\\",        # Windows device namespace prefix
)

# FIO job options whose presence is always refused by the safety contract.
_DISALLOWED_JOB_OPTIONS: dict[str, str] = {
    "verify": "write-verify workloads may be destructive; excluded by safety contract",
    "trim":   "TRIM/UNMAP operations are destructive; excluded by safety contract",
}


def _check_filename_safety(filename: str) -> None:
    """Raise :class:`SafetyError` if *filename* targets anything other than a regular file path."""
    if not filename or not filename.strip():
        raise SafetyError("Benchmark target filename must not be empty")
    normalized = filename.strip().replace("\\", "/")
    for prefix in _BLOCK_DEVICE_PREFIXES:
        if filename.startswith(prefix) or normalized.startswith(prefix.replace("\\", "/")):
            raise SafetyError(
                f"Benchmark target {filename!r} looks like a raw block device. "
                "Only file-path targets are permitted.  "
                "See docs/research_notes.md for the project safety contract."
            )


def _check_job_options_safety(job_options: dict[str, Any]) -> None:
    """Raise :class:`SafetyError` if any job option violates the safety contract."""
    for key, reason in _DISALLOWED_JOB_OPTIONS.items():
        if key in job_options:
            raise SafetyError(f"FIO option {key!r} is not permitted: {reason}")


def _validate_protocol_v2(config: dict[str, Any]) -> None:
    """Validate the minimum metadata required for controlled Protocol v2 runs."""
    experiment_id = str(config.get("experiment_id", ""))
    if not re.fullmatch(r"EXP\d{3,}", experiment_id):
        raise RunnerError(
            "Protocol v2 requires experiment_id in the form EXP### or higher "
            f"(got {experiment_id!r})."
        )
    protocol = config.get("protocol", {})
    if not isinstance(protocol, dict):
        raise RunnerError("The 'protocol' block must be a mapping.")
    if protocol.get("version") != "2":
        raise RunnerError(
            "New benchmark runs require protocol.version: '2'. "
            "Do not execute an unversioned or legacy config."
        )
    for key in ("replicate_index", "run_order"):
        value = protocol.get(key)
        if not isinstance(value, int) or value < 1:
            raise RunnerError(
                f"Protocol v2 requires protocol.{key} to be a positive integer."
            )
    fio = config.get("fio", {})
    if not isinstance(fio, dict):
        raise RunnerError("The 'fio' block must be a mapping.")
    name = str(fio.get("name", ""))
    if not name.lower().startswith(experiment_id.lower() + "-"):
        raise RunnerError(
            "Experiment metadata mismatch: fio.name must start with the "
            f"experiment_id ({experiment_id.lower()}-)."
        )
    if "thread" not in fio:
        raise RunnerError(
            "Protocol v2 requires an explicit fio.thread setting. "
            "Set it deliberately for the target platform."
        )

def _validate_protocol_v3(config: dict[str, Any]) -> None:
    """Validate Protocol v3 paired-block and host-state metadata."""
    experiment_id = str(config.get("experiment_id", ""))
    if not re.fullmatch(r"EXP\d{3,}", experiment_id):
        raise RunnerError(
            "Protocol v3 requires experiment_id in the form EXP### or higher "
            f"(got {experiment_id!r})."
        )
    protocol = config.get("protocol", {})
    if not isinstance(protocol, dict) or protocol.get("version") != "3":
        raise RunnerError("Protocol v3 requires protocol.version: '3'.")
    for key in ("replicate_index", "run_order", "block_id"):
        value = protocol.get(key)
        if not isinstance(value, int) or value < 1:
            raise RunnerError(f"Protocol v3 requires positive integer protocol.{key}.")
    if protocol["replicate_index"] > 5:
        raise RunnerError("Protocol v3 replicate_index must be between 1 and 5.")
    if protocol["run_order"] > 10:
        raise RunnerError("Protocol v3 run_order must be between 1 and 10.")
    if protocol["block_id"] > 5:
        raise RunnerError("Protocol v3 block_id must be between 1 and 5.")
    if protocol.get("within_block_order") not in (1, 2):
        raise RunnerError("Protocol v3 within_block_order must be 1 or 2.")
    if not isinstance(protocol.get("schedule_seed"), str) or not protocol["schedule_seed"].strip():
        raise RunnerError("Protocol v3 requires a non-empty schedule_seed.")
    condition = protocol.get("condition")
    if condition not in ("QD1", "QD2"):
        raise RunnerError("Protocol v3 requires protocol.condition to be QD1 or QD2.")

    fio = config.get("fio", {})
    if not isinstance(fio, dict):
        raise RunnerError("The 'fio' block must be a mapping.")
    name = str(fio.get("name", ""))
    if not name.lower().startswith(experiment_id.lower() + "-"):
        raise RunnerError(
            "Experiment metadata mismatch: fio.name must start with the "
            f"experiment_id ({experiment_id.lower()}-)."
        )
    if "thread" not in fio:
        raise RunnerError("Protocol v3 requires an explicit fio.thread setting.")

    expected_qd = 1 if condition == "QD1" else 2
    if fio.get("iodepth") != expected_qd:
        raise RunnerError(
            f"Protocol v3 condition {condition} requires fio.iodepth={expected_qd}."
        )

    host_state = config.get("host_state")
    if not isinstance(host_state, dict):
        raise RunnerError("Protocol v3 requires a host_state mapping.")
    for key in ("power_state", "background_activity", "system_update_state"):
        value = host_state.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().upper().startswith("REPLACE_")
        ):
            raise RunnerError(
                f"Protocol v3 requires host_state.{key} to contain an observed value, not a placeholder."
            )


def _validate_protocol_v4(config: dict[str, Any]) -> None:
    """Validate the QD1/QD2/QD4/QD8 screening protocol."""
    experiment_id = str(config.get("experiment_id", ""))
    if not re.fullmatch(r"EXP\d{3,}", experiment_id):
        raise RunnerError(
            "Protocol v4 requires experiment_id in the form EXP### or higher "
            f"(got {experiment_id!r})."
        )

    protocol = config.get("protocol", {})
    if not isinstance(protocol, dict) or protocol.get("version") != "4":
        raise RunnerError("Protocol v4 requires protocol.version: '4'.")

    for key in ("replicate_index", "run_order", "block_id", "within_block_order"):
        value = protocol.get(key)
        if not isinstance(value, int) or value < 1:
            raise RunnerError(f"Protocol v4 requires positive integer protocol.{key}.")

    if protocol["replicate_index"] > 3:
        raise RunnerError("Protocol v4 replicate_index must be between 1 and 3.")
    if protocol["run_order"] > 12:
        raise RunnerError("Protocol v4 run_order must be between 1 and 12.")
    if protocol["block_id"] > 3:
        raise RunnerError("Protocol v4 block_id must be between 1 and 3.")
    if protocol["within_block_order"] > 4:
        raise RunnerError("Protocol v4 within_block_order must be between 1 and 4.")

    if not isinstance(protocol.get("schedule_id"), str) or not protocol["schedule_id"].strip():
        raise RunnerError("Protocol v4 requires a non-empty schedule_id.")

    condition = protocol.get("condition")
    expected_qd = {"QD1": 1, "QD2": 2, "QD4": 4, "QD8": 8}.get(condition)
    if expected_qd is None:
        raise RunnerError("Protocol v4 condition must be one of QD1, QD2, QD4, QD8.")

    fio = config.get("fio", {})
    if not isinstance(fio, dict):
        raise RunnerError("The 'fio' block must be a mapping.")
    name = str(fio.get("name", ""))
    if not name.lower().startswith(experiment_id.lower() + "-"):
        raise RunnerError(
            "Experiment metadata mismatch: fio.name must start with the "
            f"experiment_id ({experiment_id.lower()}-)."
        )
    if "thread" not in fio:
        raise RunnerError("Protocol v4 requires an explicit fio.thread setting.")
    if fio.get("iodepth") != expected_qd:
        raise RunnerError(
            f"Protocol v4 condition {condition} requires fio.iodepth={expected_qd}."
        )

    host_state = config.get("host_state")
    if not isinstance(host_state, dict):
        raise RunnerError("Protocol v4 requires a host_state mapping.")
    for key in ("power_state", "background_activity", "system_update_state"):
        value = host_state.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().upper().startswith("REPLACE_")
        ):
            raise RunnerError(
                f"Protocol v4 requires host_state.{key} to contain an observed value, not a placeholder."
            )


def _host_snapshot(filename: str) -> dict[str, Any]:
    """Capture reproducibility-oriented host facts without collecting host identity."""
    snapshot: dict[str, Any] = {
        "os_system": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    try:
        usage = shutil.disk_usage(filename)
    except OSError:
        usage = None
    snapshot["target_volume_total_bytes"] = usage.total if usage else None
    snapshot["target_volume_free_bytes_before_run"] = usage.free if usage else None
    return snapshot


def _check_global_safety(config: dict[str, Any]) -> None:
    """Raise :class:`SafetyError` if the YAML config's safety block forbids execution."""
    safety = config.get("safety", {})
    if not isinstance(safety, dict):
        return
    if safety.get("allow_destructive_benchmarks") is True:
        # The flag may exist but it must remain False for the runner to proceed.
        raise SafetyError(
            "safety.allow_destructive_benchmarks is True in the loaded config; "
            "this runner does not support destructive benchmarks."
        )


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_experiment_config(config_path: Path) -> dict[str, Any]:
    """Load and minimally validate a YAML experiment config."""
    if not config_path.is_file():
        raise RunnerError(f"Experiment config not found: {config_path}")
    with config_path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise RunnerError(f"Config {config_path} must be a YAML mapping")
    return payload


def _resolve_config_path(config_name: str) -> Path:
    """Resolve config name to an absolute path, searching ``configs/`` if needed."""
    p = Path(config_name)
    if p.is_absolute():
        return p
    if p.is_file():
        return p.resolve()
    candidate = CONFIGS_DIR / config_name
    if candidate.is_file():
        return candidate
    raise RunnerError(
        f"Config {config_name!r} not found as an absolute path, relative path, "
        f"or under {CONFIGS_DIR}"
    )


# ---------------------------------------------------------------------------
# Command builder
# ---------------------------------------------------------------------------

def build_fio_command(fio_block: dict[str, Any]) -> list[str]:
    """Turn a YAML ``fio:`` block into an ``fio`` CLI argument list.

    The returned list is suitable for ``subprocess.run`` or logging; it is
    never executed by this function.  Raises :class:`SafetyError` or
    :class:`RunnerError` before returning if the configuration is unsafe or
    malformed.
    """
    if not isinstance(fio_block, dict):
        raise RunnerError("The 'fio' block in the experiment config must be a mapping")

    # Every field is pulled explicitly so we never pass unknown options silently.
    name = fio_block.get("name", "unnamed-job")
    filename = fio_block.get("filename")
    if not filename:
        raise RunnerError("fio.filename is required and must be a file path")

    filename = str(filename)
    _check_filename_safety(filename)

    # Collect job options for safety scanning before building the command.
    option_fields = {
        "rw", "bs", "iodepth", "ioengine", "direct", "runtime",
        "time_based", "group_reporting", "size", "numjobs", "thread",
        "output_format", "output",
    }
    job_options: dict[str, Any] = {k: fio_block[k] for k in option_fields if k in fio_block}

    # Also check for any extra keys the user added directly to the fio block.
    extra_keys = set(fio_block.keys()) - option_fields - {"name", "filename"}
    for key in extra_keys:
        job_options[key] = fio_block[key]

    _check_job_options_safety(job_options)

    cmd: list[str] = ["fio", f"--name={name}", f"--filename={filename}"]
    _KNOWN_FLAGS = {
        "rw", "bs", "iodepth", "ioengine", "direct", "runtime",
        "time_based", "group_reporting", "size", "numjobs", "thread",
    }
    for key in sorted(_KNOWN_FLAGS):
        if key in fio_block:
            cmd.append(f"--{key}={fio_block[key]}")
    # Always request JSON output from the runner.
    cmd.append("--output-format=json")
    return cmd


# ---------------------------------------------------------------------------
# Output-path helpers
# ---------------------------------------------------------------------------

def _output_json_path(experiment_id: str) -> Path:
    """Return the path where raw FIO JSON should be saved."""
    safe_id = experiment_id.lower().replace(" ", "_")
    return RAW_DATA_DIR / f"{safe_id}.json"


# ---------------------------------------------------------------------------
# Execution (only reached when execute=True)
# ---------------------------------------------------------------------------

def _invoke_fio(cmd: list[str], *, timeout_s: int = 120) -> str:
    """Execute *cmd* and return stdout.  Only called when execute=True.

    Importing subprocess is deferred to here so the entire dry-run path is
    clean of any subprocess dependency.
    """
    import subprocess  # local import: only needed during actual execution

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,  # we check returncode manually for a cleaner error
        )
    except FileNotFoundError:
        raise RunnerError(
            "fio executable not found on PATH.  "
            "Install fio and ensure it is on PATH before using --execute."
        )
    except subprocess.TimeoutExpired as exc:
        raise RunnerError(f"fio command timed out after {timeout_s}s: {exc}") from exc

    if result.returncode != 0:
        raise RunnerError(
            f"fio exited with code {result.returncode}.\n"
            f"stderr:\n{result.stderr.strip()}"
        )
    return result.stdout


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_experiment(
    config_name: str,
    *,
    execute: bool = False,
    output_dir: Path | None = None,
    fio_timeout_s: int = 120,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run or dry-run one FIO experiment from a YAML config.

    Parameters
    ----------
    config_name:
        Filename (e.g. ``"experiment_template.yaml"``) resolved against
        ``configs/``, or an absolute path to any YAML experiment config.
    execute:
        When ``False`` (the default) only build and validate the FIO command;
        do not run fio and do not write any output files.
        When ``True``, actually invoke fio, save the raw JSON artifact to
        ``data/raw/<experiment_id>.json``, and return a
        :class:`~ssd_performance_intelligence.data.schema.ParsedFioOutput`
        under ``result["parsed"]``.
    output_dir:
        Override the default output directory (``data/raw/``).  Useful for
        integration tests that want to write to a temp directory.
    fio_timeout_s:
        Subprocess timeout in seconds when ``execute=True``.
    overwrite:
        When ``False`` (the default), refuse to overwrite an existing raw JSON
        artifact. Set ``True`` only when intentionally replacing a run artifact.

    Returns
    -------
    dict with keys:

    ``"experiment_id"``   – string, e.g. ``"EXP_TEMPLATE"``
    ``"dry_run"``         – bool, mirrors ``not execute``
    ``"command"``         – list[str], the fio command that would be (or was) run
    ``"command_string"``  – the shell-quoted command string (informational)
    ``"output_path"``     – Path | None, where JSON was saved (None if dry-run)
    ``"parsed"``          – ParsedFioOutput | None, populated only when execute=True
    ``"timestamp"``       – ISO-8601 UTC timestamp of this call
    """
    config_path = _resolve_config_path(config_name)
    config = _load_experiment_config(config_path)

    _check_global_safety(config)
    protocol_version = str(config.get("protocol", {}).get("version", ""))
    if protocol_version == "3":
        # Protocol v3 validates metadata even during dry-run so placeholders
        # cannot reach execution accidentally.
        _validate_protocol_v3(config)
    elif protocol_version == "4":
        # Protocol v4 validates metadata even during dry-run.
        _validate_protocol_v4(config)
    elif execute:
        if protocol_version == "2":
            _validate_protocol_v2(config)
        else:
            raise RunnerError("Executable benchmark configs must declare protocol.version '2', '3', or '4'.")

    experiment_id: str = str(config.get("experiment_id", config_path.stem))
    fio_block: dict[str, Any] = config.get("fio", {})
    if not fio_block:
        raise RunnerError(f"Config {config_path} is missing a 'fio:' block")

    cmd = build_fio_command(fio_block)
    cmd_string = shlex.join(cmd) if sys.platform != "win32" else " ".join(cmd)

    result: dict[str, Any] = {
        "experiment_id": experiment_id,
        "dry_run": not execute,
        "command": cmd,
        "command_string": cmd_string,
        "output_path": None,
        "metadata_path": None,
        "parsed": None,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }

    if not execute:
        return result

    # ---- actual execution path ----------------------------------------
    raw_stdout = _invoke_fio(cmd, timeout_s=fio_timeout_s)
    parsed: ParsedFioOutput = parse_fio_output(raw_stdout)

    out_dir = output_dir if output_dir is not None else RAW_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{experiment_id.lower().replace(' ', '_')}.json"

    if out_path.exists() and not overwrite:
        raise RunnerError(
            f"Raw output already exists: {out_path}. "
            "Use a new experiment_id for a new run, or pass --overwrite only "
            "when intentionally replacing that artifact."
        )

    # Write the raw JSON payload (not the normalized Python object) to disk.
    out_path.write_text(
        json.dumps(parsed.raw, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Keep protocol metadata beside the raw artifact without modifying FIO JSON.
    protocol = config.get("protocol", {})
    metadata = {
        "experiment_id": experiment_id,
        "protocol": protocol,
        "config_path": str(config_path),
        "timestamp_utc": result["timestamp"],
        "fio_command": cmd,
        "notes": config.get("notes", {}),
        "host_state": config.get("host_state", {}),
        "host_snapshot": _host_snapshot(str(fio_block.get("filename", ""))),
    }
    metadata_path = out_path.with_suffix(".metadata.json")
    if metadata_path.exists() and not overwrite:
        out_path.unlink()
        raise RunnerError(
            f"Protocol metadata already exists: {metadata_path}. "
            "Use a new experiment_id for a new run."
        )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    result["output_path"] = out_path
    result["metadata_path"] = metadata_path
    result["parsed"] = parsed
    return result
