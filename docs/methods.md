# Methods checklist (for future experiments)

When an experiment is added under `experiments/`, record at least:

1. Git commit hash and config filename
2. Dataset identifier and content hash
3. Hardware and OS context (device model if known; otherwise “unknown”)
4. Train / validation / test split rule
5. Baseline definition
6. Metrics and uncertainty (e.g. multiple seeds or time-based splits)
7. Negative results and known confounds

Until that record exists, treat any numeric claim as unsupported.
