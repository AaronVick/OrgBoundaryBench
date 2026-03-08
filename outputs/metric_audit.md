# Metric Audit

- Source phase: `phase_01_n200`
- Headline metric: `accuracy`

## Current metric behavior

- math_governed: `0.25`
- best baseline: `0.25`
- delta: `0.0`

## Audit findings

- Current weighting effectively flattens differences because only label-accuracy style metrics are scored for this task family.
- Governance quality dimensions (provenance completeness, challengeability, reversibility quality, responsibility clarity) are not part of the measured objective here.
- Result: benchmark currently rewards generic label fluency and routing priors more than structural governance quality.

See ablation table: `outputs/metric_ablation_table.csv`
