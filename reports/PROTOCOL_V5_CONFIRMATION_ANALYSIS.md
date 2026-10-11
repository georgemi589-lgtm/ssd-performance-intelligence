# Protocol v5 — Paired QD4/QD8 Confirmation Analysis

## Artifact audit

All ten scheduled configs, raw JSON artifacts, and metadata sidecars passed validation. The repository FIO parser successfully parsed every raw artifact. Each run had one job, a matching job name and requested queue depth, no reported job error, and no write I/O reported.

FIO versions: fio-3.43.
All ten artifacts report fio-3.43.

## Design and workload

Five paired blocks compare QD4 with QD8 under a file-based sequential-read workload. The configured workload is 128 KiB block size, 256 MiB test size, 10-second timed run, direct I/O, Windowsaio, and thread=1, using the same test file. The condition order is prespecified and counterbalanced but not randomized.

## Scheduled observations

| Run | Experiment | Block | Position | Condition | FIO version | IOPS | Bandwidth (B/s) | Mean latency (µs) |
|---:|---|---:|---:|---|---|---:|---:|---:|
| 1 | EXP037 | 1 | 1 | QD8 | fio-3.43 | 6010.3 | 787781771 | 1308.6 |
| 2 | EXP038 | 1 | 2 | QD4 | fio-3.43 | 5532.9 | 725214390 | 710.0 |
| 3 | EXP039 | 2 | 1 | QD4 | fio-3.43 | 5559.4 | 728687451 | 707.9 |
| 4 | EXP040 | 2 | 2 | QD8 | fio-3.43 | 5355.9 | 702012301 | 1470.2 |
| 5 | EXP041 | 3 | 1 | QD4 | fio-3.43 | 5491.1 | 719723022 | 714.6 |
| 6 | EXP042 | 3 | 2 | QD8 | fio-3.43 | 5946.5 | 779421050 | 1317.5 |
| 7 | EXP043 | 4 | 1 | QD8 | fio-3.43 | 5456.4 | 715182403 | 1436.9 |
| 8 | EXP044 | 4 | 2 | QD4 | fio-3.43 | 5391.3 | 706643345 | 724.5 |
| 9 | EXP045 | 5 | 1 | QD4 | fio-3.43 | 5501.5 | 721099141 | 712.4 |
| 10 | EXP046 | 5 | 2 | QD8 | fio-3.43 | 4840.5 | 634457630 | 1633.2 |

## Condition-level descriptive statistics

| Condition | n | Mean IOPS | Median IOPS | Sample SD IOPS | IOPS CV | Mean bandwidth (MB/s) | Mean latency (µs) | Latency CV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QD4 | 5 | 5495.3 | 5501.5 | 64.1 | 1.17% | 720.27 | 713.9 | 0.90% |
| QD8 | 5 | 5521.9 | 5456.4 | 478.3 | 8.66% | 723.77 | 1433.3 | 9.25% |

## Paired comparison

Primary outcome: D = IOPS(QD4) − IOPS(QD8). Positive values favor QD4; negative values favor QD8.

| Block | QD4 experiment | QD4 IOPS | QD8 experiment | QD8 IOPS | D (QD4−QD8) | D relative to QD8 |
|---:|---|---:|---|---:|---:|---:|
| 1 | EXP038 | 5532.9 | EXP037 | 6010.3 | -477.4 | -7.94% |
| 2 | EXP039 | 5559.4 | EXP040 | 5355.9 | +203.5 | +3.80% |
| 3 | EXP041 | 5491.1 | EXP042 | 5946.5 | -455.5 | -7.66% |
| 4 | EXP044 | 5391.3 | EXP043 | 5456.4 | -65.1 | -1.19% |
| 5 | EXP045 | 5501.5 | EXP046 | 4840.5 | +661.0 | +13.66% |

- Mean paired difference: **-26.7 IOPS**.
- Median paired difference: **-65.1 IOPS**.
- Sample SD of paired differences: **478.1 IOPS**.
- Blocks with QD4 higher than QD8: **2/5**.

## Interpretation and limitations

These are descriptive results from one host and one file-based sequential-read workload. Five pairs are a small confirmation study, not population-level proof. The paired design helps compare nearby runs but cannot remove all time-varying host-state or environmental effects.

Do not attribute the observed differences to NAND, controller behavior, firmware, saturation, thermal throttling, or production performance without direct evidence for those mechanisms.

Two accidental duplicate commands occurred after the scheduled EXP034 artifact was saved during Protocol v4. Their unsaved results are excluded from the v4 ledger, but the extra reads may have affected the host state before subsequent v4 runs. This limitation remains documented in the v4 report.

## Decision

Use the paired direction, condition variability, latency, artifact metadata, and FIO version consistency to decide whether the Protocol v4 pattern was reproduced. If the paired direction is mixed or variability remains high, classify the result as inconclusive and gather further controlled observations. Do not train a predictive model from this small study alone.
