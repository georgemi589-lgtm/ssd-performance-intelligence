# Protocol v3 QD1/QD2 Confirmation Analysis

## Purpose

Protocol v3 was designed to test whether the large QD2-versus-QD1 throughput difference
observed in Protocol v2 remained visible after correcting the main experimental-design
limitation: QD1 and QD2 were previously aligned with odd/even run-order parity.

Protocol v3 used five paired blocks. Each block contained one QD1 and one QD2 run, and
the within-block order was counterbalanced across blocks.

## Final dataset

| Block | Run order | Experiment | Condition | IOPS | Bandwidth (B/s) | Mean latency (µs) | Within-block order |
|---:|---:|---|---|---:|---:|---:|---:|
| 1 | 1 | EXP015 | QD2 | 4729.5 | 619908569 | 419.2 | 1 |
| 1 | 2 | EXP016 | QD1 | 2534.0 | 332142555 | 392.2 | 2 |
| 2 | 3 | EXP017 | QD1 | 2551.5 | 334436085 | 389.6 | 1 |
| 2 | 4 | EXP018 | QD2 | 4814.9 | 631100998 | 412.4 | 2 |
| 3 | 5 | EXP019 | QD2 | 4810.1 | 630471916 | 412.8 | 1 |
| 3 | 6 | EXP020 | QD1 | 2564.6 | 336152957 | 387.6 | 2 |
| 4 | 7 | EXP021 | QD1 | 2432.3 | 318800759 | 408.7 | 1 |
| 4 | 8 | EXP022 | QD2 | 4861.1 | 637155919 | 408.7 | 2 |
| 5 | 9 | EXP023 | QD2 | 3934.6 | 515716748 | 496.3 | 1 |
| 5 | 10 | EXP024 | QD1 | 1874.7 | 245722320 | 528.1 | 2 |

The runner preserved a raw FIO JSON artifact and metadata sidecar for each Protocol v3
run. The v3 dataset uses the same file-based sequential-read workload as the baseline:
128 KiB blocks, 256 MiB size, 10 second timed run, direct I/O, Windowsaio, and explicit
thread setting.

## Descriptive statistics

| Condition | n | Mean IOPS | Median IOPS | Sample SD | CV | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| QD1 | 5 | 2391.42 | 2534.0 | 293.52 | 12.27% | 1874.7 | 2564.6 |
| QD2 | 5 | 4630.04 | 4810.1 | 391.64 | 8.46% | 3934.6 | 4861.1 |

For bandwidth:

| Condition | Mean BW (B/s) | Sample SD | CV |
|---|---:|---:|---:|
| QD1 | 313450935.2 | 38473760.2 | 12.27% |
| QD2 | 606870830.0 | 51333099.0 | 8.46% |

For mean total latency:

| Condition | Mean latency (µs) | Sample SD | CV |
|---|---:|---:|---:|
| QD1 | 421.24 | 60.32 | 14.32% |
| QD2 | 429.88 | 37.32 | 8.68% |

## Matched-block comparison

For each block, define the paired IOPS difference as:

QD2 IOPS − QD1 IOPS.

| Block | QD1 IOPS | QD2 IOPS | Difference | QD2/QD1 |
|---:|---:|---:|---:|---:|
| 1 | 2534.0 | 4729.5 | +2195.5 | 1.87× |
| 2 | 2551.5 | 4814.9 | +2263.4 | 1.89× |
| 3 | 2564.6 | 4810.1 | +2245.5 | 1.88× |
| 4 | 2432.3 | 4861.1 | +2428.8 | 2.00× |
| 5 | 1874.7 | 3934.6 | +2059.9 | 2.10× |

All five matched blocks show QD2 above QD1.

The mean paired difference is **2238.62 IOPS** with a sample SD of **132.88 IOPS**. The
mean QD2 throughput is approximately **93.6% higher** than the mean QD1 throughput in
this Protocol v3 dataset.

The pairwise differences are all positive and fall between 2059.9 and 2428.8 IOPS.
Their coefficient of variation is approximately **5.94%**, which is substantially
tighter than the earlier Protocol v2 QD1 variability.

These are descriptive paired-design results, not a claim about all SSDs, all systems,
or a population-level causal effect.

## Run-order counterbalancing

Protocol v3 did not repeat the Protocol v2 odd/even confounding.

QD2 was first within blocks 1, 3, and 5 and second within blocks 2 and 4.
QD1 was first within blocks 2 and 4 and second within blocks 1, 3, and 5.

Therefore, condition is no longer perfectly aligned with within-block order. This is a
material design improvement over Protocol v2.

The final block still shows lower throughput for both conditions than most earlier
blocks, so system-state/time variation remains visible. Importantly, the QD2-versus-QD1
gap persists in that final block.

## Interpretation

The Protocol v3 confirmation experiment provides substantially stronger evidence than
Protocol v2 that the QD2 condition is associated with higher sequential-read throughput
under this particular file-based workload and host.

The key evidence is not just the group means. QD2 exceeds QD1 in all five matched blocks,
the condition order is counterbalanced, and the paired differences are relatively
consistent.

At the same time, the result should remain bounded:

- This is one host and one SSD/test-file environment.
- The benchmark is file-based and read-only; it does not directly measure NAND-level
  behavior, controller internals, or production workload performance.
- The experiment establishes a strong workload-level observation, not a universal SSD
  law.
- Host state was captured by the Protocol v3 runner, but this report does not infer
  causal effects from unobserved host variables.

## Decision

The evidence is now sufficient to justify an exploratory **queue-depth scaling phase**
including QD4 and QD8.

The next phase should not reuse the fixed v3 schedule. It should use a randomized or
counterbalanced design across **QD1, QD2, QD4, and QD8**, preserving the same workload
definition and safety constraints.

A sensible next stage is an initial three-repeat screening design (12 total runs):
three randomized/counterbalanced blocks containing all four conditions. If QD4 or QD8
shows materially higher variability, saturation, or anomalous latency behavior, those
conditions should receive additional repeats before modeling.

No production-readiness or NAND-level conclusion is supported by the present data.
