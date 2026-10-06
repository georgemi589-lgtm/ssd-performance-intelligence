# Benchmark Protocol v3

## Purpose

Protocol v3 is the next confirmation experiment after the Protocol v2 baseline. Its
purpose is to reduce confounding between queue depth and run order/system state.

## What changed from Protocol v2

Protocol v2 used an interleaved odd/even sequence. That meant every QD1 run had an
odd run order and every QD2 run had an even run order. The two conditions were
therefore perfectly aligned with run-order parity.

Protocol v3 replaces that pattern with five paired blocks. Each block contains one
QD1 run and one QD2 run, but the order inside each block is counterbalanced across
the five blocks.

## Fixed workload

The workload remains unchanged:

- file-based target only
- sequential read
- 128 KiB block size
- 256 MiB test size
- 10 second timed run
- direct I/O enabled
- explicit FIO thread setting
- QD1 or QD2 as the experimental condition
- no destructive operation
- no raw block-device target

## Schedule

The schedule is predetermined before new measurements are collected.

| Run order | Experiment | Condition | Replicate | Block | Within-block order |
|---:|---|---|---:|---:|---:|
| 1 | EXP015 | QD2 | 1 | 1 | 1 |
| 2 | EXP016 | QD1 | 1 | 1 | 2 |
| 3 | EXP017 | QD1 | 2 | 2 | 1 |
| 4 | EXP018 | QD2 | 2 | 2 | 2 |
| 5 | EXP019 | QD2 | 3 | 3 | 1 |
| 6 | EXP020 | QD1 | 3 | 3 | 2 |
| 7 | EXP021 | QD1 | 4 | 4 | 1 |
| 8 | EXP022 | QD2 | 4 | 4 | 2 |
| 9 | EXP023 | QD2 | 5 | 5 | 1 |
| 10 | EXP024 | QD1 | 5 | 5 | 2 |

Schedule seed: `2026-10-06-balanced-v1`.

The seed documents the schedule-generation decision. The exact schedule above is
the source of truth for execution order.

## Host-state recording

Every Protocol v3 config must include:

- power_state
- background_activity
- system_update_state

The runner also captures a reproducibility-oriented host snapshot in the metadata
sidecar: operating-system information, processor string, Python version, CPU count,
and target-volume free/total space before the FIO run.

Do not record host identity or other unnecessary personal information.

## Artifact policy

For every successful run:

1. Preserve untouched FIO JSON.
2. Never overwrite an experiment artifact.
3. Preserve the metadata sidecar.
4. Preserve the exact configuration used.
5. Keep missing values missing; never reconstruct benchmark fields.

## Interpretation

Protocol v3 remains descriptive. A QD1/QD2 difference is not treated as a causal
effect unless the observed pattern remains credible after considering run order,
host state, and repeatability.

QD4/QD8 should not be introduced simply because Protocol v2 showed a large mean
difference. The decision should follow the Protocol v3 evidence review.
