# Benchmark Protocol v5 — Paired QD4/QD8 Confirmation

## Purpose

Protocol v5 follows the Protocol v4 queue-depth scaling screen. Protocol v4 showed higher mean IOPS at QD4 than QD8, while QD8 had notably higher observed mean latency and run-to-run variability. The purpose of v5 is to check whether the QD4/QD8 difference persists in a new, paired, counterbalanced set of runs.

The confirmatory question is:

> Under the same file-based sequential-read workload, does QD4 continue to have higher throughput and lower mean latency than QD8 across paired blocks, and is QD8 variability still materially higher?

This protocol is confirmatory for the observed QD4/QD8 pattern, but five pairs on one host remain a small, host-specific study. It cannot establish a universal SSD performance law.

## Predetermined design

- Five paired blocks; each block contains one QD4 run and one QD8 run.
- Ten scheduled FIO runs total: five observations for each condition.
- Within-block order is counterbalanced as evenly as possible: QD8 runs first in blocks 1 and 4; QD4 runs first in blocks 2, 3, and 5.
- Schedule ID: `v5-qd4-qd8-paired-5block-v1`
- Configurations: `configs/exp037.yaml` through `configs/exp046.yaml`.
- The schedule and condition order must not be changed after results are observed.

This is counterbalanced, not randomized. It is not a fully balanced crossover, because five pairs require one condition to be first in one more block than the other. The order is prespecified to avoid always running one condition first.

## Fixed workload

Keep the workload the same as Protocol v4:

- file-based target only: `C:\\fio-lab\\exp001_testfile.bin`
- sequential read only (`rw=read`)
- block size: 128 KiB
- configured test size: 256 MiB
- timed runtime: 10 seconds
- direct I/O enabled
- I/O engine: `windowsaio`
- explicit `thread=1`
- queue depth is the only configured workload factor: QD4 (`iodepth=4`) or QD8 (`iodepth=8`)
- no raw block-device target, write workload, TRIM, or destructive options

Do not replace, resize, recreate, or move the test file during the protocol.

## Prespecified run schedule

| Run order | Experiment | Condition | Replicate | Block | Within-block order |
|---:|---|---|---:|---:|---:|
| 1 | EXP037 | QD8 | 1 | 1 | 1 |
| 2 | EXP038 | QD4 | 1 | 1 | 2 |
| 3 | EXP039 | QD4 | 2 | 2 | 1 |
| 4 | EXP040 | QD8 | 2 | 2 | 2 |
| 5 | EXP041 | QD4 | 3 | 3 | 1 |
| 6 | EXP042 | QD8 | 3 | 3 | 2 |
| 7 | EXP043 | QD8 | 4 | 4 | 1 |
| 8 | EXP044 | QD4 | 4 | 4 | 2 |
| 9 | EXP045 | QD4 | 5 | 5 | 1 |
| 10 | EXP046 | QD8 | 5 | 5 | 2 |

## Run procedure

1. Use the same laptop, power connection/power mode, test file, and benchmark setup throughout the study where practical. Record the actual observed host state for every run; never copy a state value if it is no longer true.
2. Do not run a benchmark when a system update is in progress or the machine is obviously busy with a large background task. If a pair is postponed, postpone the pair rather than selectively rerunning one condition.
3. Before each run, fill all three `host_state` fields in that experiment's YAML config: `power_state`, `background_activity`, and `system_update_state`. Leave no `REPLACE_WITH_ACTUAL_STATE` placeholder.
4. Use the dry-run first. Confirm the experiment ID, target file, `rw=read`, expected queue depth, and output destination. Only then execute the scheduled run.
5. Allow the host to sit idle for at least 60 seconds between scheduled runs, including between the two runs within a pair. Apply the same interval to every run.
6. Run each experiment ID once. Never use `--overwrite` for these scheduled experiments.
7. If validation fails before FIO starts, correct the config and retry after checking that no artifacts were created. If FIO starts but fails, or if an output/metadata error appears, stop and report it; do not immediately repeat the command.
8. Preserve every completed JSON artifact and metadata sidecar. Do not discard an anomalous observation because it disagrees with the expected pattern.

## Outcomes and analysis plan

The primary outcome is within-block IOPS difference:

`D_b = IOPS(QD4)_b - IOPS(QD8)_b`

For the five paired blocks, report each pair difference, the mean paired difference, median paired difference, sample standard deviation, and the number of blocks with QD4 above QD8. Also report condition-specific IOPS, bandwidth, and mean latency summaries with sample standard deviations and coefficients of variation.

With only five pairs, results remain descriptive. Do not rely on normality assumptions or present the study as population-level proof. Inspect the raw JSON and metadata before calculating summary statistics.

## Prespecified interpretation rules

- If QD4 exceeds QD8 in most or all pairs and QD8 continues to show higher variability/latency, treat the v4 pattern as supported on this host/workload and consider a later targeted investigation into host-state effects.
- If the paired direction is mixed or the differences are small relative to within-condition variability, report the result as inconclusive and design additional repeats before escalating.
- If either condition has a clear operational anomaly, preserve it, inspect metadata and raw FIO output, and report both the original result and any documented follow-up. Do not silently exclude the run.
- Do not claim SSD saturation, controller limits, NAND behavior, thermal throttling, or production readiness without evidence that directly tests those mechanisms.

## Research integrity note

Two accidental duplicate commands were invoked after the scheduled EXP034 result had already been saved. The runner rejected the duplicate outputs after FIO invocation; the unsaved outputs are excluded from the v4 ledger and may have affected host state before later runs. The runner has since been changed to check raw and metadata artifact paths before invoking FIO. This v5 protocol is intended to validate the QD4/QD8 observation under a prespecified, paired schedule, not to erase the documented v4 deviation.
