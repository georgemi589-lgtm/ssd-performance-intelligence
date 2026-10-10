# SSD Performance Intelligence

Evidence-based research prototype for **AI-based SSD performance and workload intelligence**.

This repository is an evidence-first R&D prototype for studying how storage workloads relate to SSD performance (throughput, latency, and related telemetry). It does **not** contain trained models. The recorded study sequence now includes legacy observations and controlled Protocol v2–v4 experiments. Protocol v4 screened QD1/QD2/QD4/QD8 with 12 scheduled read-only runs. In that screen, QD4 had the highest mean throughput, while QD8 showed materially greater variability and higher mean latency; these host/workload-specific observations justify follow-up testing, not a universal SSD conclusion. See the [Protocol v4 analysis](reports/PROTOCOL_V4_SCALING_ANALYSIS.md), [Protocol v3 confirmation analysis](reports/PROTOCOL_V3_CONFIRMATION_ANALYSIS.md), and [QD1/QD2 repeatability report](reports/QD1_QD2_repeatability.md). The summary ledger is tracked at `data/analysis/observations.csv`; raw JSON and metadata sidecars remain local and are intentionally ignored by Git. The next planned step is a five-block paired QD4/QD8 confirmation study under [Protocol v5](docs/benchmark_protocol_v5.md), using scheduled configs `configs/exp037.yaml`–`configs/exp046.yaml`. These are host-level observations, not device specifications or maximum-performance results.

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

- **Scope and sample size.** Protocol v4 has only three scheduled observations per queue-depth condition on one host and one file-based workload. The v4 report documents two unsaved duplicate FIO invocations after EXP034; those results are excluded and the protocol deviation may have affected later host state.
- **Device diversity.** SSD behavior depends on NAND type, controller, DRAM/HMB, firmware, interface (SATA/NVMe), and host stack. Early findings will not generalize by default.
- **Artifact availability.** Raw FIO JSON and metadata sidecars are local-only by default. The tracked observation ledger summarizes reported results; verify local artifacts before reproducing the analysis.
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
