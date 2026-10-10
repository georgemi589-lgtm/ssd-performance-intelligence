# Protocol v4 — Queue-Depth Scaling Analysis

## Executive summary

Protocol v4 screened a file-based sequential-read workload at queue depths 1, 2, 4, and 8. The planned schedule contains three observations per condition (12 scheduled runs total).

In this single-host screening dataset, mean IOPS rose from QD1 through QD4. QD4 had the highest observed condition mean (5,762.6 IOPS). QD8 had a lower mean (5,143.5 IOPS), higher mean latency (1,587.8 microseconds), and much greater run-to-run variability (IOPS coefficient of variation 20.70%). QD8 outperformed QD4 in one of the three blocks but underperformed it in the other two.

These are descriptive results for this host, test file, and workload. They do not establish a universal optimum, device saturation, controller behavior, or NAND-level behavior. The QD8 variability warrants a targeted follow-up before model development.

## Research question

How do measured sequential-read IOPS, bandwidth, mean latency, and run-to-run variability change across QD1, QD2, QD4, and QD8 under the same file-based workload?

## Protocol and workload

- Protocol: v4, schedule ID `v4-balanced-3rep-v1`
- Design: three blocks, with each queue-depth condition appearing once in each block
- Planned sample size: 12 runs; three observations per condition
- Target: file-based test file at `C:\\fio-lab\\exp001_testfile.bin`
- Operation: sequential read only
- Block size: 128 KiB
- Configured test size: 256 MiB
- Runtime: 10 seconds, time-based
- I/O engine: `windowsaio`
- Direct I/O: enabled
- FIO thread setting: 1
- Conditions: QD1, QD2, QD4, QD8
- Raw result files were reported as saved locally for all 12 scheduled experiments. They are not embedded in this report and should remain preserved as separate artifacts.

This is a screening design, not a fully balanced crossover design. The order varies across blocks, but with three blocks the conditions cannot occupy every within-block position equally.

## Scheduled observations

Bandwidth is reported in bytes per second as shown by the runner. Latency is the mean latency value reported by the runner. Values below are the 12 scheduled observations, in run order.

| Run order | Experiment | Block | Position | Condition | IOPS | Bandwidth (B/s) | Mean latency (µs) |
|---:|---|---:|---:|---|---:|---:|---:|
| 1 | EXP025 | 1 | 1 | QD2 | 3,788.7 | 496,595,255 | 513.7 |
| 2 | EXP026 | 1 | 2 | QD8 | 5,433.9 | 712,233,873 | 1,454.9 |
| 3 | EXP027 | 1 | 3 | QD1 | 1,791.3 | 234,792,008 | 552.4 |
| 4 | EXP028 | 1 | 4 | QD4 | 5,884.2 | 771,255,380 | 667.5 |
| 5 | EXP029 | 2 | 1 | QD4 | 5,544.0 | 726,669,144 | 708.6 |
| 6 | EXP030 | 2 | 2 | QD1 | 1,749.1 | 229,261,323 | 565.9 |
| 7 | EXP031 | 2 | 3 | QD8 | 3,963.8 | 519,546,512 | 1,999.2 |
| 8 | EXP032 | 2 | 4 | QD2 | 3,656.6 | 479,282,375 | 531.6 |
| 9 | EXP033 | 3 | 1 | QD1 | 1,697.7 | 222,524,896 | 582.8 |
| 10 | EXP034 | 3 | 2 | QD4 | 5,859.7 | 768,044,437 | 679.5 |
| 11 | EXP035 | 3 | 3 | QD2 | 3,807.3 | 499,032,951 | 514.5 |
| 12 | EXP036 | 3 | 4 | QD8 | 6,032.9 | 790,743,406 | 1,309.4 |

## Descriptive statistics

For a condition with observations (x_1,\ldots,x_n), the report uses the arithmetic mean, sample standard deviation, and coefficient of variation:

[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\qquad
s=\sqrt{\frac{\sum_{i=1}^{n}(x_i-\bar{x})^2}{n-1}}
\qquad
CV=\frac{s}{\bar{x}}\times100\%.
]

The standard deviation uses (n-1) in the denominator. With only three runs per condition, the estimates are sensitive to individual observations and are descriptive, not population-level estimates.

| Condition | n | Mean IOPS | Median IOPS | Sample SD IOPS | IOPS CV | Min IOPS | Max IOPS | Mean bandwidth (MB/s) | Mean latency (µs) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| QD1 | 3 | 1,746.0 | 1,749.1 | 46.9 | 2.69% | 1,697.7 | 1,791.3 | 228.86 | 567.0 |
| QD2 | 3 | 3,750.9 | 3,788.7 | 82.2 | 2.19% | 3,656.6 | 3,807.3 | 491.64 | 519.9 |
| QD4 | 3 | 5,762.6 | 5,859.7 | 189.7 | 3.29% | 5,544.0 | 5,884.2 | 755.32 | 685.2 |
| QD8 | 3 | 5,143.5 | 5,433.9 | 1,064.7 | 20.70% | 3,963.8 | 6,032.9 | 674.17 | 1,587.8 |

Bandwidth in MB/s uses decimal units: 1 MB/s = 1,000,000 B/s.

Additional variability context:

| Condition | Sample SD bandwidth (MB/s) | Bandwidth CV | Sample SD latency (µs) | Latency CV |
|---|---:|---:|---:|---:|
| QD1 | 6.14 | 2.68% | 15.2 | 2.69% |
| QD2 | 10.77 | 2.19% | 10.1 | 1.94% |
| QD4 | 24.87 | 3.29% | 21.1 | 3.08% |
| QD8 | 139.55 | 20.70% | 363.6 | 22.90% |

## Within-block comparison

Each block included all four queue-depth conditions. The block-specific IOPS are:

| Block | QD1 | QD2 | QD4 | QD8 | QD8 minus QD4 | QD8 relative to QD4 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,791.3 | 3,788.7 | 5,884.2 | 5,433.9 | -450.3 | -7.65% |
| 2 | 1,749.1 | 3,656.6 | 5,544.0 | 3,963.8 | -1,580.2 | -28.50% |
| 3 | 1,697.7 | 3,807.3 | 5,859.7 | 6,032.9 | +173.2 | +2.96% |

QD4 exceeded QD8 in two blocks; QD8 exceeded QD4 in one. The direction is therefore not uniform in every block, even though the overall QD4 mean is higher.

Relative to the QD1 mean, the mean IOPS were about 2.15 times higher at QD2 and 3.30 times higher at QD4. These ratios describe this data set only; they should not be generalized to other systems.

## Interpretation

### 1. Throughput rose from QD1 through QD4

The condition means were ordered QD1 < QD2 < QD4. This pattern was also visible within each block. It supports the bounded observation that higher configured queue depth was associated with higher measured throughput up to QD4 under the present workload and host setup.

### 2. QD8 did not provide a consistent improvement over QD4

The mean QD8 IOPS was 10.74% lower than the mean QD4 IOPS. Mean QD8 bandwidth was also lower. The block-level contrast shows this was driven especially by Block 2; QD8 was slightly faster in Block 3. With three observations per condition, this is a screening signal, not proof that QD8 is intrinsically slower.

### 3. QD8 showed materially higher observed variability and latency

QD8 had an IOPS CV of 20.70% and latency CV of 22.90%, compared with IOPS CVs between 2.19% and 3.29% for QD1–QD4. Its mean latency was about 2.32 times QD4's mean latency. This makes QD8 the priority condition for further controlled investigation.

### 4. The data do not identify a cause

Potential explanations include time-varying host activity, device state, workload/queue interactions, or other environmental effects. The current observations do not discriminate among these explanations. No causal attribution is made to the SSD controller, firmware, NAND, thermal state, or operating system.

## Protocol deviation and artifact integrity

After the scheduled EXP034 run had completed and its output had been saved, two accidental repeat commands were issued with the same experiment ID. At that point, the runner checked for an existing raw artifact only after invoking FIO. The duplicate commands therefore invoked FIO before the runner rejected the attempts because `exp034.json` already existed. The outputs from those duplicate attempts were not saved as separate artifacts and are excluded from the 12-observation analysis.

The duplicate read runs may have affected the system's state before later scheduled runs. Their measurements are unavailable, so their effect cannot be quantified. This deviation should remain visible in the research record rather than being silently ignored.

A software correction has now been committed: the runner checks both the raw JSON path and metadata-sidecar path before invoking FIO, then checks again before writing. Regression tests were added for existing raw and metadata artifacts. The local test suite must be run after syncing these changes; this report does not claim those tests have passed.

Before this report is considered fully audited, verify locally that all 12 scheduled raw JSON files and their metadata sidecars exist and that the JSON files parse successfully. The terminal messages confirm that the raw JSON files were reported saved; this report was created from the metrics shared in the conversation, not by independently parsing the local artifacts.

## Limitations

- One host and one file-based test target were used.
- Three scheduled observations per condition are too few for strong population-level or inferential claims.
- The design varies condition positions but is not a fully balanced crossover.
- A documented protocol deviation introduced two unsaved duplicate FIO invocations after EXP034.
- Host-state and environment metadata need a local completeness audit.
- Results do not measure raw-device performance, endurance, write amplification, NAND behavior, controller internals, or production workload performance.
- No predictive model should be trained or validated from this 12-run screen alone.

## Decision and next experiment

1. Audit the local artifacts and metadata for EXP025–EXP036 and confirm that each raw JSON is parseable.
2. Sync the runner guard and regression tests; run the full existing test suite and record its actual result.
3. Conduct a targeted QD4-versus-QD8 confirmation study using five paired blocks (10 scheduled runs), with condition order counterbalanced across blocks and the same read-only file-based workload. Capture host state before every run.
4. Define and document the handling of anomalous runs before looking at new results. Do not delete inconvenient results; investigate, preserve, and report them.
5. Recalculate the results from parsed raw JSON, using the scripted analysis as the source of truth for future updates.

The current evidence justifies follow-up testing of the QD4/QD8 difference and the observed QD8 variability. It does not justify a claim of SSD saturation, a universal optimum queue depth, or a hardware-internal causal explanation.
