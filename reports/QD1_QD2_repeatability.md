# QD1/QD2 repeatability analysis

This report records the sequential-read repeatability work under Benchmark Protocol v2 and keeps legacy observations explicitly separated from the controlled protocol subset.

## Protocol v2 subset

The current controlled subset contains five QD1 and four QD2 observations.

| Condition | n (v2) | IOPS mean | IOPS sample SD | IOPS CV | Mean latency | Latency sample SD | Latency CV |
|---|---:|---:|---:|---:|---:|---:|---:|
| QD1 | 5 | 2324.440 | 791.492 | 34.051% | not yet recomputed in this ledger | — | — |
| QD2 | 4 | 4515.725 | 396.551 | 8.782% | 445.650 µs | 18.759 µs | 4.210% |

The planned five-repeat controlled QD1 set is now complete. QD2 still requires one final Protocol v2 observation before the controlled baseline can be closed.

## Interpretation

EXP013 produced 1765.1 IOPS, the lowest QD1 observation in the controlled subset. The QD1 IOPS CV remains about 34.1%, showing substantial run-to-run variability.

The QD2 subset currently has CV about 8.8% in IOPS after the high 5064.8 IOPS observation from EXP012. QD2 is therefore more variable than earlier estimates suggested, but still tighter than QD1 in this host-specific dataset.

These are descriptive measurement-system observations. They do not establish that queue depth itself causes the observed performance differences.

## Provenance

Legacy EXP001/EXP002 observations remain explicitly separated from Protocol v2. Their original raw artifacts were overwritten before the current artifact-protection workflow existed. EXP005 through EXP013 are Protocol v2 runs with retained raw JSON and metadata sidecars.

## Next protocol step

Complete the fifth Protocol v2 QD2 observation. Then stop benchmarking and perform the full baseline review, including run order, descriptive statistics, provenance, protocol compliance, and sensitivity to the legacy observations, before deciding whether to expand to QD4/QD8.
