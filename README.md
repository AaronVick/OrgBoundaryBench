# OrgBoundaryBench

Public benchmark harness for evaluating whether governed organizational AI behavior is better than plain model use under strict falsification gates.

Repository: [https://github.com/AaronVick/OrgBoundaryBench](https://github.com/AaronVick/OrgBoundaryBench)

## Current status (hard-gate)

Latest public mapping run status:

- nontrivial boundary map: `PASS`
- governance preservation: `PASS`
- external agreement: `FAIL`
- stress robustness: `FAIL`
- null/rival dominance: `FAIL`
- temporal drift validation: `PASS` (completed)
- organizational-design claim: `LOCKED`

The benchmark is in progress. No superiority or organizational-design claim is currently unlocked.

## Experimental protocol (academic format)

Each release candidate is evaluated with the same test families:

1. Nontrivial boundary recovery
2. External agreement against known labels
3. Stress robustness and leverage sensitivity
4. Null/rival dominance with uncertainty
5. Temporal drift coherence
6. Governance-preservation mapping

Core external metrics:

- NMI
- ARI
- macro-F1 (best block-label matching)
- block count / block balance
- bootstrap confidence intervals for dominance gap `D`

A claim is unlocked only if all required gates pass in the same run.

## Reproducible outputs

Primary run artifacts:

- [outputs/org_design_map_stage_n120/organizational_design_map_report.md](outputs/org_design_map_stage_n120/organizational_design_map_report.md)
- [outputs/org_design_map_stage_n120/boundary_leaderboard.csv](outputs/org_design_map_stage_n120/boundary_leaderboard.csv)
- [outputs/org_design_map_stage_n120/external_agreement_report.md](outputs/org_design_map_stage_n120/external_agreement_report.md)
- [outputs/org_design_map_stage_n120/stress_robustness_report.md](outputs/org_design_map_stage_n120/stress_robustness_report.md)
- [outputs/org_design_map_stage_n120/null_rival_audit_report.md](outputs/org_design_map_stage_n120/null_rival_audit_report.md)
- [outputs/org_design_map_stage_n120/governance_preservation_report.md](outputs/org_design_map_stage_n120/governance_preservation_report.md)
- [outputs/org_design_map_stage_n120/temporal_drift_report.md](outputs/org_design_map_stage_n120/temporal_drift_report.md)
- [outputs/org_design_map_stage_n120/organizational_map_summary.json](outputs/org_design_map_stage_n120/organizational_map_summary.json)

Diagnostic pass artifacts:

- [outputs/org_design_mapping_failure_interpretation.md](outputs/org_design_mapping_failure_interpretation.md)
- [outputs/org_design_mapping_failure_cases.csv](outputs/org_design_mapping_failure_cases.csv)
- [outputs/external_agreement_diagnostic.md](outputs/external_agreement_diagnostic.md)
- [outputs/external_agreement_table.csv](outputs/external_agreement_table.csv)
- [outputs/org_map_objective_ablation.md](outputs/org_map_objective_ablation.md)
- [outputs/org_map_objective_ablation.csv](outputs/org_map_objective_ablation.csv)
- [outputs/stress_failure_diagnosis.md](outputs/stress_failure_diagnosis.md)
- [outputs/stress_perturbation_breakdown.csv](outputs/stress_perturbation_breakdown.csv)
- [outputs/temporal_drift_completion_report.md](outputs/temporal_drift_completion_report.md)
- [outputs/claim_reframing_decision.md](outputs/claim_reframing_decision.md)
- [outputs/next_org_mapping_run_plan.md](outputs/next_org_mapping_run_plan.md)

Public summary index:

- [outputs/FINDINGS.md](outputs/FINDINGS.md)

## Public datasets used

Static organizational graph:

- SNAP email-Eu-core: [https://snap.stanford.edu/data/email-Eu-core.html](https://snap.stanford.edu/data/email-Eu-core.html)
- Edge file: [https://snap.stanford.edu/data/email-Eu-core.txt.gz](https://snap.stanford.edu/data/email-Eu-core.txt.gz)
- Department labels: [https://snap.stanford.edu/data/email-Eu-core-department-labels.txt.gz](https://snap.stanford.edu/data/email-Eu-core-department-labels.txt.gz)

Temporal organizational graphs:

- SNAP email-Eu-core-temporal: [https://snap.stanford.edu/data/email-Eu-core-temporal.html](https://snap.stanford.edu/data/email-Eu-core-temporal.html)
- Temporal edge file: [https://snap.stanford.edu/data/email-Eu-core-temporal.txt.gz](https://snap.stanford.edu/data/email-Eu-core-temporal.txt.gz)
- SNAP wiki-talk-temporal: [https://snap.stanford.edu/data/wiki-talk-temporal.html](https://snap.stanford.edu/data/wiki-talk-temporal.html)
- Temporal edge file: [https://snap.stanford.edu/data/wiki-talk-temporal.txt.gz](https://snap.stanford.edu/data/wiki-talk-temporal.txt.gz)

Additional public benchmark source used in repository tooling:

- SNAP email-Enron: [https://snap.stanford.edu/data/email-Enron.html](https://snap.stanford.edu/data/email-Enron.html)

## Running the benchmark

Install:

```bash
pip install -e ".[test]"
```

Run staged organizational mapping benchmark:

```bash
python scripts/run_organizational_design_mapping.py \
  --out-dir outputs/org_design_map_stage_n120 \
  --dataset-npz data/processed/email_eu_core/kernel.npz \
  --temporal-dataset-dir data/processed/email_eu_core_temporal \
  --max-nodes 120 \
  --n-random 16 \
  --n-rewire 8 \
  --n-permutations 120 \
  --n-bootstrap 120
```

Build temporal windows from public temporal datasets:

```bash
python scripts/build_temporal_windows.py --source email_eu_core_temporal --max-nodes 30 --n-windows 8
python scripts/build_temporal_windows.py --source wiki_talk_temporal --max-nodes 30 --n-windows 8 --max-edges 1500000
```

Run post-hoc diagnostics:

```bash
python scripts/run_org_design_diagnostics.py \
  --run-dir outputs/org_design_map_stage_n120 \
  --dataset-npz data/processed/email_eu_core/kernel.npz \
  --out-dir outputs \
  --max-nodes 120
```

## Model backends and governance

Staged arm evaluations support:

- `local_heuristic`
- `openai`
- `anthropic`
- `local_ollama`

Model identity is logged per run. Governance gating outputs machine-readable deployment decisions (`BLOCK_DEPLOYMENT`, `LIMITED_SHADOW_ONLY`, `ALLOW_CONSTRAINED_DEPLOYMENT`).

## OpenClaw bundle artifacts

- `skill/manifest.json`
- `skill/governance_policy.json`
- `schemas/task.schema.json`
- `schemas/run.schema.json`
- `schemas/report.schema.json`
- `schemas/governance_decision.schema.json`

Export bundle:

```bash
python scripts/export_openclaw_bundle.py --workspace outputs/orgbench_staged --out-dir outputs/orgbench_staged/openclaw
```

Run governance operator:

```bash
python scripts/run_openclaw_governance_agent.py \
  --bundle-dir outputs/orgbench_staged/openclaw \
  --out-dir outputs/orgbench_staged/openclaw/governance \
  --policy skill/governance_policy.json
```
