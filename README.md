# OrgBoundaryBench

Public benchmark harness for evaluating whether governed organizational AI behavior is better than plain model use under strict falsification gates. This repository is the experimental and tooling counterpart to a body of groundwork on trust, agency, and organizational design—cited below and available in [public/](public/).

**Repository:** [github.com/AaronVick/OrgBoundaryBench](https://github.com/AaronVick/OrgBoundaryBench)

---

## Benchmark & invitation (not a verdict)

This framework is released as an **open benchmark**, not a final verdict. It provides:

- **Open benchmark** — Public protocol, test families, and evaluation criteria.
- **Reproducible code** — Deterministic scripts, documented seeds, and public datasets (SNAP, Zenodo).
- **Documented failures** — Current gate outcomes and failure interpretations are reported in [Current status](#current-status-hard-gate) and [outputs/FINDINGS.md](outputs/FINDINGS.md).
- **Explicit unresolved gates** — Which gates pass or fail is stated clearly; no superiority claim is made until all required gates pass.

**We invite replication, criticism, and extension.** Independent runs, alternative baselines, improved methodology, and extensions to new domains are welcome. The benchmark is designed to be falsifiable and to advance the evidence base for organizational AI governance.

---

## Table of contents

- [Benchmark & invitation](#benchmark--invitation-not-a-verdict) — Open benchmark, reproducible code, documented failures, explicit gates; we invite replication, criticism, and extension
- [Groundwork & citation](#groundwork--citation) — Zenodo DOIs, public slide decks, and academic references
- [Public docs & slide decks](#public-docs--slide-decks) — All materials in [public/](public/) with Zenodo DOIs
- [Academic references (supporting literature)](#academic-references-supporting-literature) — Non–Aaron Vick citations with verified DOI/publisher links
- [Exploratory simulations](#exploratory-simulations) — Boundary-coherence simulation runs ([docs/](docs/exploratory_simulations), [tests/](tests/exploratory_simulations))
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

The following works form the conceptual and academic groundwork for this benchmark. They are preserved on Zenodo with DOIs for citation; slide decks and preprints are in [public/](public/) and linked from Zenodo.

### Trust After Machines

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18682993.svg)](https://doi.org/10.5281/zenodo.18682993)

- **DOI:** [10.5281/zenodo.18682993](https://doi.org/10.5281/zenodo.18682993)
- **Zenodo:** [zenodo.org/records/18682993](https://zenodo.org/records/18682993)
- **Cite:** Aaron Vick. *Trust After Machines.* Zenodo, 2025. doi:[10.5281/zenodo.18682993](https://doi.org/10.5281/zenodo.18682993).

### Long Arc of Trust

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18663463.svg)](https://doi.org/10.5281/zenodo.18663463)

- **DOI:** [10.5281/zenodo.18663463](https://doi.org/10.5281/zenodo.18663463)
- **Zenodo:** [zenodo.org/records/18663463](https://zenodo.org/records/18663463)
- **Cite:** Aaron Vick. *Long Arc of Trust.* Zenodo, 2025. doi:[10.5281/zenodo.18663463](https://doi.org/10.5281/zenodo.18663463).

### The Agentic Shift

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18624567.svg)](https://doi.org/10.5281/zenodo.18624567)

- **DOI:** [10.5281/zenodo.18624567](https://doi.org/10.5281/zenodo.18624567)
- **Zenodo:** [zenodo.org/records/18624567](https://zenodo.org/records/18624567)
- **In-repo (slide deck):** [public/The_Agentic_Shift.pdf](public/The_Agentic_Shift.pdf)
- **Cite:** Aaron Vick. *The Agentic Shift.* Zenodo, 2025. doi:[10.5281/zenodo.18624567](https://doi.org/10.5281/zenodo.18624567).

### The 5 Pillars of Grace (April 2025)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18838932.svg)](https://doi.org/10.5281/zenodo.18838932)

- **DOI:** [10.5281/zenodo.18838932](https://doi.org/10.5281/zenodo.18838932)
- **Zenodo:** [zenodo.org/records/18838932](https://zenodo.org/records/18838932)
- **In-repo (slide deck):** [public/The_5_Pillars_of_Grace__A_Formal_Architecture_for_Recursive_Reflective_Coherence.pdf](public/The_5_Pillars_of_Grace__A_Formal_Architecture_for_Recursive_Reflective_Coherence.pdf)
- **Cite:** Aaron Vick. *The 5 Pillars of Grace: A Formal Architecture for Recursive Reflective Coherence.* Zenodo, April 2025. doi:[10.5281/zenodo.18838932](https://doi.org/10.5281/zenodo.18838932).

### Public docs & slide decks

All public materials are in [public/](public/). Slide decks for the Zenodo works are available in-repo and on Zenodo (Preview/Download).

| Document | In-repo | DOI / notes |
|----------|---------|-------------|
| **Trust After Machines** | — | [10.5281/zenodo.18682993](https://doi.org/10.5281/zenodo.18682993) (Zenodo only) |
| **Long Arc of Trust** | — | [10.5281/zenodo.18663463](https://doi.org/10.5281/zenodo.18663463) (Zenodo only) |
| **The Agentic Shift** | [The_Agentic_Shift.pdf](public/The_Agentic_Shift.pdf) | [10.5281/zenodo.18624567](https://doi.org/10.5281/zenodo.18624567) |
| **The 5 Pillars of Grace** | [The_5_Pillars_of_Grace__A_Formal_Architecture_for_Recursive_Reflective_Coherence.pdf](public/The_5_Pillars_of_Grace__A_Formal_Architecture_for_Recursive_Reflective_Coherence.pdf) | [10.5281/zenodo.18838932](https://doi.org/10.5281/zenodo.18838932) |
| **Architecting AI Interiority** | [Architecting_AI_Interiority.pdf](public/Architecting_AI_Interiority.pdf) | — |
| **Leading at the Threshold** | [Leading at the Threshold.pdf](public/Leading%20at%20the%20Threshold.pdf) | — |
| **Author / contact** | [AaronVick.pdf](public/AaronVick.pdf) | — |


*To view slide decks, open the Zenodo record links above or the PDFs in [public/](public/) (Zenodo Preview/Download or a local PDF viewer).*

### Academic references (supporting literature)

The following academic works are cited in the dissertation and related materials as supporting literature (organizational theory, network science, TDA, automation, and systems theory). All links below are verified citation URLs (DOI or publisher).

**Organizational theory & sensemaking**

| Citation | Link |
|----------|------|
| March, J.G. & Simon, H.A. *Organizations.* Wiley, 1958. | [Cambridge review](https://www.cambridge.org/core/journals/american-political-science-review/article/abs/organizations-by-james-g-march-and-herbert-a-simon-with-the-collaboration-of-harold-guetzkow-new-york-john-wiley-and-sons-inc-london-chapman-and-hall-ltd-1958-pp-xi-262-600/6017E27AAE077C170FE0805D5976118F) |
| Mintzberg, H. *The Structuring of Organizations.* Prentice Hall, 1979. | [WorldCat](https://www.worldcat.org/title/structuring-of-organizations/oclc/4492683) |
| Weick, K. *Sensemaking in Organizations.* Sage, 1995. | [Sage](https://us.sagepub.com/en-us/nam/sensemaking-in-organizations/book205732) |
| Vaughan, D. *The Challenger Launch Decision.* University of Chicago Press, 1996. | [DOI](https://doi.org/10.7208/chicago/9780226851785.001.0001) |
| Argyris, C. & Schön, D. *Organizational Learning: A Theory of Action Perspective.* Addison-Wesley, 1978. | [WorldCat](https://www.worldcat.org/title/organizational-learning-a-theory-of-action-perspective/oclc/3163019) |
| Senge, P. *The Fifth Discipline*, rev. ed. Doubleday, 2006. | [WorldCat](https://www.worldcat.org/title/fifth-discipline/oclc/318262215) |
| Pfeffer, J. *New Directions for Organization Theory: Problems and Prospects.* Oxford University Press, 1997. | [OUP/RePEc](https://ideas.repec.org/b/oxp/obooks/9780195114348.html) |

**Network science & social network analysis**

| Citation | Link |
|----------|------|
| Barabási, A.-L. *Network Science.* Cambridge University Press, 2016. | [Free online](http://networksciencebook.com/) · [CUP](https://www.cambridge.org/us/universitypress/subjects/physics/statistical-physics/network-science?format=HB&isbn=9781107076266) |
| Newman, M. *Networks*, 2nd ed. Oxford University Press, 2018. | [OUP](https://academic.oup.com/book/27303) |
| Wasserman, S. & Faust, K. *Social Network Analysis: Methods and Applications.* Cambridge University Press, 1994. | [CUP](https://www.cambridge.org/us/universitypress/subjects/sociology/sociology-general-interest/social-network-analysis-methods-and-applications) |
| Borgatti, S.P., Mehra, A., Brass, D.J. & Labianca, G. "Network Analysis in the Social Sciences." *Science* 323 (2009): 892–895. | [DOI](https://doi.org/10.1126/science.1165821) |
| Cross, R., Borgatti, S.P. & Parker, A. "Making Invisible Work Visible." *California Management Review* 44, no. 2 (2002): 25–46. | [CMR](https://cmr.berkeley.edu/2002/02/44-2-making-invisible-work-visible-using-social-network-analysis-to-support-strategic-collaboration/) · [JSTOR](https://www.jstor.org/stable/41166121) |
| Uzzi, B. & Spiro, J. "Collaboration and Creativity: The Small World Problem." *American Journal of Sociology* 111, no. 2 (2005): 447–504. | [DOI](https://doi.org/10.1086/432782) |
| White, H.C., Boorman, S.A. & Breiger, R.L. "Social Structure from Multiple Networks. I. Blockmodels of Roles and Positions." *American Journal of Sociology* 81, no. 4 (1976): 730–780. | [DOI](https://doi.org/10.1086/226141) |
| Burt, R.S. *Structural Holes: The Social Structure of Competition.* Harvard University Press, 1992. | [HUP](https://www.hup.harvard.edu/books/9780674843714) |
| Doreian, P., Batagelj, V. & Ferligoj, A. *Generalized Blockmodeling.* Cambridge University Press, 2005. | [CUP](https://www.cambridge.org/us/universitypress/subjects/sociology/sociology-general-interest/generalized-blockmodeling) |

**Community detection & spectral methods**

| Citation | Link |
|----------|------|
| Newman, M.E.J. "Modularity and Community Structure in Networks." *PNAS* 103, no. 23 (2006): 8577–8582. | [DOI](https://doi.org/10.1073/pnas.0601602103) |
| Blondel, V.D., Guillaume, J.-L., Lambiotte, R. & Lefebvre, E. "Fast Unfolding of Communities in Large Networks." *J. Stat. Mech.* 2008 (2008): P10008. | [DOI](https://doi.org/10.1088/1742-5468/2008/10/P10008) |
| von Luxburg, U. "A Tutorial on Spectral Clustering." *Statistics and Computing* 17, no. 4 (2007): 395–416. | [DOI](https://doi.org/10.1007/s11222-007-9033-z) |

**Topological data analysis & higher-order networks**

| Citation | Link |
|----------|------|
| Carlsson, G. "Topology and Data." *Bulletin of the American Mathematical Society* 46, no. 2 (2009): 255–308. | [DOI](https://doi.org/10.1090/S0273-0979-09-01249-X) · [AMS](https://www.ams.org/journals/bull/2009-46-02/S0273-0979-09-01249-X/) |
| Edelsbrunner, H. & Harer, J. *Computational Topology: An Introduction.* American Mathematical Society, 2010. | [AMS](https://bookstore.ams.org/mbk-69/) |
| Benson, A.R., Gleich, D.F. & Leskovec, J. "Higher-Order Organization of Complex Networks." *Science* 353, no. 6295 (2016): 163–166. | [DOI](https://doi.org/10.1126/science.aad9029) |
| Battiston, F. et al. "Networks Beyond Pairwise Interactions: Structure and Dynamics." *Physics Reports* 874 (2020): 1–92. | [DOI](https://doi.org/10.1016/j.physrep.2020.05.004) |
| Holme, P. & Saramäki, J. "Temporal Networks." *Physics Reports* 519, no. 3 (2012): 97–125. | [DOI](https://doi.org/10.1016/j.physrep.2012.03.001) |

**Automation, supervisory control & human–machine systems**

| Citation | Link |
|----------|------|
| Parasuraman, R., Sheridan, T.B. & Wickens, C.D. "A Model for Types and Levels of Human Interaction with Automation." *IEEE Trans. Syst. Man Cybern. A* 30, no. 3 (2000): 286–297. | [DOI](https://doi.org/10.1109/3468.844354) · [IEEE Xplore](https://ieeexplore.ieee.org/document/844354) |
| Sheridan, T.B. *Telerobotics, Automation, and Human Supervisory Control.* MIT Press, 1992. | [MIT Press](https://mitpress.mit.edu/9780262193342/telerobotics-automation-and-human-supervisory-control/) |

**Systems theory & autopoiesis**

| Citation | Link |
|----------|------|
| Maturana, H. & Varela, F. *Autopoiesis and Cognition: The Realization of the Living.* Reidel, 1980. | [WorldCat](https://www.worldcat.org/title/autopoiesis-and-cognition-the-realization-of-the-living/oclc/5844214) |
| Luhmann, N. *Social Systems.* Stanford University Press, 1995. | [Stanford](https://www.sup.org/books/sociology/social-systems) |

---

## Exploratory simulations

Exploratory boundary-coherence simulations (synthetic Dirichlet-kernel runs for bound scaling, collapse hazard, and coordination-skeleton strategies) are maintained in two places:

- **[docs/exploratory_simulations/](docs/exploratory_simulations/)** — Scripts, run outputs (run001–run010), findings, and [CHANGELOG](docs/exploratory_simulations/CHANGELOG.md).
- **[tests/exploratory_simulations/](tests/exploratory_simulations/)** — Mirror/copy for test and reproducibility tooling; same structure and findings.

These runs are *exploratory computational scaffolding* (see methodology and dissertation Ch13), not external validation of the benchmark. Run-by-run changelog, artifact paths, and narrative–result divergence are documented in the findings and CHANGELOG.

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

Latest public mapping run status (documented for reproducibility and critique):

- nontrivial boundary map: `PASS`
- governance preservation: `PASS`
- external agreement: `FAIL`
- stress robustness: `FAIL`
- null/rival dominance: `FAIL`
- temporal drift validation: `PASS` (completed)
- organizational-design claim: `LOCKED`

These are **explicit unresolved gates**: the benchmark is in progress, and no superiority or organizational-design claim is currently unlocked. See [outputs/org_design_mapping_failure_interpretation.md](outputs/org_design_mapping_failure_interpretation.md) and [outputs/FINDINGS.md](outputs/FINDINGS.md) for documented failures and interpretation. Replication and independent verification are invited.

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

Remote-compute runs (Claude API), when used:

- `outputs/remote_compute_claude/<run_id>/` — payload, result, run_metadata, optional verification_report (see [docs/REMOTE_COMPUTE_PROTOCOL.md](docs/REMOTE_COMPUTE_PROTOCOL.md)).

**Evidentiary testing (two decisive runs):** To run the tests that would move the scientific needle — full email-Eu-core null/rival/leverage audit and event-linked criterion — see [docs/evidentiary_roadmap.md](docs/evidentiary_roadmap.md). One-command full audit (build kernel if needed, then run PRD-31): `python3 scripts/run_evidentiary_full_audit.py` (optional `--feasible` for n=400).

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

## Remote compute (Claude API)

When local runs are infeasible (e.g. laptop memory or runtime limits), the same logical procedures (bootstrap null dominance, permutation external p-values) can be run **remotely** by sending a small payload and explicit math instructions to **Claude Opus 4.6** via the Anthropic API. Results are documented with model ID, payload hash, and optional local verification.

- **Protocol:** [docs/REMOTE_COMPUTE_PROTOCOL.md](docs/REMOTE_COMPUTE_PROTOCOL.md)
- **Model:** `claude-opus-4-6` (documented in run artifacts and protocol).
- **Scripts:**  
  - `scripts/prepare_remote_compute_payload.py` — build payload JSON from a small kernel.  
  - `scripts/run_remote_compute_claude.py` — send payload to Claude, write result to `outputs/remote_compute_claude/<run_id>/`.  
  - `scripts/verify_remote_compute.py` — verify a remote result by re-running the same payload locally.
- **Outputs:** Each run produces `payload.json`, `result.json`, `run_metadata.json`, and optionally `verification_report.json` after verification. These can be published for reproducibility; the protocol describes verification and caveats (context limits, numeric precision).

Requires `ANTHROPIC_API_KEY`. No API key is stored in the repository.

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
