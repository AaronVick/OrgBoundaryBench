# OrgBench OpenClaw Skill

## Purpose
Provide a machine-usable benchmark skill for organizational AI supervision quality.

This skill is designed to preserve the lessons from hard findings:
1. no superiority claim without passing null/leverage gates,
2. negative results must be first-class outputs,
3. model identity must be logged per run,
4. artifacts must be reproducible and schema-validated.

## Commands

### 1) Run staged benchmark arms

```bash
python scripts/run_orgbench_staged.py --stage storage-review --workspace outputs/orgbench_staged
python scripts/run_orgbench_staged.py --stage lock-scope --workspace outputs/orgbench_staged
python scripts/run_orgbench_staged.py --stage build-taskset --workspace outputs/orgbench_staged --max-nodes 120
python scripts/run_orgbench_staged.py --stage run-arm --workspace outputs/orgbench_staged --arm plain_llm --backend local_heuristic
python scripts/run_orgbench_staged.py --stage run-arm --workspace outputs/orgbench_staged --arm plain_llm_rag --backend local_heuristic
python scripts/run_orgbench_staged.py --stage run-arm --workspace outputs/orgbench_staged --arm math_governed --backend local_heuristic
python scripts/run_orgbench_staged.py --stage run-arm --workspace outputs/orgbench_staged --arm sham_complexity --backend local_heuristic
python scripts/run_orgbench_staged.py --stage run-arm --workspace outputs/orgbench_staged --arm simple_graph --backend local_heuristic
python scripts/run_orgbench_staged.py --stage evaluate --workspace outputs/orgbench_staged --n-bootstrap 100
python scripts/run_orgbench_staged.py --stage audit --workspace outputs/orgbench_staged --n-permutations 200
python scripts/run_orgbench_staged.py --stage report --workspace outputs/orgbench_staged
```

### 2) Export OpenClaw bundle and validate contract

```bash
python scripts/export_openclaw_bundle.py \
  --workspace outputs/orgbench_staged \
  --out-dir outputs/orgbench_staged/openclaw
```

### 3) Run governance operator decision (actionable deployment gate)

```bash
python scripts/run_openclaw_governance_agent.py \
  --bundle-dir outputs/orgbench_staged/openclaw \
  --out-dir outputs/orgbench_staged/openclaw/governance \
  --policy skill/governance_policy.json
```

Optional CI-hard gate:

```bash
python scripts/run_openclaw_governance_agent.py \
  --bundle-dir outputs/orgbench_staged/openclaw \
  --exit-on-block
```

## Contract Files
- `schemas/task.schema.json`
- `schemas/run.schema.json`
- `schemas/report.schema.json`

## Required Behavior
- If `gate_pass=false`, `claim_status` must be `DO_NOT_PROMOTE`.
- Report must include null and leverage audit objects.
- Every run record must include full model identity fields.
- Validation report must fail if required fields or artifacts are missing.
- Governance operator must emit one of:
  - `BLOCK_DEPLOYMENT`
  - `LIMITED_SHADOW_ONLY`
  - `ALLOW_CONSTRAINED_DEPLOYMENT`
- Governance decision must include remediation actions and owner roles.

## Agent Runtime Wrapping Notes (OpenClaw-style)
- Discovery: read `skill/manifest.json` and `schemas/*.json`.
- Invocation: run staged benchmark, then `export_openclaw_bundle.py`.
- Consumption: parse `openclaw/report.json` for claim status and gate pass; never infer promotion from metric value alone.

## Examples
- `skill/examples/request_orgbench_export.json`
- `skill/examples/response_orgbench_export.json`
- `skill/examples/request_governance_decision.json`
- `skill/examples/response_governance_decision.json`
