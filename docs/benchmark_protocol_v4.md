# Benchmark Protocol v4 — Queue-Depth Scaling Screen

## Purpose

Protocol v4 is the exploratory queue-depth scaling phase after the Protocol v3
QD1/QD2 confirmation study.

The question is:

> How does measured sequential-read throughput, latency, and repeatability change
> across QD1, QD2, QD4, and QD8 under the same file-based workload?

## Design

The initial screen uses three repeats of each queue-depth condition:

- QD1: 3 observations
- QD2: 3 observations
- QD4: 3 observations
- QD8: 3 observations
- Total: 12 FIO runs

Each block contains all four conditions exactly once. The order is predetermined and
counterbalanced across blocks.

This is a screening design, not a fully balanced crossover design. With only three
blocks, every condition cannot occupy every possible within-block position. The
schedule is nevertheless designed so that queue depth is not permanently tied to a
single position in the run sequence.

## Fixed workload

The workload remains unchanged from Protocol v3:

- file-based target only
- sequential read
- 128 KiB block size
- 256 MiB test size
- 10 second timed run
- direct I/O enabled
- Windowsaio
- explicit thread setting
- read-only
- no raw block-device target
- no destructive FIO option

Queue depth is the experimental factor.

## Predetermined schedule

Schedule ID: `v4-balanced-3rep-v1`

| Run order | Experiment | Condition | Replicate | Block | Within-block order |
|---:|---|---|---:|---:|---:|
| 1 | EXP025 | QD2 | 1 | 1 | 1 |
| 2 | EXP026 | QD8 | 1 | 1 | 2 |
| 3 | EXP027 | QD1 | 1 | 1 | 3 |
| 4 | EXP028 | QD4 | 1 | 1 | 4 |
| 5 | EXP029 | QD4 | 2 | 2 | 1 |
| 6 | EXP030 | QD1 | 2 | 2 | 2 |
| 7 | EXP031 | QD8 | 2 | 2 | 3 |
| 8 | EXP032 | QD2 | 2 | 2 | 4 |
| 9 | EXP033 | QD1 | 3 | 3 | 1 |
| 10 | EXP034 | QD4 | 3 | 3 | 2 |
| 11 | EXP035 | QD2 | 3 | 3 | 3 |
| 12 | EXP036 | QD8 | 3 | 3 | 4 |

## Host-state recording

Every Protocol v4 config must record:

- power_state
- background_activity
- system_update_state

The runner also captures a reproducibility-oriented host snapshot in the metadata
sidecar, including operating-system information, processor string, Python version,
CPU count, and target-volume free/total space before the run.

## Analysis

The screen will examine:

- IOPS / throughput versus queue depth
- mean latency versus queue depth
- run-to-run variability
- within-block contrasts
- whether QD4/QD8 introduce diminishing returns
- whether latency variability expands at higher queue depth
- whether anomalous runs require additional repeats

No predictive model should be built from this screen alone.

## Escalation rule

After the 12-run screen:

1. If QD4/QD8 show stable behavior and a clear response pattern, design the next
   confirmatory experiment around the observed scaling region.
2. If QD4 or QD8 shows high variability or anomalous latency, add targeted repeats
   before drawing conclusions.
3. Do not claim saturation, controller limits, NAND behavior, or production
   performance from this screen alone.
