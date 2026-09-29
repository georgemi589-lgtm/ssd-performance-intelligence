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
| EXP011 | 1 | 2674.800 | 350595647 | 371.300 | v2 |
| EXP002 | 2 | 4332.267 | 567838870 | 440.430 | legacy |
| EXP004 | 2 | 4484.700 | 587812245 | 429.900 | legacy |
| EXP006 | 2 | 4450.000 | 583264502 | 438.000 | v2 |
| EXP008 | 2 | 4430.800 | 580748171 | 442.300 | v2 |
| EXP010 | 2 | 4117.300 | 539661208 | 472.700 | v2 |

EXP001 and EXP002 are preserved only as documented observations because their original raw artifacts were overwritten before the artifact-protection workflow existed. EXP003 and EXP004 are retained local raw artifacts from the legacy repeat stage. EXP005 through EXP011 are Protocol v2 runs with raw JSON and metadata sidecars.

## Five-observation documented baseline

Across all documented observations, QD1 has n=6 and QD2 has n=5.

## Protocol v2 subset

The current controlled subset contains four QD1 and three QD2 observations.

| Condition | n (v2) | IOPS mean | IOPS sample SD | IOPS CV | Mean latency | Latency sample SD | Latency CV |
|---|---:|---:|---:|---:|---:|---:|---:|
| QD1 | 4 | 2464.275 | 839.596 | 34.071% | 435.900 µs | 133.866 µs | 30.710% |
| QD2 | 3 | 4332.700 | 186.789 | 4.311% | 451.000 µs | 18.915 µs | 4.194% |

The Protocol v2 subset is still too small to close the planned five-repeat controlled baseline.

## Interpretation

The controlled observations continue to show materially different run-to-run variability between the QD1 and QD2 groups on this host. QD1 remains substantially more variable across the current controlled measurements.

This is a measurement-system observation, not evidence that queue depth itself causes the observed performance difference. The legacy observations remain separate and are not silently treated as Protocol v2 replicates.

## Missing values

Complete latency percentile data are not available in the retained console summaries for EXP003 and EXP004. Those fields remain blank rather than reconstructed or imputed. EXP005 through EXP011 preserve the headline latency metric reported by the runner.

## Provenance note

EXP001 and EXP002 raw JSON artifacts were overwritten before the current artifact-protection workflow existed. Their reported values are retained only as contemporaneously documented observations and are not reconstructed into synthetic raw FIO JSON.

## Next protocol step

Complete one additional QD2 Protocol v2 repeat and then one additional QD1 Protocol v2 repeat, preserving the interleaved design. Only after five Protocol v2 observations per QD1 and QD2 are available and reviewed should the project consider QD4/QD8 or predictive modeling.
