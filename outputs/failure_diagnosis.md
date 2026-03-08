# Failure Diagnosis (Live Artifact Audit)

- Campaign source: `outputs/orgbench_public_campaign_opus46_n200/campaign_summary.json`
- Phase: `phase_01_n200`
- Best baseline arm: `sham_complexity`
- Test tasks: `32`

## Root-cause matrix

| Candidate source | Verdict | Evidence (live artifacts) |
|---|---|---|
| Dataset/task weakness | YES | Single task family (`node_label_classification`) with high label cardinality; governance/reversibility features are not in task target. |
| Metric weakness | PARTIAL | Accuracy/macro-F1/balanced_accuracy are measured; governance quality metrics are not measured in this harness. |
| Arm implementation weakness | YES | `math_governed` uses `spectral_fallback_large_n` at n=200 and ties sham (`0.25` vs `0.25`). |
| Sham/plain baseline too strong | NO | Best baseline is only `0.25`; failure is from no positive delta, not from an exceptionally strong baseline. |
| Aaron stack not affecting decisions enough | YES | Aaron-specific context is present, but net gain is zero (wins and losses offset). |
| Null suite too hard / malformed | NO (null), PARTIAL (leverage design) | Null gate appropriately fails with non-positive effect; leverage slice is degenerate on normalized-degree tasks. |
| Leverage sensitivity driven by a few tasks | NO | Degree cutoff equals 1.0; reduced set degenerates, so no specific high-degree slice is isolated. |
| Simple absence of real advantage | YES | `delta_vs_best = 0.0`, null fail (`p=0.488`), governance `BLOCK_DEPLOYMENT`. |

## Task-level outcome counts (math_governed vs best baseline)

- Math advantage tasks: `0`
- Math underperformed tasks: `0`
- Tied correct tasks: `8`
- Tied wrong tasks: `24`
- Output changed by math path: `9/32`
- Changed to correct: `0`
- Changed to wrong: `0`
- Changed but still wrong: `9`

## Hard conclusion

Current failure is predominantly **absence of measurable real advantage** on this public task formulation. The Aaron path is active but not producing net empirical lift over the best baseline under preregistered gates.

Supporting table: `outputs/failure_case_table.csv`
