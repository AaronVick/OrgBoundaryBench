# Staged OrgBench Headline Report
Generated: 2026-03-08T14:59:44.287884+00:00

## Headline Table

| Arm | Metric | Value | 95% CI | n | Gate pass |
|-----|--------|-------|--------|---|-----------|
| math_governed | accuracy | 0.2500 | [0.1242, 0.4062] | 32 | False |
| plain_llm | accuracy | 0.1250 | [0.0305, 0.2500] | 32 | False |
| plain_llm_rag | accuracy | 0.1250 | [0.0305, 0.2500] | 32 | False |
| sham_complexity | accuracy | 0.2500 | [0.1242, 0.4062] | 32 | False |
| simple_graph | accuracy | 0.1250 | [0.0305, 0.2500] | 32 | False |

## Gate Summary
- Overall null/leverage gate pass: False
- Null audit: {"n_permutations": 500, "p_value": 0.488, "pass": false}
- Leverage audit: {"degree_cutoff_90pct": 1.0, "delta_full": 0.0, "delta_without_top_degree": 0.0, "delta_drop": 0.0, "pass": false}

## What Would Make This Look Good While Still Being Wrong?
- Leakage between train/test nodes or labels.
- Density/degree confounding that mimics governance gains.
- Label contamination from preprocessing choices.
- Extra orchestration gains misattributed to boundary math.

## Claim Status
DO NOT PROMOTE