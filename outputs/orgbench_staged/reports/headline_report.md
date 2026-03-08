# Staged OrgBench Headline Report
Generated: 2026-03-08T13:51:57.179924+00:00

## Headline Table

| Arm | Metric | Value | 95% CI | n | Gate pass |
|-----|--------|-------|--------|---|-----------|
| math_governed | accuracy | 0.3333 | [0.1667, 0.6479] | 12 | False |
| plain_llm | accuracy | 0.1667 | [0.0000, 0.4812] | 12 | False |
| plain_llm_rag | accuracy | 0.3333 | [0.1667, 0.6479] | 12 | False |
| sham_complexity | accuracy | 0.2500 | [0.0833, 0.5000] | 12 | False |
| simple_graph | accuracy | 0.1667 | [0.0000, 0.4812] | 12 | False |

## Gate Summary
- Overall null/leverage gate pass: False
- Null audit: {"n_permutations": 200, "p_value": 0.735, "pass": false}
- Leverage audit: {"degree_cutoff_90pct": 1.0, "delta_full": 0.0, "delta_without_top_degree": 0.0, "delta_drop": 0.0, "pass": false}

## What Would Make This Look Good While Still Being Wrong?
- Leakage between train/test nodes or labels.
- Density/degree confounding that mimics governance gains.
- Label contamination from preprocessing choices.
- Extra orchestration gains misattributed to boundary math.

## Claim Status
DO NOT PROMOTE