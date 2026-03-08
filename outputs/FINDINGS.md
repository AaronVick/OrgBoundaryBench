# Empirical Findings: BPO and Relational Closure

Aggregated empirical conclusions from framework runs. Updated from run reports (see `outputs/runs/`) and PRD-06/PRD-13 falsification. **Methodology:** `outputs/METHODOLOGY.md`; **Framework overview:** `docs/FRAMEWORKS.md`.

---

## 1. Boundary-Preserving Organization (BPO)

**Source runs:** Latest: `outputs/runs/2026-03-08T001500Z/` (and prior runs in `runs/`).

### 1.1 Domain 6.1 (Synthetic)

- **T3.2 (closure bound):** No violations in N=200 samples; max ratio at or below 1.0. **Finding:** Numerical support for \(E^{\mathrm{op}}_{\mathrm{cl}}(q) \leq m_*^2 \|K\|^2\).
- **T3.3 (spectral decay):** max_decay_ratio within design tolerance (reversible, finite t). **Finding:** Spectral decay behavior consistent with theorem.
- **T3.4 (greedy):** Steps in [4, 8], all ≤ n−1. **Finding:** Greedy coarse-graining terminates as proved.
- **E6.1 (discrimination):** AUC(E_cl)=1.0, AUC(Q)=1.0; closure ≥ Q−0.05. **Finding:** Closure energy discriminates lumpable vs non-lumpable at least as well as modularity on synthetic benchmarks; no falsification.

### 1.2 Domain 6.4 (Public data — Enron SNAP)

- **Test D:** q* (greedy) and Louvain computed on same kernel (60-node subgraph). E_cl(q*)=0, Q(q*)=0; Louvain: E_cl=0.074, Q=0.234. **Finding:** Framework and baseline both reported; full Test D (precision/recall vs org-chart) not applied in reported run.
- **Limitations:** 60-node subgraph; org-chart not used; Domains 6.2, 6.3, 6.5, 6.6 not yet run.

### 1.3 Falsification status (Table 1)

- **E6.1:** Not triggered (closure meets or exceeds Q−0.05 on 6.1).
- **6.4 vs Louvain:** Calibration only; no claim yet that q* beats Louvain on precision/recall vs org.

---

## 2. Relational Closure / Topology of Interiority (RCTI)

**Source runs:** RCTI verification runs (when present) in `outputs/runs/<run_id>/` with `frameworks: [RelationalClosure]` and artifacts `rcti_verification_report.txt`, `conditions_C1_C4_C2F.yaml`, `falsification_F1_F5.md`.

### 2.1 Synthetic / small-graph (pipeline validation)

- **C1 (topological non-triviality):** Reported per run: presence of persistent H₁ (or β₁ proxy) with lifespan > τ at matched density.
- **C3 (dynamical persistence):** Single-window runs report N/A; multi-window runs report barcode stability d_B < δ where applicable.
- **C4b (compositional coherence):** Non-trivial β_k for k≥2 when computed.
- **C2F (closure fidelity):** Reported when S' is specified; relative-homology fidelity 0–1.

### 2.2 Falsification (F1–F5)

- **F1 (barcode discrimination):** Not yet tested on neural conscious/unconscious contrast (e.g. propofol). Status: deferred until neural pipeline.
- **F2 (C2F decorrelation):** Requires self-boundary phenomenology comparison; deferred.
- **F3 (transformer surprise):** Not tested; framework predicts LLMs satisfying C1–C4 would be conscious.
- **F4 (dissociation):** Two-parameter dissociation (HC vs C2F) testable on synthetic or future psychedelic/sedation data.
- **F5 (density artifact):** Matched-density controls mandated in methodology; any reported topological difference must survive density matching.

### 2.3 Limitations

- Directed flag complex and persistence implemented for small graphs; neuron-resolution or dense attention graphs require Flagser or scaled pipeline.
- C2F requires pre-registered S'; endogenous S' identification not yet implemented.
- First empirical test (graded propofol EEG) not yet run; protocol in Appendix A of paper.

### 2.4 Empirical test families (PRD-17, PRD-21, PRD-22)

**PRD-17 (Boundary Benchmark Harness):** Implemented in `src/boundary_org/harness.py` and `scripts/run_boundary_benchmark.py`. First run (synthetic n=10): q* collapsed to one block (E_cl=0); **success: False** (non-triviality not met). Leaderboard: singleton best J (lowest cost), then Louvain, one_block/q_star/random tied. **Finding:** On this synthetic, greedy reached trivial partition; success criterion correctly flags failure. Run with block-structured synthetic (e.g. lumpable 3-block) expected to yield success=True when q* has ≥2 blocks and beats baselines on J.

**PRD-21 (RCTI Comparative):** Implemented in `src/relational_closure/graph_baselines.py` and `scripts/run_rcti_comparative.py`. Three constructions (raw, threshold_0.5, symmetrized) run on same synthetic directed graph; C1, C4b, persistence entropy, n_simplices and six baselines (density, clustering, reciprocity, modularity, spectral_gap, entropy_degrees) reported per construction. **Finding:** Pipeline and baselines execute; discrimination vs condition labels (AUC) requires labeled data and is not yet run.

**PRD-22 (Phase Monitoring):** Implemented in `src/boundary_org/phase_monitoring.py` and `scripts/run_phase_monitoring.py`. Trajectory of (E_cl, n_blocks, NMI to previous q*) over a sequence of kernels; flags for rising_closure and abrupt_switch (NMI below threshold). **Finding:** Trajectory and flags reported; first run (synthetic 4-step perturbation) produces trajectory and optional flags. Correlation with known failure events deferred to data with incident labels.

**PRD-18 (Governance Stress):** Implemented in `src/boundary_org/governance_stress.py` and `scripts/run_governance_stress.py`. Perturbation families (noise, missingness, workload_scale); recompute E_cl and NMI(q_baseline, q_perturbed) per trial; pass = majority stable and E_cl ratio bounded. **Finding:** Suite runs; pass/fail depends on kernel and thresholds (e.g. synthetic n=8 may pass or fail). Injected-dispute workflow (five questions) remains simulated/stub for real deployment.

**PRD-19 (Quiet Error Lab):** Implemented in `src/boundary_org/quiet_error_lab.py` and `scripts/run_quiet_error_lab.py`. Planted errors (row_swap); detector flags when E_cl ratio or NMI crosses thresholds; detection_rate, false_reassurance_rate. **Finding:** Lab runs; pass requires detection_rate ≥ 0.5 and false_reassurance ≤ 0.5. First runs on synthetic show whether detector (closure/partition change) distinguishes planted vs control.

**PRD-20 (Misalignment Engine):** Implemented in `src/boundary_org/misalignment_engine.py` and `scripts/run_misalignment_engine.py`. Predictive boundary q_pred = greedy(K, μ); control proxy q_ctrl = greedy(perturbed K) or Louvain; m_n = ‖Π_pred − Π_ctrl‖ (Estimator 5.2). **Finding:** m_n computed and reported; override/recovery/confusion outcomes stubbed (synthetic relation to m_n) until real intervention data are available.

**PRD-23 (Nontrivial Boundary on Public Labeled Graphs):** Implemented in `src/boundary_org/labeled_harness.py`, `src/boundary_org/baselines.py` (spectral_partition), and `scripts/run_nontrivial_boundary_public.py`. Data pipeline: `scripts/download_and_normalize.py --source email_eu_core` builds (K, μ, labels) from SNAP email-Eu-core. Harness runs one-block, singleton, q*, Louvain, spectral, random matched; scores J(q); computes NMI, ARI, macro-F1 vs ground-truth labels; reports meaningful vs useless collapse. **Finding:** Suite runs on synthetic (n=8) and will run on email-Eu-core once data is downloaded; integration test uses synthetic mode. Falsification: q* trivial or external agreement strictly worse than all baselines (PRD-23 §4).

**PRD-24 (Public Incident-Coupled Phase Monitoring):** Implemented in `src/boundary_org/incident_phase_monitoring.py` and `scripts/run_incident_phase_monitoring.py`. Rolling (m_cl, boundary switch), phase alert steps; lead time to incident and false positive burden; density/entropy/spectral-gap drift baselines. **Finding:** Runs on synthetic kernels and incident step; pass iff phase is not worse than baselines on lead time or FP rate. Real incident timestamps (Enron, MIMIC-IV) can be encoded and loaded for event-linked validation.

**PRD-25 (Governance Metrics on Real Appeals/Overrides):** Implemented in `src/boundary_org/governance_metrics.py` and `scripts/run_governance_metrics.py`. ChallengeEvent dataclass; override latency, reversal success, unattributed residue, unresolved challenge rate; χ(d) proxy (reversibility). **Finding:** Pass only if reversal success ≥ threshold and unresolved/unattributed below thresholds (challenge paths alter outcomes). Synthetic event list for testing; MiDAS audit encoding can feed same API.

**PRD-27 (RCTI Real Sedation Test):** Implemented in `src/relational_closure/sedation_discrimination.py` and `scripts/run_rcti_sedation_test.py`. Two constructions (raw, threshold); per-sample topology (PE) and six baselines; AUC vs condition labels; pass iff topology beats or matches baselines. **Finding:** Synthetic condition contrast (cycle-like vs dense random) runs; real OpenNeuro/PhysioNet sedation data can replace synthetic when available.

**PRD-26 (Misalignment Outcome Validation):** Implemented in `src/boundary_org/misalignment_outcome_validation.py` and `scripts/run_misalignment_outcome_validation.py`. Per-unit m_n and outcomes (override_success, recovery_time, confusion); correlation in expected direction; comparison to null (permuted m_n) and graph-feature controls (density, spectral_gap); out-of-sample train/test consistency. **Finding:** Synthetic units with stub outcomes; pass requires direction_ok, m_n adds value vs controls, oos consistent. Real override/recovery data can replace stubs.

**PRD-28 (Cross-Construction Invariance and Artifact Audit):** Implemented in `src/relational_closure/cross_construction_invariance.py` and `scripts/run_cross_construction_invariance.py`. Multiple constructions (raw, threshold_0.5, symmetrized); rank correlation of PE across constructions over samples; fail if conclusions reverse or rank correlation below threshold. **Finding:** Runs on synthetic graphs; conclusions_agree and rank_correlation_pe reported; real data (e.g. PRD-27 sedation) can be passed for invariance check.

**PRD-29 (Public OrgBench Campaign and Gated Release Orchestration):** Implemented in `scripts/run_orgbench_public_campaign.py` with staged node-schedule execution, required Arm set, OpenClaw export, and governance operator per phase. **Finding:** Live campaigns on processed email-Eu-core (scaffold local-heuristic and real Anthropic Opus 4.6 phases) produced complete phase artifacts and consistently halted on `BLOCK_DEPLOYMENT` when gates failed; even at `n=200` (test n=32), `math_governed` did not exceed best baseline (`delta=0.0`), so no promotion claim.

---

## 3. Cross-framework

- **Run report convention:** All runs tag `frameworks: [BPO]` and/or `[RelationalClosure]`; findings and falsification are reported per framework in run_report.md and here.
- **Reproducibility:** Seeds and environment in run reports; REPRODUCIBILITY.md and METHODOLOGY.md for procedures.

---

**Usecase PRDs (useccases.md):** **PRD II (Null-Model, Rival-Theory, and Outlier Audit)** implemented as a single scientific-method report via `scripts/run_usecase_ii_audit.py`. Combines null/rival audit (D = Perf(q*) − max(baselines ∪ nulls)) and leverage stability (S_max). Report `usecase_II_report.txt` includes Hypothesis, Methods, Public data used, Baseline, Outcomes, Falsification, and “What would make this look good but be wrong”. Optional `--data` for public processed kernel (e.g. email-Eu-core). Bootstrap by default (--bootstrap 50); nulls include graph-structure (row-sum-preserving rewire) and leverage includes top-degree node drop. See [docs/prds/usecases-index.md](../docs/prds/usecases-index.md), [docs/findings/20260310_usecases_findings.md](../docs/findings/20260310_usecases_findings.md), and [docs/findings/20260308_usecase2_synthetic_vs_public.md](../docs/findings/20260308_usecase2_synthetic_vs_public.md) (synthetic-vs-public comparison). **PRD III** (drift/lead-time): `run_usecase_iii_drift_benchmark.py` → `usecase_III_report.txt`. **PRD VIII** (model identity): `run_usecase_viii_identity.py` → `usecase_VIII_report.txt`, `run_identity.json`. **PRD IV** (contestability): `run_usecase_iv_contestability.py` → `usecase_IV_report.txt`. See [docs/findings/20260312_usecases_III_VIII_findings.md](../docs/findings/20260312_usecases_III_VIII_findings.md), [docs/findings/20260313_usecase_IV_findings.md](../docs/findings/20260313_usecase_IV_findings.md).

**Extended PRDs (extendedPRD.md):** PRD XII (Grace) stub: `run_grace_validation.py` → `grace_validation_report.txt`. PRD XIII (Supervisory Overload): `run_supervisory_overload_audit.py` → `supervisory_overload_report.txt`. PRD XIV (Drift Dashboard): `run_extended_drift_dashboard.py` → `extended_drift_report.txt`. PRD XVI: `validate_findings_sections.py` enforces 9 sections in findings docs. PRD XVII: `run_aaron_vs_plain_suite.py` → suite report + build_public_findings. PRD XV: `run_extended_contestability_legitimacy.py` → `extended_contestability_legitimacy_report.txt`. See [docs/prds/extendedPRD-index.md](../docs/prds/extendedPRD-index.md), [docs/findings/20260311_extendedPRD_findings.md](../docs/findings/20260311_extendedPRD_findings.md), [docs/findings/20260314_extendedPRD_XV_findings.md](../docs/findings/20260314_extendedPRD_XV_findings.md).

**Detailed findings reports:**
- [docs/findings/20260307_findings.md](../docs/findings/20260307_findings.md) — 2026-03-07: executive summary, expected vs actual by claim, testing/output breakdown, cross-cutting methodology.
- [docs/findings/20260308_findings.md](../docs/findings/20260308_findings.md) — 2026-03-08: testing framework coverage (all run scripts integration-tested), empirical families status, and **§5 What we learned** (methodological reflections: numerical stability, falsification semantics, integration tests as contract, stubs/deferred outcomes, traceability).
- [docs/findings/20260309_findings.md](../docs/findings/20260309_findings.md) — 2026-03-09: **testing and findings only** — objectives (claims under test), methods (test design, execution, coverage), results (suite outcome, BPO 6.1/6.4, empirical families, RCTI), analysis (expected vs actual, falsification status, PRD-11 replication/sensitivity), conclusions, limitations. Scientific method and PhD rigor; traceability to PRDs and artifacts.
- [docs/findings/20260310_usecases_findings.md](../docs/findings/20260310_usecases_findings.md) — 2026-03-10: **usecase PRD II** — scientific-method run: hypothesis, methods, public data (synthetic vs processed), baseline, outcomes, falsification, “wrong but impressive”; traceability to useccases.md and artifacts.
- [docs/findings/20260308_usecase2_synthetic_vs_public.md](../docs/findings/20260308_usecase2_synthetic_vs_public.md) — 2026-03-08: **usecase II synthetic vs public** — bootstrap by default, graph-structure null (row-sum-preserving rewire), top-degree leverage test; direct synthetic-vs-public comparison (D, CI, S_max, pass); 9-section findings.
- [docs/findings/20260308_final_usecase_build_findings.md](../docs/findings/20260308_final_usecase_build_findings.md) — 2026-03-08: **final usecase build** — PRD specification (finalusecase.md) in executive language; alignment with testing structure; findings update in academic review tone; traceability documented.
- [docs/findings/20260308_org_final_build_findings.md](../docs/findings/20260308_org_final_build_findings.md) — 2026-03-08: **org final build** — final applied use case build derived from org_use_Case.md; organizational coherence and fragmentation-stress validation mapped to run_usecase_ii_audit and run_nontrivial_boundary_public; PRD I/II mapping; findings in academic review tone; traceability documented.
- [docs/findings/20260308_organizational_empirical_validation_findings.md](../docs/findings/20260308_organizational_empirical_validation_findings.md) — 2026-03-08: **organizational empirical validation** — PRD Section 4.4 evidence categories and A8.1–A8.5; two critical deliverables (email-Eu-core Usecase II run, Enron time-windowed CF_t pipeline); implementation and integration tests; placeholder-resolution path; academic review tone.
- [docs/findings/20260308_hard_readiness_final_execution_pass.md](../docs/findings/20260308_hard_readiness_final_execution_pass.md) — 2026-03-08: **hard readiness + final execution pass** — staged real-backend Arm comparison completed; headline gate fails (null/leverage), direct no-go on superiority claim, dataset-by-dataset status, go/no-go table, and ordered last-mile execution tasks.
- [docs/findings/20260308_orgbench_backend_wiring.md](../docs/findings/20260308_orgbench_backend_wiring.md) — 2026-03-08: **OrgBench backend wiring** — staged runner supports OpenAI/Anthropic/Ollama with unchanged schema and strict/fallback behavior; invalid model/DNS failures are explicit, and canonical `claude-opus-4-6` smoke run executes with full identity logging.
- [docs/findings/20260308_orgbench_opus46_campaign.md](../docs/findings/20260308_orgbench_opus46_campaign.md) — 2026-03-08: **Opus 4.6 real-backend campaign** — validated Anthropic `claude-opus-4-6` identity logging and executed n=80 and n=200 multi-arm public phases; both failed null/leverage gates and remained `BLOCK_DEPLOYMENT`.
- [docs/findings/20260308_orgbench_failure_diagnosis_refresh.md](../docs/findings/20260308_orgbench_failure_diagnosis_refresh.md) — 2026-03-08: **failure diagnosis + release refresh** — task-level differential audit, Aaron activation audit, metric/null/leverage diagnosis, strict `BLOCK_DEPLOYMENT` refresh, and concrete next public-data run plan.
- [docs/findings/20260308_organizational_design_mapping_validation.md](../docs/findings/20260308_organizational_design_mapping_validation.md) — 2026-03-08: **PRD-30 organizational design mapping validation** — staged public run (`n=120`) generated full 8-artifact map bundle; Test A/F passed, Test B/C/D/E failed, and mapping claim remained locked (`decision=FAIL`).
- [docs/findings/20260308_org_design_mapping_diagnostics.md](../docs/findings/20260308_org_design_mapping_diagnostics.md) — 2026-03-08: **PRD-30 diagnostic + temporal completion pass** — failure interpretation, external diagnostic, objective ablation, perturbation breakdown, temporal corpus completion (email temporal + wiki temporal slice), and updated strict claim-lock verdict.
- [docs/findings/20260308_openclaw_skill_contract.md](../docs/findings/20260308_openclaw_skill_contract.md) — 2026-03-08: **OpenClaw skill contract** — added `skill/` package, `schemas/` contracts, and `export_openclaw_bundle.py`; live bundle validation passes while preserving `DO_NOT_PROMOTE` gate semantics and mandatory negative-result reporting.
- [docs/findings/20260308_openclaw_governance_operator.md](../docs/findings/20260308_openclaw_governance_operator.md) — 2026-03-08: **OpenClaw governance operator** — added actionable governance decision runner (`run_openclaw_governance_agent.py`) with machine-readable deployment recommendation (`BLOCK_DEPLOYMENT`/`LIMITED_SHADOW_ONLY`/`ALLOW_CONSTRAINED_DEPLOYMENT`) and owner-assigned remediation actions.
- [docs/findings/20260308_orgbench_public_campaign_findings.md](../docs/findings/20260308_orgbench_public_campaign_findings.md) — 2026-03-08: **OrgBench public campaign scaffold** — phased public Arm execution with OpenClaw governance gate; live run stopped on `BLOCK_DEPLOYMENT` due to null-gate failure, preserving falsification discipline.
- [docs/findings/20260311_extendedPRD_findings.md](../docs/findings/20260311_extendedPRD_findings.md) — 2026-03-11: **extended PRDs XII–XIV, XVI, XVII** — hypotheses, design, datasets, controls/baselines, nulls/outlier, results, falsification, limitations, next step; PRD XVI contract.
- [docs/findings/20260312_usecases_III_VIII_findings.md](../docs/findings/20260312_usecases_III_VIII_findings.md) — 2026-03-12: **usecase PRD III and VIII** — drift/lead-time benchmark (public data used, baseline, outcomes, falsification); model identity and reproducibility (run_identity.json, scientific-method report).
- [docs/findings/20260313_usecase_IV_findings.md](../docs/findings/20260313_usecase_IV_findings.md) — 2026-03-13: **usecase PRD IV** — contestability, provenance, responsibility (χ(d), reversal, unattributed residue); scientific-method report; public data = future (wiki-talk-temporal, GH Archive, Apache).
- [docs/findings/20260314_extendedPRD_XV_findings.md](../docs/findings/20260314_extendedPRD_XV_findings.md) — 2026-03-14: **extended PRD XV** — contestability and legitimacy field benchmark (what public data used, how/what/why, baseline, outcomes); structural proxy; 9-section findings.

**PRD-11 (Extended Testing Framework and Rigor):** Implemented in `src/boundary_org/extended_rigor.py` and `scripts/run_extended_rigor.py`. Report `extended_rigor_report.txt`: replication (multi-seed J_star mean/std, success_rate), sensitivity (vary n), negative-result checklist; pass = replication stable and checklist complete. See PRD-11 §9.

**PRD-16 (Adversarial and Domain-Grounded Falsification):** Implemented in `src/boundary_org/adversarial_audit.py` and `scripts/run_adversarial_audit.py`. Report `adversarial_audit_report.txt`: Adversarial checklist Q1–Q4 (reject trivial partition, construction robustness, beat baselines on real task, governance properties). Q1 from harness; Q2–Q4 "Not assessed" until multi-construction/real data. Pass = Q1 not Fail. See PRD-16 §6 and outputs/METHODOLOGY.md §6.2.

**thoughts3 (docs/thoughts3.md):** **PRD II (Null-Model and Rival-Theory Audit)** implemented in `src/boundary_org/null_rival_audit.py` and `scripts/run_null_rival_audit.py`. D(q) = Perf(q) − max(baselines ∪ nulls); nulls include random partition and label permutation; optional bootstrap CI. **PRD III (Outlier and Leverage Stability)** implemented in `src/boundary_org/leverage_stability.py` and `scripts/run_leverage_stability.py`. S(q) = max over node-drop and edge-drop of |Perf(q) − Perf(q^{−A})|; pass if S below threshold. **PRD VIII (Cross-Modal Sedation Replication)** implemented in `src/relational_closure/cross_modal_replication.py` and `scripts/run_cross_modal_replication.py`; report `cross_modal_replication_report.txt`; pass iff sign(ΔT_A)=sign(ΔT_B) (directionally consistent across modalities); falsification: modality-specific artifact. **PRD X (Human Confirmation-Bias Stress Test)** implemented in `src/boundary_org/confirmation_bias_stress.py` and `scripts/run_confirmation_bias_stress.py`; report `confirmation_bias_stress_report.txt`; challenge_rate_visible/quiet, false_reassurance_rate, rubber_stamping_falls; pass iff challenge rises when it should and rubber-stamping does not dominate. See [docs/prds/thoughts3-index.md](../docs/prds/thoughts3-index.md).

**Next PRDs (evidential separation and release discipline):** PRD-23 through PRD-29 are **implemented** (scripts, tests, reports). PRD-26: m_n vs outcomes, correlation in expected direction, null and graph-feature controls, out-of-sample. PRD-28: multiple constructions (raw, threshold, symmetrized), rank correlation of PE, fail if conclusions reverse. PRD-29: phased campaign execution with governance stop-on-block before promotion. See [docs/prds/](../docs/prds/) and [docs/thoughts2.md](../docs/thoughts2.md).

*Last updated from runs in outputs/runs/. Update this file when new runs alter empirical conclusions or falsification status.*
