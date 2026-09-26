# Experiment pipeline

This document covers the automated experiment infrastructure added to the project.
It describes every step from configuration file to normalized dataset record and
explains how to run an experiment safely.

For the overarching research methodology — what to record, how to handle provenance,
and what the safety contract is for local measurement — see
[`docs/methods.md`](methods.md) and [`docs/research_notes.md`](research_notes.md).

---

## Pipeline overview

```
configs/<experiment>.yaml
        │
        ▼
experiments/run_experiment.py  ──────────────────────────────────────┐
        │                                                             │
        │  loads and validates the YAML config                       │
        │  enforces safety rules (file-path only, no block devices)  │
        │  builds the fio CLI command                                │
        │                                                             │
        │  DRY-RUN (default): prints the command, exits              │
        │                                                             │
        │  --execute: invokes fio ──────────────────────────────────►│
        │                                                             │
        ▼                                                             │
   fio (external binary)                                             │
        │                                                             │
        │  writes JSON to stdout (--output-format=json)              │
        ▼                                                             │
data/raw/<experiment_id>.json   ◄────────────────────────────────────┘
        │
        │  raw JSON is saved verbatim; it is never mutated
        ▼
ssd_performance_intelligence.data.fio_parser
        │
        │  splits off any leading non-JSON FIO warning text
        │  parses the JSON body safely
        │  passes raw dict + preamble to schema.ParsedFioOutput.from_raw()
        ▼
ssd_performance_intelligence.data.schema
        │
        │  validates every field type
        │  builds frozen, typed dataclasses
        │  preserves source units (all latency in ns, bw in KiB/s + bytes/s)
        │  exposes normalized µs values via properties
        ▼
ParsedFioOutput (in memory)
        │
        │  .raw          – the untouched original JSON dict
        │  .jobs[0..N]   – tuple of typed FioJobRecord objects
        │       .metadata         – JobMetadata
        │       .read / .write    – DirectionStats (throughput, IOPS, latency)
        │       .iodepth          – IODepthDistribution
        ▼
(future) features / model training
```

---

## Step 1 — Write a config

Copy `configs/experiment_template.yaml` and edit the fields for your run:

```yaml
experiment_id: EXP002          # unique; becomes the output file stem

safety:
  allow_destructive_benchmarks: false   # must stay false
  allow_system_disk_tests: false        # must stay false

fio:
  name: exp002-seq-read
  filename: /tmp/fio-lab/exp002_testfile.bin   # file path only — see Safety below
  size: 256M
  rw: read
  bs: 128k
  iodepth: 1
  ioengine: libaio      # windowsaio on Windows
  direct: 1
  runtime: 10
  time_based: 1
  group_reporting: 1

notes:
  objective: >
    Describe what this experiment is measuring and why.
  hardware: "Samsung 980 Pro 1 TB, NVMe, PCIe 4.0"
  os: "Ubuntu 24.04 LTS"
  limitations: >
    Single run, no device identification beyond model string.
```

Every key under `fio:` maps directly to a fio CLI flag (`--key=value`).
The runner always appends `--output-format=json`; do not include it in the config.

---

## Step 2 — Dry-run (default)

```
python experiments/run_experiment.py --config configs/exp002.yaml
```

Dry-run mode builds and validates the fio command without running it.
It exits with code 0 and prints:

```
[run_experiment] Mode: DRY-RUN — fio will NOT be invoked
                 (Pass --execute to actually run the benchmark)

Experiment : EXP002
Timestamp  : 2026-09-25T10:00:00Z
Dry-run    : True

FIO command:
  fio --name=exp002-seq-read --filename=/tmp/fio-lab/exp002_testfile.bin ...

Dry-run complete.  No fio process was started; no files were written.
```

Review the printed command and confirm it targets the correct file and workload
before proceeding to step 3.

---

## Step 3 — Execute

Only when you have reviewed the dry-run output and satisfied the
[methods checklist](methods.md):

```
python experiments/run_experiment.py \
    --config configs/exp002.yaml \
    --execute
```

On success the runner:

1. Invokes `fio` with the assembled command.
2. Captures its JSON stdout.
3. Passes the text to `fio_parser.parse_fio_output()`.
4. Saves the **raw JSON payload** to `data/raw/exp002.json`.
5. Returns the `ParsedFioOutput` object to the calling process.

The runner also refuses to overwrite an existing raw artifact by default. Use a new `experiment_id` for each run. The `--overwrite` option is available only for an intentional replacement.

Nothing is written to disk during dry-run.

---

## Step 4 — Inspect the raw artifact

`data/raw/<experiment_id>.json` contains the unmodified JSON from fio's stdout
(formatted with two-space indentation).  If fio printed a warning before its
JSON body (as on Windows), the runner strips the warning during parsing but
does not include it in the saved artifact.

The raw JSON is the single source of truth. All normalized values in Python
are derived from it; nothing is inferred, invented, or interpolated.

To parse a saved artifact from the Python REPL or a notebook:

```python
from ssd_performance_intelligence.data.fio_parser import parse_fio_file

out = parse_fio_file("data/raw/exp002.json")

job = out.jobs[0]
print(job.metadata.jobname)
print(job.read.iops.iops)           # IOPS as stored by fio
print(job.read.total_latency.mean_us)  # mean total latency in µs
print(job.read.completion_latency.p99_us)   # p99 clat in µs
```

---

## Source-unit preservation and normalized µs values

FIO stores all latency values in **nanoseconds** in its JSON.  The schema
preserves this exactly:

| Property | Unit | Source |
|---|---|---|
| `LatencyStats.min_ns` | nanoseconds | fio JSON verbatim |
| `LatencyStats.mean_ns` | nanoseconds | fio JSON verbatim |
| `LatencyStats.percentiles_ns` | nanoseconds | fio JSON verbatim |
| `LatencyStats.min_us` | microseconds | computed: `min_ns / 1000` |
| `LatencyStats.mean_us` | microseconds | computed: `mean_ns / 1000` |
| `LatencyStats.p50_us` | microseconds | computed: `percentiles_ns["50.000000"] / 1000` |
| `LatencyStats.p95_us` | microseconds | computed |
| `LatencyStats.p99_us` | microseconds | computed |
| `LatencyStats.p999_us` | microseconds | computed (`99.900000` key) |

Bandwidth:

| Property | Unit | Source |
|---|---|---|
| `ThroughputStats.bw_bytes_per_sec` | bytes/s | fio `bw_bytes` verbatim |
| `ThroughputStats.bw_kib_s` | KiB/s | fio `bw` verbatim |

No values are silently converted or renamed.  The `*_ns` suffix on every
latency field signals that you are reading a stored nanosecond value.

---

## Safety rules

The runner enforces these rules before any subprocess is created.
A `SafetyError` is raised and the program exits with code 1 if any rule is violated.

| Rule | Enforcement |
|---|---|
| `fio.filename` must be a regular file path | Checked against `/dev/`, `\\.\ `, `\\?\` prefixes |
| `safety.allow_destructive_benchmarks` must be `false` | Read from YAML config |
| `verify` and `trim` options are refused | Checked in `build_fio_command()` |
| Dry-run is the default | `execute=False` unless the caller passes `--execute` |
| Raw JSON is never mutated | `ParsedFioOutput.raw` holds the original dict; normalized fields are separate frozen dataclasses |

These rules mirror the project-wide principles in `docs/research_notes.md`:
use an isolated spare device, a written protocol, and a non-system volume.
The runner adds a code-level guard so the protocol cannot accidentally be bypassed.

---

## Module reference

### `ssd_performance_intelligence.data.fio_parser`

| Symbol | Purpose |
|---|---|
| `parse_fio_output(text)` | Parse FIO JSON text into a `ParsedFioOutput` |
| `parse_fio_file(path)` | Read a saved artifact from disk and parse it |
| `parse_fio_json_text(text)` | Low-level: return `(dict, preamble)` without validating the schema |
| `FioParseError` | Raised on malformed input |

Never invokes fio. Never writes files.

### `ssd_performance_intelligence.data.schema`

Key types (all frozen dataclasses):

| Type | Description |
|---|---|
| `ParsedFioOutput` | Top-level: `.raw` dict + `.jobs` tuple |
| `FioJobRecord` | One job: `.metadata`, `.read`, `.write`, `.trim`, `.sync`, `.iodepth` |
| `JobMetadata` | Non-metric fields: jobname, groupid, CPU, elapsed, job options |
| `DirectionStats` | One direction: throughput, IOPS, latency sub-records |
| `ThroughputStats` | Bandwidth fields in KiB/s and bytes/s |
| `IOPSStats` | IOPS and IOPS sample statistics |
| `LatencyStats` | Min/max/mean/stddev/percentiles in ns; `*_us` properties |
| `IODepthDistribution` | Achieved iodepth level, submit, and complete histograms |
| `FioSchemaError` | Raised when a field fails type validation |

### `ssd_performance_intelligence.data.runner`

| Symbol | Purpose |
|---|---|
| `run_experiment(config_name, *, execute=False, ...)` | Load config, validate, build command, optionally invoke fio |
| `build_fio_command(fio_block)` | Assemble the fio CLI argument list from a config dict |
| `SafetyError` | Raised when a safety rule is violated (exits with code 1) |
| `RunnerError` | Raised for configuration or execution errors |

---

## Running the tests

```
pytest tests/test_fio_parser.py tests/test_schema.py -v
```

Tests use only the synthetic fixture in `tests/fixtures/fio_fixtures.py`.
They never invoke fio and never read from `data/raw/`.

---

## Adding a new experiment

1. Copy `configs/experiment_template.yaml` → `configs/expNNN.yaml`.
2. Set `experiment_id`, `fio.filename`, and `fio.*` parameters.
3. Run the dry-run and review the printed command.
4. Complete the [methods checklist](methods.md) for this experiment.
5. Run with `--execute`.
6. Create `experiments/EXPNNN.md` documenting the objective, hardware context,
   workload, and limitations (follow `experiments/EXP001.md` as the template).
7. Create `reports/EXPNNN.md` with the results table (follow `reports/EXP001.md`).
8. Parse `data/raw/expNNN.json` with `parse_fio_file()` to produce the
   normalized Python record for downstream feature engineering.
