# QD1/QD2 repeatability analysis

This report records the controlled sequential-read repeatability baseline under Benchmark Protocol v2.

## Dataset

| Experiment | Requested QD | IOPS | Bandwidth (B/s) | Mean total latency (µs) |
|---|---:|---:|---:|---:|
| EXP001 | 1 | 4823.318 | 632201893 | 205.254 |
| EXP003 | 1 | 2368.100 | 310386778 | 417.000 |
| EXP005 | 1 | 3564.400 | 467198745 | 278.400 |
| EXP007 | 1 | 1834.100 | 240401329 | 539.300 |
| EXP009 | 1 | 1783.800 | 233809067 | 554.600 |
| EXP002 | 2 | 4332.267 | 567838870 | 440.430 |
| EXP004 | 2 | 4484.700 | 587812245 | 429.900 |
| EXP006 | 2 | 4450.000 | 583264502 | 438.000 |
| EXP008 | 2 | 4430.800 | 580748171 | 442.300 |

EXP001 and EXP002 are preserved as documented observations because their original raw artifacts were overwritten by subsequent repeat runs. EXP003, EXP004, EXP005, EXP006, EXP007, EXP008, and EXP009 have retained local raw JSON artifacts. Protocol v2 runs also have metadata sidecars.

## Descriptive variability

| Condition | Metric | n | Mean | Sample SD | CV |
|---|---|---:|---:|---:|---:|
| QD1 | IOPS | 5 | 2874.744 | 1304.066 | 45.363% |
| QD2 | IOPS | 4 | 4424.442 | 65.373 | 1.478% |
| QD1 | Bandwidth | 5 | 376799562.4 B/s | 170926724.4 B/s | 45.363% |
| QD2 | Bandwidth | 4 | 579915947.0 B/s | 8565682.1 B/s | 1.477% |
| QD1 | Mean total latency | 5 | 398.911 µs | 155.162 µs | 38.897% |
| QD2 | Mean total latency | 4 | 437.658 µs | 5.463 µs | 1.248% |

These are sample descriptive statistics. The QD1 condition now has five observations, while QD2 has four; this remains a small host-specific dataset.

## Interpretation

The five observed QD1 runs continue to show substantial run-to-run variability. QD1 IOPS ranges from 1783.8 to 4823.3, with a descriptive CV of about 45.4%.

The four observed QD2 runs remain tightly clustered at 4332.3 to 4484.7 IOPS, with a descriptive CV of about 1.48%.

This is a measurement-system observation, not evidence that queue depth itself causes the observed performance difference. QD1 and QD2 are still being characterized under the controlled protocol, and the QD2 condition needs its fifth repeat before the baseline is complete.

## Missing values

Complete latency percentile data are not available in the retained console summaries for EXP003 and EXP004. Those fields remain blank rather than reconstructed or imputed. EXP005 through EXP009 were recorded through the Protocol v2 runner; this checkpoint preserves the headline latency metric reported by the runner.

## Provenance note

EXP001 and EXP002 raw JSON artifacts were overwritten before the current artifact-protection workflow existed. Their reported values are retained only as contemporaneously documented observations and are not reconstructed into synthetic raw FIO JSON.

## Next protocol step

Complete the fifth QD2 repeat under Protocol v2. Do not expand to QD4/QD8 or build performance models until both QD1 and QD2 baseline sets are complete and reviewed.
