# QD1/QD2 repeatability analysis

This report records the sequential-read repeatability work under Benchmark Protocol v2 and keeps legacy observations explicitly separated from the controlled protocol subset.

## Final Protocol v2 dataset

The controlled baseline is complete with five observations per condition.

| Run order | Experiment | Condition | IOPS | Bandwidth (B/s) | Mean total latency (µs) |
|---:|---|---|---:|---:|---:|
| 1 | EXP005 | QD1 | 3564.4 | 467198745 | 278.4 |
| 2 | EXP006 | QD2 | 4450.0 | 583264502 | 438.0 |
| 3 | EXP007 | QD1 | 1834.1 | 240401329 | 539.3 |
| 4 | EXP008 | QD2 | 4430.8 | 580748171 | 442.3 |
| 5 | EXP009 | QD1 | 1783.8 | 233809067 | 554.6 |
| 6 | EXP010 | QD2 | 4117.3 | 539661208 | 472.7 |
| 7 | EXP011 | QD1 | 2674.8 | 350595647 | 371.3 |
| 8 | EXP012 | QD2 | 5064.8 | 663852616 | 391.6 |
| 9 | EXP013 | QD1 | 1765.1 | 231358265 | 560.4 |
| 10 | EXP014 | QD2 | 3705.2 | 485651838 | 524.1 |

All ten controlled runs were executed with FIO 3.42 using the same file target, 128 KiB sequential-read workload, 256 MiB test size, 10-second timed run, direct I/O, and explicit thread setting.

## Descriptive statistics

| Condition | Metric | n | Mean | Median | Sample SD | CV | Min | Max |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| QD1 | IOPS | 5 | 2324.440 | 1834.100 | 791.492 | 34.051% | 1765.100 | 3564.400 |
| QD2 | IOPS | 5 | 4353.620 | 4430.800 | 499.329 | 11.469% | 3705.200 | 5064.800 |
| QD1 | Bandwidth (B/s) | 5 | 304672610.6 | 240401329.0 | 103743797.8 | 34.051% | 231358265 | 467198745 |
| QD2 | Bandwidth (B/s) | 5 | 570635667.0 | 580748171.0 | 65446195.6 | 11.469% | 485651838 | 663852616 |
| QD1 | Mean total latency (µs) | 5 | 460.800 | 539.300 | 128.609 | 27.910% | 278.400 | 560.400 |
| QD2 | Mean total latency (µs) | 5 | 453.740 | 442.300 | 48.862 | 10.769% | 391.600 | 524.100 |

The QD2 mean IOPS is approximately 87.3% higher than the QD1 mean in this dataset. That is a descriptive contrast only.

## Run-order observation

The protocol interleaved QD1 and QD2 as odd/even run orders. This reduced long uninterrupted condition blocks, but it also means condition and run-order parity are perfectly aligned: every QD1 run occurred at an odd run order and every QD2 run at an even run order.

Within-condition IOPS decreases across run order for both groups in these ten observations. The descriptive Pearson correlation between run order and IOPS is approximately -0.55 for QD1 and -0.27 for QD2. With only five observations per condition, these are exploratory diagnostics, not statistical inference.

Because queue depth and run-order parity are aliased, the present experiment cannot cleanly establish a causal QD1-vs-QD2 effect independent of time/order effects.

## Key findings

1. QD1 is considerably less repeatable than QD2 for this workload on this host. IOPS CV is 34.1% for QD1 versus 11.5% for QD2.
2. The observed QD2 IOPS is higher in every interleaved run-order pair than the immediately preceding QD1 observation, but this paired pattern is still descriptive and does not prove causality.
3. Mean latency is much closer between conditions than throughput is: 460.8 µs for QD1 versus 453.7 µs for QD2.
4. The large QD1 spread and the visible run-order trend indicate that host/system-state variability is material and should be treated as a first-class experimental factor.
5. Legacy EXP001/EXP002 observations are retained separately and are not used to claim Protocol v2 replication. Their original raw artifacts were overwritten before the artifact-protection workflow existed.

## Decision

The baseline has successfully established that repeatability is not uniform across queue-depth conditions on this host. The data are strong enough to justify moving to a better-controlled experimental design, but not strong enough to claim that queue depth alone causes the observed throughput difference.

Before expanding to QD4/QD8, the next experiment should improve the design by randomizing or counterbalancing condition order and explicitly recording additional host-state variables. A blocked or randomized sequence is preferable to a fixed odd/even assignment.

No production-readiness or NAND-level conclusion is supported by this dataset.
