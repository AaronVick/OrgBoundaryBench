# Staged OrgBench Headline Report
Generated: 2026-03-08T14:07:46.442747+00:00

## Headline Table

| Arm | Metric | Value | 95% CI | n | Gate pass |
|-----|--------|-------|--------|---|-----------|
| math_governed | accuracy | 0.2000 | [0.0000, 0.4000] | 5 | False |
| plain_llm | accuracy | 0.0000 | [0.0000, 0.0000] | 5 | False |
| plain_llm_rag | accuracy | 0.4000 | [0.0000, 0.8000] | 5 | False |
| sham_complexity | accuracy | 0.2000 | [0.0000, 0.4000] | 5 | False |
| simple_graph | accuracy | 0.0000 | [0.0000, 0.0000] | 5 | False |

## Gate Summary
- Overall null/leverage gate pass: False
- Null audit: {"n_permutations": 200, "p_value": 1.0, "pass": false}
- Leverage audit: {"degree_cutoff_90pct": 1.0, "delta_full": -0.2, "delta_without_top_degree": -0.2, "delta_drop": 0.0, "pass": false}

## What Would Make This Look Good While Still Being Wrong?
- Leakage between train/test nodes or labels.
- Density/degree confounding that mimics governance gains.
- Label contamination from preprocessing choices.
- Extra orchestration gains misattributed to boundary math.

## Claim Status
DO NOT PROMOTE