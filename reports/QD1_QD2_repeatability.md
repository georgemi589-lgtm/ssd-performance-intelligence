# QD1/QD2 repeatability analysis

This report records the sequential-read repeatability work under Benchmark Protocol v2 and keeps legacy observations explicitly separated from the controlled protocol subset.

## Dataset

| Experiment | Requested QD | IOPS | Bandwidth (B/s) | Mean total latency (µs) | Protocol |
|---|---:|---:|---:|---:|---|
| EXP001 | 1 | 4823.318 | 632201893 | 205.254 | legacy |
| EXP003 | 1 | 2368.100 | 310386778 | 417.000 | legacy |
| EXP005 | 1 | 3564.400 | 467198745 | 278.400 | v2 |
| EXP007 | 1 | 1834.100 | 240401329 | 539.300 | v2 |
| EXP009 | 1 | 1783.800 | 233809067 | 554.600 | v2 |
| EXP002 | 2 | 4332.267 | 567838870 | 440.430 | legacy |
| EXP004 | 2 | 4484.700 | 587812245 | 429.900 | legacy |
| EXP006 | 2 | 4450.000 | 583264502 | 438.000 | v2 |
| EXP008 | 2 | 4430.800 | 580748171 | 442.300 | v2 |
| EXP010 | 2 | 4117.300 | 539661208 | 472.700 | v2 |

EXP001 and EXP002 are preserved only as documented observations because their original raw artifacts were overwritten before the artifact-protection workflow existed. EXP003 and EXP004 are retained local raw artifacts from the legacy repeat stage. EXP005 through EXP010 are Protocol v2 runs with raw JSON and metadata sidecars.

## Five-observation documented baseline

Across all documented observations, both QD1 and QD2 currently have n=5.

| Condition | Metric | n | Mean | Median | Sample SD | CV | Min | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| QD1 | IOPS | 5 | 2874.744 | 2368.100 | 1304.066 | 45.363% | 1783.800 | 4823.318 |
| QD2 | IOPS | 5 | 4363.013 | 4430.800 | 148.568 | 3.405% | 4117.300 | 4484.700 |
| QD1 | Bandwidth (B/s) | 5 | 376799562.4 | 310386778.0 | 170926724.4 | 45.363% | 233809067 | 632201893 |
| QD2 | Bandwidth (B/s) | 5 | 571864999.2 | 580748171.0 | 19470926.6 | 3.405% | 539661208 | 587812245 |
| QD1 | Mean total latency (µs) | 5 | 398.911 | 417.000 | 155.162 | 38.897% | 205.254 | 554.600 |
| QD2 | Mean total latency (µs) | 5 | 444.666 | 440.430 | 16.370 | 3.681% | 429.900 | 472.700 |

These statistics mix legacy and Protocol v2 observations and are therefore descriptive context, not the final controlled-protocol result.

## Protocol v2 subset

The current controlled subset contains three QD1 and three QD2 observations.

| Condition | n (v2) | IOPS mean | IOPS sample SD | IOPS CV |
|---|---:|---:|---:|---:|
| QD1 | 3 | 2394.100 | 1033.026 | 43.146% |
| QD2 | 3 | 4332.700 | 179.245 | 4.137% |

The Protocol v2 subset is still too small to close the planned five-repeat controlled baseline.

## Interpretation

The measurements show materially different run-to-run variability between the QD1 and QD2 groups on this host. However, this remains a measurement-system observation. It does not establish that queue depth itself causes the observed performance difference.

The legacy observations are retained for provenance and historical context but are not silently treated as Protocol v2 replicates.

## Missing values

Complete latency percentile data are not available in the retained console summaries for EXP003 and EXP004. Those fields remain blank rather than reconstructed or imputed. EXP005 through EXP010 preserve the headline latency metric reported by the runner.

## Next protocol step

Complete two additional Protocol v2 repeats for each condition, maintaining the interleaved design. Only after five Protocol v2 observations per QD1 and QD2 are available and reviewed should the project consider QD4/QD8 or predictive modeling.
