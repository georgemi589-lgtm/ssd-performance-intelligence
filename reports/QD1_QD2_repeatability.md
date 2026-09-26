# QD1/QD2 repeatability analysis

This report records the first repeatability check for the SSD Performance Intelligence prototype.

## Dataset

| Experiment | Requested QD | IOPS | Bandwidth (B/s) | Mean total latency (µs) |
|---|---:|---:|---:|---:|
| EXP001 | 1 | 4823.318 | 632201893 | 205.254 |
| EXP003 | 1 | 2368.100 | 310386778 | 417.000 |
| EXP002 | 2 | 4332.267 | 567838870 | 440.430 |
| EXP004 | 2 | 4484.700 | 587812245 | 429.900 |

EXP001 and EXP002 are preserved as documented observations because their original raw artifacts were overwritten by subsequent repeat runs. EXP003 and EXP004 remain available as local raw JSON artifacts.

## Descriptive variability

| Condition | Metric | Mean | Sample SD | CV |
|---|---|---:|---:|---:|
| QD1 | IOPS | 3595.709 | 1736.101 | 48.283% |
| QD2 | IOPS | 4408.483 | 107.787 | 2.445% |
| QD1 | Bandwidth | 471294335.5 B/s | 227557650.1 B/s | 48.284% |
| QD2 | Bandwidth | 577825557.5 B/s | 14123308.9 B/s | 2.444% |
| QD1 | Mean total latency | 311.127 µs | 149.727 µs | 48.124% |
| QD2 | Mean total latency | 435.165 µs | 7.446 µs | 1.711% |

These are sample standard deviations from only two observations per condition.

## Interpretation

The two QD1 runs show much larger run-to-run variation than the two QD2 runs. Therefore, the earlier one-run observation cannot be interpreted as evidence that queue depth 2 inherently reduces or increases SSD performance.

The useful finding at this stage is methodological: measurement variability itself must be characterized before attributing a performance difference to workload parameters.

No population-level conclusion is drawn from these four observations.

## Missing values

Complete latency percentile data are not available in the retained console summaries for EXP003 and EXP004. Those fields are left blank rather than reconstructed or imputed.

## Next protocol refinement

Before expanding to QD4/QD8, tighten the baseline measurement protocol: retain each raw artifact under a unique experiment ID, explicitly use the Windows thread option to remove the observed FIO mutex warning, keep the read-only workload unchanged, and collect multiple repeats per condition.
