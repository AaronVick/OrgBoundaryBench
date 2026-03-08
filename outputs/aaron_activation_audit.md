# Aaron Stack Activation Audit

- Source phase: `phase_01_n200`
- Math run id: `20260308T145647Z_math_governed`

## Boundary / partition activation

- boundary_mode values: `['spectral_fallback_large_n']`
- boundary_block values on test tasks: `[0, 1]`
- q_non_trivial values: `[1]`

## Governance trigger instrumentation (from live context keys)

| Trigger | Observed in artifacts |
|---|---|
| provenance sufficiency trigger | NOT_INSTRUMENTED |
| reversibility trigger | NOT_INSTRUMENTED |
| contestability trigger | NOT_INSTRUMENTED |
| misalignment trigger | NOT_INSTRUMENTED |
| drift trigger | NOT_INSTRUMENTED |

## Did triggers change final output/recommendation?

- Output changed by math path: `9/32`
- Changed to correct: `0`
- Changed to wrong: `0`
- Governance recommendation: `BLOCK_DEPLOYMENT`

Plain statement: The current Aaron stack influences context construction, but the governance-specific triggers above are not materially wired into per-task decision changes in this harness.
