# Leverage Gate Diagnosis

- Source phase: `phase_01_n200`
- Degree cutoff (90th pct): `1.0`
- delta_full: `0.0`
- delta_without_top_degree: `0.0`
- leverage pass: `False`

## Diagnosis

- Failure is primarily due to no positive advantage (`delta_without_top_degree <= 0`).
- Additional design issue: degree is near-constant in this normalized kernel, so top-degree slicing is weakly informative.

## Scientifically appropriate?

- Yes for this run (no positive effect should fail).
- But leverage slice construction should be improved to test sensitivity meaningfully on normalized kernels.

## Gate change analysis (old vs proposed)

| Gate element | Old | Proposed | Change rationale |
|---|---|---|---|
| Leverage slice definition | Top 10% by normalized degree from task table | Top 10% by pre-normalization weighted degree (or centrality) | Avoid degenerate all-equal degree slicing. |
| Pass rule | `delta_reduced > 0` and `delta_drop <= 0.03` | **No threshold change**; keep same pass rule | Preserve strictness; only fix slice validity. |
