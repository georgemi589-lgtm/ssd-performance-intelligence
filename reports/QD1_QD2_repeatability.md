# QD1/QD2 repeatability analysis

This report records the controlled sequential-read repeatability baseline under Benchmark Protocol v2.

## Dataset

| Experiment | Requested QD | IOPS | Bandwidth (B/s) | Mean total latency (µs) |
|---|---:|---:|---:|---:|
| EXP001 | 1 | 4823.318 | 632201893 | 205.254 |
| EXP003 | 1 | 2368.100 | 310386778 | 417.000 |
| EXP005 | 1 | 3564.400 | 467198745 | 278.400 |
| EXP007 | 1 | 1834.100 | 240401329 | 539.300 |
| EXP002 | 2 | 4332.267 | 567838870 | 440.430 |
| EXP004 | 2 | 4484.700 | 587812245 | 429.900 |
| EXP006 | 2 | 4450.000 | 583264502 | 438.000 |
| EXP008 | 2 | 4430.800 | 580748171 | 442.300 |

EXP001 and EXP002 are preserved as documented observations because their original raw artifacts were overwritten by subsequent repeat runs. EXP003, EXP004, EXP005, EXP006, EXP007, and EXP008 have retained local raw JSON artifacts. Protocol v2 runs also have metadata sidecars.

## Descriptive variability

| Condition | Metric | n | Mean | Sample SD | CV |
|---|---|---:|---:|---:|---:|
| QD1 | IOPS | 4 | 3147.479 | 1330.996 | 42.288% |
| QD2 | IOPS | 4 | 4424.442 | 65.373 | 1.478% |
| QD1 | Bandwidth | 4 | 412547168.8 B/s | 174197022.7 B/s | 42.287% |
| QD2 | Bandwidth | 4 | 579915947.0 B/s | 8565682.1 B/s | 1.477% |
| QD1 | Mean total latency | 4 | 359.988 µs | 148.327 µs | 41.203% |
| QD2 | Mean total latency | 4 | 437.658 µs | 5.463 µs | 1.248% |

These are sample descriptive statistics. The sample sizes remain small, so they should not be treated as population estimates.

## Interpretation

With four observations in each group, the QD1 measurements continue to show substantially greater run-to-run variability than the QD2 measurements on this host.

For IOPS, the observed QD1 range is 1834.1 to 4823.3, while the observed QD2 range is 4332.3 to 4484.7. The corresponding descriptive CVs are about 42.3% for QD1 and 1.48% for QD2.

This is a measurement-system observation, not evidence that queue depth itself causes the observed performance difference. The baseline remains focused on characterizing repeatability before introducing higher queue depths or predictive modeling.

## Missing values

Complete latency percentile data are not available in the retained console summaries for EXP003 and EXP004. Those fields remain blank rather than reconstructed or imputed. EXP005 through EXP008 were recorded through the Protocol v2 runner; this checkpoint preserves the headline latency metric reported by the runner.

## Provenance note

EXP001 and EXP002 raw JSON artifacts were overwritten before the current artifact-protection workflow existed. Their reported values are retained only as contemporaneously documented observations and are not reconstructed into synthetic raw FIO JSON.

## Next protocol step

Continue the interleaved five-repeat QD1/QD2 baseline. Do not expand to QD4/QD8 or build performance models until the baseline repeatability dataset is complete and reviewed.
