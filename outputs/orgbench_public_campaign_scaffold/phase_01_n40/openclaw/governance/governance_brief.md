# OpenClaw Governance Brief
Generated: 2026-03-08T14:36:05.953007+00:00

Recommendation: **BLOCK_DEPLOYMENT**
Operating mode: `blocked`

## Hard failures
- gate_failed
- sample_size_too_small

## Soft failures
- ci_too_wide

## Required remediations
- [BLOCKING] gate_failed: Do not deploy. Re-run staged arms and pass null+leverage gates with preregistered thresholds. (owner: research_lead)
- [BLOCKING] sample_size_too_small: Increase task count per arm to policy minimum before deployment decision. (owner: benchmark_operator)
- [NON-BLOCKING] ci_too_wide: Increase evaluation sample and bootstrap stability to narrow uncertainty intervals. (owner: benchmark_operator)
