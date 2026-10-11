# Protocol v5 — Latency and Achieved Queue-Depth Diagnostics

## Provenance and audit

This report is generated from the ten local Protocol v5 raw FIO JSON artifacts after the shared Protocol v5 audit passed. The script checks configuration, metadata, the FIO job schema, requested queue depth, and that the read-only job does not report write I/O.

- Scheduled runs validated: 10/10
- FIO versions: fio-3.43
- All runs in this study should use the same FIO version for direct within-study comparison.

## Per-run latency details

Completion latency (clat) percentiles are FIO per-run values. They are not pooled request-level percentiles. Submission latency (slat), completion latency (clat), and total latency (lat) are distinct measurements.

| Experiment | Block | Condition | IOPS | clat p50 (us) | clat p95 (us) | clat p99 (us) | clat p99.9 (us) | mean slat (us) | mean clat (us) | mean total lat (us) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EXP037 | 1 | QD8 | 6010.3 | 1220.6 | 1941.5 | 2342.9 | 3063.8 | 51.6 | 1256.9 | 1308.6 |
| EXP038 | 1 | QD4 | 5532.9 | 626.7 | 1056.8 | 1302.5 | 1859.6 | 49.9 | 660.0 | 710.0 |
| EXP039 | 2 | QD4 | 5559.4 | 626.7 | 1056.8 | 1302.5 | 1941.5 | 49.8 | 658.1 | 707.9 |
| EXP040 | 2 | QD8 | 5355.9 | 1335.3 | 2310.1 | 2867.2 | 4292.6 | 55.6 | 1414.6 | 1470.2 |
| EXP041 | 3 | QD4 | 5491.1 | 626.7 | 1056.8 | 1318.9 | 1941.5 | 51.5 | 663.1 | 714.6 |
| EXP042 | 3 | QD8 | 5946.5 | 1220.6 | 1941.5 | 2375.7 | 5341.2 | 53.9 | 1263.6 | 1317.5 |
| EXP043 | 4 | QD8 | 5456.4 | 1302.5 | 2244.6 | 2834.4 | 6062.1 | 53.2 | 1383.7 | 1436.9 |
| EXP044 | 4 | QD4 | 5391.3 | 626.7 | 1056.8 | 1335.3 | 3489.8 | 57.5 | 667.0 | 724.5 |
| EXP045 | 5 | QD4 | 5501.5 | 626.7 | 1056.8 | 1302.5 | 2089.0 | 50.6 | 661.8 | 712.4 |
| EXP046 | 5 | QD8 | 4840.5 | 1253.4 | 3031.0 | 8585.2 | 10158.1 | 52.7 | 1580.5 | 1633.2 |

## Condition-level diagnostic summaries

These are arithmetic means of five per-run summaries. The averages of p50/p95/p99/p99.9 values are not the percentile distribution of all requests pooled together.

| Condition | Mean IOPS | Mean BW (MB/s) | Mean slat (us) | Mean clat (us) | Mean total lat (us) | Mean per-run clat p50 (us) | Mean per-run clat p95 (us) | Mean per-run clat p99 (us) | Mean per-run clat p99.9 (us) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QD4 | 5495.3 | 720.27 | 51.8 | 662.0 | 713.9 | 626.7 | 1056.8 | 1312.4 | 2264.3 |
| QD8 | 5521.9 | 723.77 | 53.4 | 1379.9 | 1433.3 | 1266.5 | 2293.8 | 3801.1 | 5783.6 |

## Achieved queue-depth distribution

FIO iodepth_level values are percentages in FIO's depth buckets; they are not percentages of wall-clock time. Compare these with the configured depth, but do not assume the requested queue depth was achieved for every I/O.

| Experiment | Condition | Requested depth | Depth bucket 2 (%) | Depth bucket 4 (%) | Depth bucket 8 (%) |
|---|---|---:|---:|---:|---:|
| EXP037 | QD8 | 8 | 0.206 | 16.610 | 83.122 |
| EXP038 | QD4 | 4 | 9.430 | 90.408 | 0.000 |
| EXP039 | QD4 | 4 | 8.023 | 91.797 | 0.000 |
| EXP040 | QD8 | 8 | 0.233 | 14.152 | 85.544 |
| EXP041 | QD4 | 4 | 9.942 | 89.868 | 0.000 |
| EXP042 | QD8 | 8 | 0.193 | 16.546 | 83.199 |
| EXP043 | QD8 | 8 | 0.268 | 15.929 | 83.729 |
| EXP044 | QD4 | 4 | 11.811 | 88.013 | 0.000 |
| EXP045 | QD4 | 4 | 8.722 | 91.094 | 0.000 |
| EXP046 | QD8 | 8 | 0.206 | 12.154 | 87.575 |

## Recorded host state

| Experiment | Power state | Background activity | System-update state | CPU count | Free bytes before run |
|---|---|---|---|---:|---:|
| EXP037 | AC power | idle | no update in progress | 8 | 17774878720 |
| EXP038 | AC power | idle | no update in progress | 8 | 17771761664 |
| EXP039 | AC power | idle | no update in progress | 8 | 17769320448 |
| EXP040 | AC power | idle | no update in progress | 8 | 17768202240 |
| EXP041 | AC power | idle | no update in progress | 8 | 17767993344 |
| EXP042 | AC power | idle | no updates in progress | 8 | 17770127360 |
| EXP043 | AC power | idle | no updates in progress | 8 | 17770119168 |
| EXP044 | AC power | idle | no update in progress | 8 | 17767931904 |
| EXP045 | AC power | idle | no update in progress | 8 | 17767976960 |
| EXP046 | AC power | idle | no update in progress | 8 | 17767165952 |

## Interpretation

1. Throughput is very similar between conditions in Protocol v5, but the mean IOPS difference is small relative to the larger run-to-run variation observed in QD8. Do not claim a reliable throughput advantage for either condition from these five pairs.
2. Mean submission latency is similar between conditions, while mean completion latency is substantially higher at QD8. The measured latency difference is chiefly in FIO's completion-latency component, not the submission-latency component. This does not identify an SSD-internal or operating-system mechanism.
3. QD8's per-run p50, p95, p99, and p99.9 completion-latency values exceed QD4's in every paired block in this dataset. QD8's upper tail is particularly high in EXP046; preserve and investigate this result rather than excluding it.
4. The achieved-depth histograms reflect the configured conditions: QD4 runs mostly occupy the depth-4 bucket, while QD8 runs mostly occupy the depth-8 bucket. Non-zero shares in adjacent buckets are not, by themselves, evidence of a failed configuration.
5. Power/background/update labels and CPU count are stable across the runs. Minor wording differences in update-state metadata should be normalized for future conventions, not silently rewritten in historical records.

## Limitations and next decision

This is five pairs on one host and one file-based sequential-read workload. FIO latency metrics reflect the storage path observable by FIO; they do not isolate physical NAND service time or controller behavior. Averages of per-run percentile values are descriptive and are not pooled request-level percentiles.

No additional QD4/QD8 runs are recommended immediately. Preserve these results and finalize the primary Protocol v5 report with the latency diagnostics. A next study should be designed only after defining a new question, such as whether this latency trade-off generalizes to a different read-only block size or access pattern. Do not claim generalization from this host alone.
