# Research notes

## Provenance rules

- Record license, URL, citation, collection date, and sampling bias **before** any dataset is copied into `data/raw/`.
- Prefer public, citable I/O traces and published benchmark logs over ad-hoc tests on a developer laptop.
- If local measurement is ever required, use an isolated spare device, a written protocol, and a non-system volume. Destructive or wear-heavy workloads are out of scope unless separately designed.

## Candidate data classes (not yet acquired)

These are categories to investigate, not a commitment that files are present:

- Block-level traces from published storage-research corpora
- NVMe/SATA telemetry dumps released with papers
- Synthetic workload *descriptions* (JSON/YAML) that specify I/O mix without running them

## Open questions

- Which public corpora document device model and firmware?
- How should queue depth and I/O size be binned so experiments stay comparable?
- What leakage paths exist (training on the same trace window used for evaluation)?
