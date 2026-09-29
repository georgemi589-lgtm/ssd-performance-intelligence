# QD1/QD2 repeatability analysis

This report records the sequential-read repeatability work under Benchmark Protocol v2 and keeps legacy observations explicitly separated from the controlled protocol subset.

## Protocol v2 subset

The current controlled subset contains four QD1 and four QD2 observations.

| Condition | n (v2) | IOPS mean | IOPS sample SD | IOPS CV | Mean latency | Latency sample SD | Latency CV |
|---|---:|---:|---:|---:|---:|---:|---:|
| QD1 | 4 | 2464.275 | 839.596 | 34.071% | 435.900 µs | 133.866 µs | 30.710% |
| QD2 | 4 | 4515.725 | 396.551 | 8.782% | 445.650 µs | 18.759 µs | 4.210% |

The controlled baseline is now one QD1 observation away from the planned five-repeat design.

## Interpretation

EXP012 is the highest observed QD2 IOPS in the current Protocol v2 subset, at 5064.8 IOPS. This increases QD2 run-to-run variability compared with the previous three QD2 observations, but the descriptive QD2 CV remains lower than the current QD1 CV.

This remains a measurement-system observation, not evidence that queue depth itself causes the observed performance difference.

## Provenance

Legacy EXP001/EXP002 observations remain explicitly separated from Protocol v2. Their original raw artifacts were overwritten before the current artifact-protection workflow existed. EXP005 through EXP012 are Protocol v2 runs with retained raw JSON and metadata sidecars.

## Next protocol step

Complete the fifth Protocol v2 QD1 observation. Then perform a full baseline review, including run order, descriptive statistics, provenance, and protocol compliance, before deciding whether to expand the experiment matrix.
