# SSD Performance Intelligence

Evidence-based research prototype for **AI-based SSD performance and workload intelligence**.

This repository is a structured starting point for studying how storage workloads relate to SSD behavior (throughput, latency, and related telemetry). It does **not** contain trained models. One documented host-level FIO snapshot exists ([EXP001](reports/EXP001.md)); that run is not a device spec and not a maximum-performance result.

## Research problem

Solid-state drives exhibit workload-dependent performance: sequential vs random I/O, queue depth, mix of reads and writes, and device-internal state can all change observed latency and throughput. Operators and researchers often see these effects only after the fact, from coarse benchmarks or incomplete telemetry.

The long-term research goal is to ask, with measured evidence rather than vendor slogans:

- Which workload features are associated with SSD performance variation?
- Can models trained on documented traces or controlled experiments **predict** or **explain** performance under held-out workloads?
- Where do such models fail (device type, firmware, cache effects, thermal throttling, write amplification)?

No accuracy, speedup, ranking, or peak-SSD claims are made. EXP001 is reported with methods, the raw FIO artifact, and explicit limits (unknown device; host-level FIO only).

## Initial research questions

1. **Representation.** What compact, reproducible features describe an SSD workload (I/O size, randomness, read/write mix, concurrency, burstiness) without requiring destructive device tests?
2. **Data sources.** Which public traces, published benchmark logs, or carefully scoped local measurements are suitable, and what bias do they introduce?
3. **Prediction vs explanation.** For a given device class and workload window, can we estimate latency/throughput distributions better than simple baselines, and which features drive those estimates?
4. **Generalization.** Do relationships learned on one dataset or device transfer to another, or are they device-specific?
5. **Operational use.** If a model is useful at all, what would a conservative inference workflow look like (inputs, outputs, confidence, human review)—without claiming production readiness?

## Scope

**In scope (this prototype):**

- Reproducible project layout, configuration, and documentation
- Data ingestion and feature pipelines *once* datasets are added with provenance
- Later: baselines, models, evaluation protocols, and a thin app/report layer

**Out of scope (current phase):**

- Training or shipping ML models
- Downloading or redistributing third-party datasets
- Destructive or wear-inducing disk benchmarks (e.g. filling a live system disk, unconstrained `fio` on production volumes)
- Invented numbers, leaderboards, or “SOTA” claims

## Limitations

- **Sparse measurements.** EXP001 is a single sequential-read FIO job. `data/` is otherwise empty; do not treat placeholders as hidden results. Device model for EXP001 is unknown.
- **Device diversity.** SSD behavior depends on NAND type, controller, DRAM/HMB, firmware, interface (SATA/NVMe), and host stack. Early findings will not generalize by default.
- **Observability.** Host-level I/O stats omit much of FTL, GC, and NAND-level state.
- **Ethics and safety.** Benchmarks that wear devices or disrupt a user’s machine are excluded unless explicitly designed, isolated, and documented later.
- **Reproducibility burden.** Any future number in `reports/` must cite config, data hash, code version, and hardware context.

## Planned workflow

1. **Literature and data audit** — catalog candidate traces and papers; record licenses and sampling bias (`docs/`).
2. **Ingest** — add *documented* datasets only to `data/raw/` (never commit large binaries by default); write loaders in `src/ssd_performance_intelligence/data/`.
3. **Features** — implement deterministic transformations in `features/`; pin versions in `configs/`.
4. **Baselines first** — simple statistical predictors before any learned model (`experiments/`, `evaluation/`).
5. **Models (later)** — train only after splits, metrics, and leakage checks are specified.
6. **Reporting** — methods and negative results in `reports/`; notebooks for exploration only, not as the source of truth.
7. **Optional interface** — `app/` for inspecting artifacts, not for unverified recommendations.

## Repository layout

| Path | Role |
|------|------|
| `configs/` | Experiment and pipeline configuration (no result tables) |
| `data/raw/`, `data/processed/`, `data/sample/` | Local data placeholders; sample files must stay tiny and documented |
| `docs/` | Research notes and methods |
| `experiments/` | Runnable experiment entrypoints (added as studies are defined) |
| `notebooks/` | Exploratory analysis |
| `src/ssd_performance_intelligence/` | Installable package (`data`, `features`, `models`, `evaluation`, `inference`) |
| `tests/` | Automated checks |
| `app/` | Future inspection UI/CLI |
| `reports/` | Written findings after evidence exists |

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License and contribution

Research prototype. Add a license file before public redistribution of code or data. Do not commit raw telemetry that may include host identifiers without review.
