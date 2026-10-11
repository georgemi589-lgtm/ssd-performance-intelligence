# Benchmark Protocol v6 — 4 KiB Sequential-Read QD4/QD8 Study

## Purpose

Protocol v5 compared QD4 and QD8 with 128 KiB sequential reads. It showed nearly identical average IOPS but approximately twice the mean total latency at QD8, along with greater throughput variability. Protocol v6 asks whether the observed latency trade-off also appears with a smaller 4 KiB sequential-read request size.

Research question:

> Under a 4 KiB file-based sequential-read workload, how do QD4 and QD8 compare in IOPS, bandwidth, completion latency, tail latency, and run-to-run variability?

This study changes the configured block size from 128 KiB to 4 KiB while keeping the other specified workload settings fixed. It does not directly measure physical NAND latency, controller behavior, or production workload performance.

## Design

- Five paired blocks; every block contains one QD4 run and one QD8 run.
- Ten scheduled runs total, five per condition.
- Prespecified counterbalanced order:
  - Block 1: QD8 first, then QD4.
  - Block 2: QD4 first, then QD8.
  - Block 3: QD4 first, then QD8.
  - Block 4: QD8 first, then QD4.
  - Block 5: QD4 first, then QD8.
- Schedule ID: `v6-4k-seq-qd4-qd8-paired-5block-v1`
- Configurations: `configs/exp047.yaml` through `configs/exp056.yaml`.

This is counterbalanced, not randomized. Since there are five blocks, one condition must appear first in one more block than the other. The condition order is fixed in advance and must not be changed after the study starts.

## Fixed workload

- Target: file-based `C:\fio-lab\exp001_testfile.bin`
- Operation: sequential read only (`rw=read`)
- Block size: 4 KiB (`bs=4k`)
- Configured test size: 256 MiB
- Runtime: 10 seconds, time-based
- Direct I/O: enabled
- I/O engine: `windowsaio`
- Thread: explicitly set to 1
- Queue-depth conditions: QD4 (`iodepth=4`) and QD8 (`iodepth=8`)
- No raw block-device access, writes, TRIM, or destructive benchmark options.

Use the same existing test file for every run. Do not recreate, resize, replace, or move it during this protocol. This remains a file-based host-level experiment, not a raw-device test.

## Prespecified schedule

| Run order | Experiment | Condition | Replicate | Block | Within-block order |
|---:|---|---|---:|---:|---:|
| 1 | EXP047 | QD8 | 1 | 1 | 1 |
| 2 | EXP048 | QD4 | 1 | 1 | 2 |
| 3 | EXP049 | QD4 | 2 | 2 | 1 |
| 4 | EXP050 | QD8 | 2 | 2 | 2 |
| 5 | EXP051 | QD4 | 3 | 3 | 1 |
| 6 | EXP052 | QD8 | 3 | 3 | 2 |
| 7 | EXP053 | QD8 | 4 | 4 | 1 |
| 8 | EXP054 | QD4 | 4 | 4 | 2 |
| 9 | EXP055 | QD4 | 5 | 5 | 1 |
| 10 | EXP056 | QD8 | 5 | 5 | 2 |

## Run procedure

1. Before every run, observe and record the actual power state, background activity, and system-update state. Never assume these are unchanged from a previous run.
2. Do not run while a system update is in progress or the machine is obviously busy with a large background task. If one run is delayed for such a reason, postpone its paired run too rather than selectively rerunning a single condition.
3. Replace the three `host_state` placeholders in each YAML config before using it.
4. Run the dry-run first. Check the experiment ID, target path, read-only setting, `bs=4k`, queue depth, runtime, and output destination.
5. Allow at least 60 seconds of idle time between scheduled runs. Apply the same wait rule consistently.
6. Run each experiment ID once. Do not use `--overwrite`.
7. If an executable run produces an error, stop and report the exact message before attempting another execution.
8. Preserve every successful raw JSON artifact and metadata sidecar, including outliers. Do not silently remove results because they conflict with the earlier pattern.

## Outcomes and analysis

The primary outcome is the within-block IOPS difference:

`D_b = IOPS(QD4)_b - IOPS(QD8)_b`

Report every pair difference, mean and median pair difference, sample standard deviation of pair differences, and number of blocks where QD4 is faster. Also report per-condition IOPS, bandwidth, mean completion latency, mean total latency, P50/P95/P99/P99.9 completion-latency percentiles, and run-to-run variability.

Average per-run percentiles are not the same as percentiles computed over pooled requests. Keep those interpretations separate.

## Interpretation rules

- If QD8 again has similar average IOPS but substantially higher completion and tail latency, the latency trade-off is observed at both 128 KiB and 4 KiB sequential reads on this host. That still would not establish generalization to other workloads or systems.
- If the throughput or latency comparison changes at 4 KiB, report the block-size-dependent pattern and do not label either condition universally optimal.
- If the pairwise direction varies or run-to-run variability is high, treat the result as inconclusive and consider more controlled observations before escalation.
- Inspect FIO versions, raw artifacts, metadata, and achieved queue-depth distributions before interpreting the result.
- Do not infer controller limits, NAND service time, saturation, thermal throttling, or production readiness without evidence that directly tests those mechanisms.

## Limitations

The study contains five pairs on one host and one file-based target. Protocol v5 used 128 KiB blocks; v6 uses 4 KiB blocks, so absolute performance figures should not be compared as if block size were unchanged. Differences between v5 and v6 may reflect the workload-size change and its interaction with queue depth.

Do not train a predictive model from these experiments alone. This protocol is a controlled exploratory comparison intended to test a specific workload-transfer question.
