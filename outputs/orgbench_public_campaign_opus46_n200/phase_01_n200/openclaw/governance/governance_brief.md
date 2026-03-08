# OpenClaw Governance Brief
Generated: 2026-03-08T14:59:44.403500+00:00

Recommendation: **BLOCK_DEPLOYMENT**
Operating mode: `blocked`

## Hard failures
- gate_failed
- math_not_better_than_sham

## Soft failures
- none

## Required remediations
- [BLOCKING] gate_failed: Do not deploy. Re-run staged arms and pass null+leverage gates with preregistered thresholds. (owner: research_lead)
- [BLOCKING] math_not_better_than_sham: No governance deployment claim allowed until math_governed beats sham_complexity by configured minimum delta. (owner: research_lead)
