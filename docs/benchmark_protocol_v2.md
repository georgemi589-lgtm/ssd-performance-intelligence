# Benchmark Protocol v2

## Purpose

Protocol v2 is the controlled measurement protocol for the SSD performance
research phase. Its purpose is to characterize run-to-run measurement
variability before attributing performance differences to workload parameters.

## Scope

Current baseline workload:

- file-based target only
- sequential read
- 128 KiB block size
- 256 MiB test size
- 10 second timed run
- direct I/O enabled
- one explicit FIO thread setting
- queue depth is the experimental condition

## Replication design

The baseline characterization uses five repeats for each condition:

- QD1: 5 observations
- QD2: 5 observations

Runs should be interleaved rather than grouped entirely by condition. The
actual run order is recorded in each configuration.

## Required metadata

Every new executable experiment must contain:

- experiment_id: unique EXP### identifier
- protocol.version: "2"
- protocol.replicate_index: positive integer
- protocol.run_order: positive integer
- fio.name beginning with the experiment_id
- explicit fio.thread value
- objective and comparison notes

## Artifact policy

For every successful run:

1. Preserve the untouched FIO JSON.
2. Never overwrite an existing experiment artifact.
3. Preserve a metadata sidecar next to the raw JSON.
4. Keep missing values missing; do not reconstruct or impute raw benchmark
   fields.
5. Record the configuration used for the run.

## Analysis

For each condition report:

- n
- mean
- median
- sample standard deviation
- coefficient of variation
- minimum
- maximum
- latency percentiles when present
- run order

The first objective is repeatability characterization. QD4/QD8 should not be
introduced until the QD1/QD2 baseline has been characterized under this
protocol.

## Interpretation rule

A difference between two workload conditions is not treated as a causal
effect of queue depth when the observed difference can reasonably be
confounded by run-to-run measurement variability.

This protocol supports descriptive experimental analysis. It does not by
itself establish population-level inference or production readiness.
