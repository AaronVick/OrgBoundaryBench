# Null Gate Diagnosis

- Source phase: `phase_01_n200`
- Observed delta (math - best baseline): `0.0`
- Permutation p-value: `0.488`
- Null gate pass: `False`

## Which null test failed

- The permutation null test in `run_null_and_leverage_audit` failed (`p > 0.05`).

## What drove failure

- Net advantage is zero (`wins=0`, `losses=0`, ties dominate), so permutation distribution is not separated from observed delta.

## Scientific appropriateness

- Appropriate. With non-positive observed effect, null gate should fail.

## Gate change analysis (old vs proposed)

| Gate element | Old | Proposed | Change rationale |
|---|---|---|---|
| Null superiority rule | `delta > 0` and `p <= 0.05` | **No change** | Failure is evidential, not a threshold artifact. |
