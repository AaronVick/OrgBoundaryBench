# Staged OrgBench Headline Report
Generated: 2026-03-08T14:36:05.856780+00:00

## Headline Table

| Arm | Metric | Value | 95% CI | n | Gate pass |
|-----|--------|-------|--------|---|-----------|
| math_governed | accuracy | 1.0000 | [1.0000, 1.0000] | 2 | False |
| plain_llm | accuracy | 0.5000 | [0.0000, 1.0000] | 2 | False |
| plain_llm_rag | accuracy | 0.5000 | [0.0000, 1.0000] | 2 | False |
| sham_complexity | accuracy | 0.5000 | [0.0000, 1.0000] | 2 | False |
| simple_graph | accuracy | 0.5000 | [0.0000, 1.0000] | 2 | False |

## Gate Summary
- Overall null/leverage gate pass: False
- Null audit: {"n_permutations": 100, "p_value": 0.55, "pass": false}
- Leverage audit: {"degree_cutoff_90pct": 1.0, "delta_full": 0.5, "delta_without_top_degree": 0.5, "delta_drop": 0.0, "pass": true}

## What Would Make This Look Good While Still Being Wrong?
- Leakage between train/test nodes or labels.
- Density/degree confounding that mimics governance gains.
- Label contamination from preprocessing choices.
- Extra orchestration gains misattributed to boundary math.

## Claim Status
DO NOT PROMOTE