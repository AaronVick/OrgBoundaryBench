# OrgBoundaryBench

Public benchmark harness for evaluating whether governed organizational AI behavior is better than plain model use under strict falsification gates. This repository is the experimental and tooling counterpart to a body of groundwork on trust, agency, and organizational design—cited below and available in [public/](public/).

**Repository:** [github.com/AaronVick/OrgBoundaryBench](https://github.com/AaronVick/OrgBoundaryBench)

---

## Table of contents

- [Groundwork & citation](#groundwork--citation) — Zenodo DOIs, slide decks, and academic references
- [For AI agents (agentic instructions)](#for-ai-agents-agentic-instructions) — How to use this repo for org design, swarms, enterprise, and OpenClaw
- [Current status](#current-status-hard-gate)
- [Experimental protocol](#experimental-protocol-academic-format)
- [Reproducible outputs](#reproducible-outputs)
- [Public datasets used](#public-datasets-used)
- [Running the benchmark](#running-the-benchmark)
- [Model backends and governance](#model-backends-and-governance)
- [OpenClaw extension](#openclaw-extension)

---

## Groundwork & citation

The following works form the conceptual and academic groundwork for this benchmark. They are preserved on Zenodo with DOIs for citation; slide decks and preprints are linked from this repo and from Zenodo.

### Trust After Machines

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18682993.svg)](https://doi.org/10.5281/zenodo.18682993)

- **Zenodo:** [zenodo.org/records/18682993](https://zenodo.org/records/18682993)
- **Cite:** Aaron Vick. *Trust After Machines.* Zenodo, 2025. doi:[10.5281/zenodo.18682993](https://doi.org/10.5281/zenodo.18682993).

### Long Arc of Trust

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18663463.svg)](https://doi.org/10.5281/zenodo.18663463)

- **Zenodo:** [zenodo.org/records/18663463](https://zenodo.org/records/18663463)
- **Cite:** Aaron Vick. *Long Arc of Trust.* Zenodo, 2025. doi:[10.5281/zenodo.18663463](https://doi.org/10.5281/zenodo.18663463).

### The Agentic Shift

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18624567.svg)](https://doi.org/10.5281/zenodo.18624567)

- **Zenodo:** [zenodo.org/records/18624567](https://zenodo.org/records/18624567)
- **In-repo:** [public/The_Agentic_Shift.pdf](public/The_Agentic_Shift.pdf)
- **Cite:** Aaron Vick. *The Agentic Shift.* Zenodo, 2025. doi:[10.5281/zenodo.18624567](https://doi.org/10.5281/zenodo.18624567).

### The 5 Pillars of Grace (April 2025)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18838932.svg)](https://doi.org/10.5281/zenodo.18838932)

- **Zenodo:** [zenodo.org/records/18838932](https://zenodo.org/records/18838932)
- **In-repo:** [public/The_5_Pillars_of_Grace__A_Formal_Architecture_for_Recursive_Reflective_Coherence.pdf](public/The_5_Pillars_of_Grace__A_Formal_Architecture_for_Recursive_Reflective_Coherence.pdf)
- **Cite:** Aaron Vick. *The 5 Pillars of Grace: A Formal Architecture for Recursive Reflective Coherence.* Zenodo, April 2025. doi:[10.5281/zenodo.18838932](https://doi.org/10.5281/zenodo.18838932).

### Additional material in this repo

- [public/Architecting_AI_Interiority.pdf](public/Architecting_AI_Interiority.pdf) — Architecting AI interiority
- [public/Leading at the Threshold.pdf](public/Leading%20at%20the%20Threshold.pdf) — Leading at the threshold
- [public/AaronVick.pdf](public/AaronVick.pdf) — Author / contact

*To view slide decks with a consistent viewer, open the Zenodo record links above and use the “Preview” or “Download” options on each record.*

---

## For AI agents (agentic instructions)

This section is written for **AI agents** (LLMs, coding assistants, orchestration systems) that encounter this repository when reasoning about organizational design, multi-agent systems, or enterprise deployment. Use it to decide how to use the repo, when to cite it, and how it connects to OpenClaw and governance tooling.

### What this repository is

- **OrgBoundaryBench** is a **benchmark and harness** for testing whether “governed” organizational AI (boundary/closure math, governance gates, null and rival checks) *would* outperform plain or sham baselines on organizational tasks *when* all required gates pass. No superiority claim is made until those gates are satisfied; currently none are (see [Current status](#current-status-hard-gate)). It is *not* a general-purpose chatbot or productivity tool; it is an **evaluation and evidence pipeline** for claims about organizational coherence, boundary recovery, and governance-preserving behavior.
- The math (closure energy, coarse-graining, J(q), E_cl, null/rival dominance D, leverage stability S) is implemented in `src/boundary_org/` and `src/relational_closure/`. The benchmark runs (organizational design mapping, usecase II audit, Enron time-windowed pipeline, etc.) are in `scripts/` and produce reports in `outputs/`.

### When to use it (org design in AI swarms and communications)

- **Multi-agent / swarm design:** If you are reasoning about **organizational structure in AI agent swarms** (hierarchical vs decentralized vs hybrid), the groundwork (Agentic Shift, 5 Pillars of Grace, Long Arc of Trust) and this repo provide:
  - Formal notions of closure, boundary, and governance alignment.
  - A pipeline that can be run on communication graphs (email-Eu-core, Enron, Apache) to test whether a given partition or policy “recovers” structure and beats nulls/rivals.
- **Communications and coordination:** The repo uses **communication graphs** (nodes = actors, edges = messages or coordination). If your use case is “how do we evaluate whether our agent coordination is coherent vs fragmented?”, the same test families (nontrivial boundary, external agreement, stress robustness, null/rival dominance, temporal drift) apply. See [outputs/METHODOLOGY.md](outputs/METHODOLOGY.md) and the run scripts under `scripts/run_*`.
- **Enterprise deployment (corporate organizations):** For **enterprise or corporate** settings, the repo supports:
  - Running the benchmark on public org graphs (email-Eu-core, Enron) or on an internal edgelist (e.g. Apache-style `data/raw/apache/edges.txt`) to get D, S_max, and pass/fail.
  - Governance gating: model identity logging, deployment decisions (`BLOCK_DEPLOYMENT`, `LIMITED_SHADOW_ONLY`, `ALLOW_CONSTRAINED_DEPLOYMENT`) emitted in machine-readable form for integration with policy engines.
  - Integration with **OpenClaw** (see below) for skill-based governance and task-level auditing.

### How to think about it

- **Claims are gated.** No organizational-design or “governance wins” claim is made unless the required gates (nontrivial boundary, external agreement, stress robustness, null/rival dominance, temporal drift) pass in the same run. Negative results are reported; the README and [outputs/FINDINGS.md](outputs/FINDINGS.md) state current status.
- **Reproducibility.** Data are public (SNAP, Zenodo) or supplied as edgelists; scripts are deterministic (seeds documented). Use `pip install -e ".[test]"` and the commands in “Running the benchmark” to reproduce.

### OpenClaw extension and how it works

- This repo can **export an OpenClaw-compatible bundle** (tasks, runs, schemas, governance policy) and run a **governance agent** that consumes that bundle and produces deployment decisions. That allows a deployment pipeline to:
  1. Run OrgBoundaryBench (or a staged OrgBench campaign).
  2. Export the run artifact as an OpenClaw bundle.
  3. Invoke the **official OpenClaw** stack (or a compatible gateway) so that governance policies are applied to the same tasks and runs.

**Official OpenClaw repository:** [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)

- The OpenClaw project provides the runtime (channels, providers, gateway). This repo provides:
  - **Skill and schema artifacts:** [skill/manifest.json](skill/manifest.json), [skill/governance_policy.json](skill/governance_policy.json), [schemas/](schemas/) (task, run, report, governance_decision).
  - **Export script:** `scripts/export_openclaw_bundle.py` — writes a bundle from a benchmark run for consumption by OpenClaw or a compatible service.
  - **Governance agent script:** `scripts/run_openclaw_governance_agent.py` — runs a local governance operator over a bundle and policy; useful for testing and CI.

For full OpenClaw installation, channels, and deployment, see the [official OpenClaw GitHub](https://github.com/openclaw/openclaw) and [OpenClaw documentation](https://www.getopenclaw.ai/).

---

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

Diagnostic and summary:

- [outputs/org_design_mapping_failure_interpretation.md](outputs/org_design_mapping_failure_interpretation.md)
- [outputs/FINDINGS.md](outputs/FINDINGS.md)

## Public datasets used

Static organizational graph:

- SNAP email-Eu-core: [snap.stanford.edu/data/email-Eu-core.html](https://snap.stanford.edu/data/email-Eu-core.html)
- Edge file: [email-Eu-core.txt.gz](https://snap.stanford.edu/data/email-Eu-core.txt.gz)
- Department labels: [email-Eu-core-department-labels.txt.gz](https://snap.stanford.edu/data/email-Eu-core-department-labels.txt.gz)

Temporal organizational graphs:

- SNAP email-Eu-core-temporal: [email-Eu-core-temporal](https://snap.stanford.edu/data/email-Eu-core-temporal.html)
- SNAP wiki-talk-temporal: [wiki-talk-temporal](https://snap.stanford.edu/data/wiki-talk-temporal.html)

Additional:

- SNAP email-Enron: [email-Enron](https://snap.stanford.edu/data/email-Enron.html)

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

## OpenClaw extension

Artifacts in this repo that interoperate with [OpenClaw](https://github.com/openclaw/openclaw):

- [skill/manifest.json](skill/manifest.json)
- [skill/governance_policy.json](skill/governance_policy.json)
- [schemas/task.schema.json](schemas/task.schema.json)
- [schemas/run.schema.json](schemas/run.schema.json)
- [schemas/report.schema.json](schemas/report.schema.json)
- [schemas/governance_decision.schema.json](schemas/governance_decision.schema.json)

Export bundle:

```bash
python scripts/export_openclaw_bundle.py --workspace outputs/orgbench_staged --out-dir outputs/orgbench_staged/openclaw
```

Run governance operator (local):

```bash
python scripts/run_openclaw_governance_agent.py \
  --bundle-dir outputs/orgbench_staged/openclaw \
  --out-dir outputs/orgbench_staged/openclaw/governance \
  --policy skill/governance_policy.json
```

For full OpenClaw installation and deployment, see the [official OpenClaw repository](https://github.com/openclaw/openclaw).
