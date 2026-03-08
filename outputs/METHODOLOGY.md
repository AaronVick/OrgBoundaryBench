# Methodology: Framework runs and scientific documentation

**Purpose:** Describe how verification and domain runs are conducted, how outputs are produced, and how they align with the paper and PRDs. This supports reproducibility, audit, and PhD-level documentation of findings.

**Source:** Vick (2025), PRD-00 (notation), PRD-04 (synthetic testing), PRD-06 (falsification), PRD-08 (reproducibility). See also `docs/METHODOLOGY.md` (traceability) and `docs/REPRODUCIBILITY.md` (commands and seeds).

---

## 1. Scientific method alignment

1. **Hypotheses / claims:** Each empirical claim is stated in the paper (Table 1) and PRD-00. Falsification conditions are operational (e.g. “AUC(closure) < AUC(Q) − 0.05” for E6.1).
2. **Test design:** Tests are specified in PRD-04 (Domain 6.1), PRD-05 (Tests A–H for 6.2–6.6), and `docs/TEST_SPEC.md` with expected outcomes and seeds.
3. **Execution:** Fixed seeds (TEST_SPEC, verification report script) ensure deterministic behavior. Environment and commands are documented in REPRODUCIBILITY.md.
4. **Analysis:** Verification report summarizes T3.2 (bound violations), T3.3 (decay ratio), T3.4 (greedy steps), E6.1 (AUC with bootstrap 95% CI). Baseline comparison is mandatory (PRD-06, Appendix A.9).
5. **Reporting:** Run report documents methodology, environment, results, findings, and claim status. Negative results are reported (PRD-06, PRD-09).

---

## 2. Run procedure (Domain 6.1 — synthetic)

1. **Environment:** Python ≥3.9; install with `pip install -e ".[test]"`. Optional: matplotlib for figures.
2. **Test suite:** `pytest tests/ -v --tb=short` (19 tests: estimators, theorems, synthetic, discrimination).
3. **Verification report:** `python scripts/generate_verification_report.py` → T3.2 (N=200, violations, max_ratio), T3.3 (max_decay_ratio), T3.4 (steps), E6.1 (AUC(E_cl), AUC(Q), bootstrap 95% CI, closure ≥ Q−0.05).
4. **Claim registry:** `python scripts/update_claim_registry.py --result pass|fail` updates last_result and last_run for MVP claims (T3.1–T3.4, E6.1).
5. **Figures (optional):** `python scripts/plot_mvp_figures.py` → closure arch (Fig 5), T3.2 scatter.
6. **Single entry:** `python scripts/run_verification.py [--all]` runs steps 2–5 as above.

---

## 3. Seeds and determinism

| Component | Seed(s) | Purpose |
|-----------|---------|---------|
| Unit tests (synthetic) | 1–5, 42, 123, 456, 789, 999, 98, 99 | Lumpable/non-lumpable generators |
| Theorem verification | 101, 202, 303, 404 | T3.1–T3.4 trials |
| Discrimination (E6.1) | 42, 123 | Lumpable vs perturbed; AUC |
| Verification report | 42 (main), 43 (bootstrap) | T3.2/T3.3/T3.4/E6.1 summary |
| Conjecture 10.1 probe | 44 | Ratio R sampling |

Same Python/NumPy version and seeds → same test outcomes and verification report (within floating-point). Bootstrap CIs may vary minimally across runs.

---

## 4. Traceability (paper → run output)

| Paper | Run output |
|-------|------------|
| Theorem 3.2 | verification_report: T3.2 violations, max_ratio |
| Theorem 3.3 | verification_report: T3.3 max_decay_ratio |
| Theorem 3.4 | verification_report: T3.4 steps; test_t34 |
| Estimator 5.1, E6.1 | verification_report: E6.1 AUC(E_cl), AUC(Q), CI; test_discrimination |
| Table 1 (claims) | claim_registry_snapshot: last_result, last_run per claim |
| Baseline [5] (modularity Q) | E6.1 comparison: AUC(Q) and closure ≥ Q−0.05 |

---

## 5. Public data (Domains 6.2–6.6)

When the data pipeline (PRD-01) is used:

- **Data source:** Document URL, version/date, citation (PRD-01 §2.3).
- **Kernel construction:** Document (S, K, μ, q) derivation per PRD-01 §2.5–2.6 (recipe).
- **Tests:** PRD-05 Tests A–H; run report documents which tests were run and on which source.
- **Findings:** Report pass/fail vs success criteria; report null or negative results (PRD-06, PRD-09).

### 5.1 Public-data run procedure (Domain 6.4 example)

1. **Acquire:** `python scripts/download_and_normalize.py [--source enron_snap] [--max-nodes N]` → downloads Enron SNAP edge list, builds LCC, optional degree-subgraph, writes `data/processed/enron_snap/kernel.npz` and `manifest.yaml`.
2. **Verify:** `python scripts/run_public_data_verification.py [--out path]` → loads kernel, computes q* (greedy T3.4) and Louvain [6] partition; reports E_cl, Q for each; writes public_data_report.txt.
3. **Document:** Run report cites manifest (URL, hash, n_used, kernel_recipe) and Test D results; notes presence/absence of org-chart for full Test D (precision/recall vs q_org).

---

## 6. Extended testing and public data (post-MVP)

- **PRD-11 (Extended Testing Framework and Rigor):** Replication runs, sensitivity analysis (seeds, subgraph size, N), effect-size and CI reporting, T3.2 sanity check on real-data kernels, and negative-result reporting checklist. Use for publication-ready runs.
- **PRD-12 (Expanded Public Data Catalog):** Additional citable public datasets (e.g. Karate, College football, EU email, OpenWorm) with kernel recipes and test mapping (Tests A–H). Extends PRD-01 §2.3 for broader domain coverage.

### 6.1 Cross-framework runs (Relational Closure / consciousness-topology)

When runs test the **second framework** — *Relational Closure and the Topology of Interiority* (Vick) — the same methodology applies (replication, sensitivity, effect sizes, negative-result reporting), with additional requirements from **PRD-13**:

- **Framework tag:** Run report must state `frameworks: [BPO]`, `[RelationalClosure]`, or `[BPO, RelationalClosure]`.
- **Claim set:** For Relational Closure, cite C1–C4, Tables 2–3, and which of F1–F5 were tested; document relational field construction, filtration type, S' for C2F, and matched-density / multi-construction compliance.
- **Falsification:** Report explicitly against F1–F5 (e.g. “F1 not triggered”; “F5: matched-density control applied”). See PRD-13 §3 for the full checklist.
- **Protocol:** When implementing the first empirical test (graded propofol + EEG), follow Appendix A of the consciousness-topology paper (neural pipeline, calibration of τ, δ, C2F cutoff, expected figures).

### 6.2 Empirical test families (PRD-17–22)

Each empirical PRD (17–22) defines tests that **can fail for the right reasons**, with five mandatory elements: falsification condition, trivial baseline, intervention test, governance metric (or N/A), and supervisor-relevant outcome. Pre-registered success/falsification criteria are documented in the PRDs; run outputs state pass/fail and whether topology or boundary machinery beat baselines.

| PRD | Family | Script | Output | Success / Falsification |
|-----|--------|--------|--------|--------------------------|
| **PRD-17** | Boundary Benchmark Harness (A) | `scripts/run_boundary_benchmark.py` | `boundary_benchmark_report.txt` | Success: q* non-trivial and J(q*) &lt; J(one_block), J(singleton), J(Louvain), mean J(random). Falsification: q* fails to beat trivial/standard baselines on J(q). |
| **PRD-21** | RCTI Comparative (E) | `scripts/run_rcti_comparative.py` | `rcti_comparative_report.txt` | Topology (C1, C4b, PE, C2F) and six graph baselines (density, clustering, reciprocity, modularity, spectral gap, entropy) per construction. Falsification: baselines outperform topology (PRD-21 §5). |
| **PRD-22** | Phase Monitoring (F) | `scripts/run_phase_monitoring.py` | `phase_monitoring_report.txt` | Trajectory: E_cl, n_blocks, NMI to previous q*; flags: rising_closure, abrupt_switch. Falsification: rising/abrupt do not correlate with later failure; or simpler indicators outperform (PRD-22 §5). |
| **PRD-18** | Governance Stress (B) | `scripts/run_governance_stress.py` | `governance_stress_report.txt` | Perturbation families (noise, missingness, workload_scale); E_cl and NMI under each; pass = majority of trials stable (NMI ≥ threshold). Falsification: boundary fails to remain near-optimal under pre-registered perturbations (PRD-18 §5). |
| **PRD-19** | Quiet Error Lab (C) | `scripts/run_quiet_error_lab.py` | `quiet_error_report.txt` | Planted errors (row_swap); detector = closure/partition change; detection_rate, false_reassurance_rate. Falsification: detection not above chance; false reassurance above threshold; rubber-stamping (PRD-19 §5). |
| **PRD-20** | Misalignment Engine (D) | `scripts/run_misalignment_engine.py` | `misalignment_report.txt` | q_pred (greedy on K), q_ctrl proxy (greedy on perturbed or Louvain); m_n = misalignment; stub outcomes. Falsification: m_n does not correlate with override/recovery/confusion; no better than trivial (PRD-20 §5). |
| **PRD-23** | Nontrivial Boundary on Public Labeled Graphs | `scripts/run_nontrivial_boundary_public.py` | `nontrivial_boundary_report.txt` | Leaderboard (J(q), one-block, singleton, q*, Louvain, spectral, random); external agreement (NMI, ARI, macro-F1 vs labels); meaningful vs useless. Falsification: q* trivial or agreement worse than all baselines (PRD-23 §4). |
| **PRD-24** | Incident-Coupled Phase Monitoring | `scripts/run_incident_phase_monitoring.py` | `incident_phase_report.txt` | Rolling m_cl, boundary switch; lead time to incident; false positive burden; density/entropy/spectral-gap drift baselines. Falsification: phase does not precede incidents, or baselines outperform (PRD-24 §4). |
| **PRD-25** | Governance Metrics on Real Appeals/Overrides | `scripts/run_governance_metrics.py` | `governance_metrics_report.txt` | Override latency, reversal success, unattributed residue, unresolved rate; χ(d) proxy. Pass only if challenge paths alter outcomes (PRD-25 §4). |
| **PRD-27** | RCTI Real Sedation Test | `scripts/run_rcti_sedation_test.py` | `rcti_sedation_report.txt` | Two+ constructions; AUC (topology vs six baselines) vs condition labels. Falsification: topology fails to beat or match baselines (PRD-27 §4). |
| **PRD-26** | Misalignment Outcome Validation | `scripts/run_misalignment_outcome_validation.py` | `misalignment_outcome_report.txt` | m_n per unit; correlation with override/recovery/confusion; null and graph-feature controls; out-of-sample. Falsification: m_n does not predict or controls dominate (PRD-26 §4). |
| **PRD-28** | Cross-Construction Invariance | `scripts/run_cross_construction_invariance.py` | `cross_construction_invariance_report.txt` | Multiple constructions; rank correlation of PE; fail if conclusions reverse. Falsification: signal is construction-artifact (PRD-28 §4). |
| **thoughts3 II** | Null-Model and Rival-Theory Audit | `scripts/run_null_rival_audit.py` | `null_rival_audit_report.txt` | D(q) = Perf(q) − max(baselines ∪ nulls); no claim unless D > 0; optional bootstrap CI. |
| **thoughts3 III** | Outlier and Leverage Stability | `scripts/run_leverage_stability.py` | `leverage_stability_report.txt` | S(q) = max \|Perf(q) − Perf(q^{−A})\| over node/edge drop; pass if S < threshold. |
| **thoughts3 VIII** | Cross-Modal Sedation Replication | `scripts/run_cross_modal_replication.py` | `cross_modal_replication_report.txt` | ΔT_A, ΔT_B per modality; pass iff sign(ΔT_A)=sign(ΔT_B). Falsification: direction reverses across modalities (modality-specific artifact). |
| **thoughts3 X** | Human Confirmation-Bias Stress Test | `scripts/run_confirmation_bias_stress.py` | `confirmation_bias_stress_report.txt` | challenge_rate_visible/quiet, false_reassurance_rate; pass iff challenge rises when it should and rubber-stamping falls. Falsification: confirmation bias (challenge does not rise; rubber-stamping dominates). |
| **PRD-11** | Extended Testing Framework and Rigor | `scripts/run_extended_rigor.py` | `extended_rigor_report.txt` | Replication (multi-seed), sensitivity (vary n), J_star mean/std; negative-result checklist. Pass = replication stable (success_rate ≥ 2/3) and checklist complete. Falsification: replication unstable or checklist incomplete (PRD-11 §9). |
| **PRD XII (buttonup)** | Findings and Outputs Publishing Layer | `scripts/build_public_findings.py` | `findings_summary.md`, `benchmark_leaderboard.csv`, `null_audit_summary.md`, `outlier_audit_summary.md`, `model_registry.csv`, `failure_gallery.md`, `dataset_provenance.md` | One command regenerates all public-facing summaries from run outputs; deterministic stubs when no runs. Acceptance: one command regenerates; negative results appear alongside positive (PRD XII buttonup). |
| **PRD-16** | Adversarial and Domain-Grounded Falsification | `scripts/run_adversarial_audit.py` | `adversarial_audit_report.txt` | Adversarial checklist Q1–Q4. Q1 = reject trivial partition; Q2–Q4 Not assessed until multi-construction/real data. Pass = Q1 not Fail. Falsification: PRD-16 §3. |
| **Usecase II (useccases.md)** | Null-Model, Rival-Theory, and Outlier Audit | `scripts/run_usecase_ii_audit.py` | `usecase_II_report.txt` |
| **Usecase III (useccases.md)** | Dynamic Drift, Failure Lead, and Recovery Benchmark | `scripts/run_usecase_iii_drift_benchmark.py` | `usecase_III_report.txt` |
| **Usecase IV (useccases.md)** | Contestability, Provenance, and Responsibility Benchmark | `scripts/run_usecase_iv_contestability.py` | `usecase_IV_report.txt` |
| **Usecase VIII (useccases.md)** | Model Identity, Reproducibility, and Dev-Test Logging | `scripts/run_usecase_viii_identity.py` | `usecase_VIII_report.txt`, `run_identity.json` | Combines null/rival audit (D = Perf(q*) − max(baselines ∪ nulls)) and leverage stability (S_max). Report includes Hypothesis, Methods, Public data used, Baseline, Outcomes, Falsification, and “What would make this look good but be wrong”. Pass = D &gt; 0 and S_max &lt; threshold. Falsification: useccases.md PRD II. |
| **PRD XII (extendedPRD)** | Grace Instrument Validation | `scripts/run_grace_validation.py` | `grace_validation_report.txt` | Multi-indicator stub; validation = future. |
| **PRD XIII (extendedPRD)** | Supervisory Overload Threshold | `scripts/run_supervisory_overload_audit.py` | `supervisory_overload_report.txt` | Workload bands; detection and false reassurance per band. |
| **PRD XIV (extendedPRD)** | Boundary Validity and Drift Dashboard | `scripts/run_extended_drift_dashboard.py` | `extended_drift_report.txt` | t ↦ E_cl,t; baselines (density/entropy/spectral-gap drift). |
| **PRD XVI (extendedPRD)** | Findings Scientific-Method Contract | `scripts/validate_findings_sections.py` | — | Validates findings docs have 9 required sections. |
| **PRD XV (extendedPRD)** | Contestability and Legitimacy Field Benchmark | `scripts/run_extended_contestability_legitimacy.py` | `extended_contestability_legitimacy_report.txt` |
| **PRD XVII (extendedPRD)** | Aaron-vs-Plain Use-Case Suite | `scripts/run_aaron_vs_plain_suite.py` | `aaron_vs_plain_suite_report.txt` | Boundary + null/rival + leverage; build_public_findings; arms = framework vs baselines. |
| **PRD-29** | Public OrgBench Campaign and Gated Release Orchestration | `scripts/run_orgbench_public_campaign.py` | `campaign_summary.json`, `campaign_summary.csv`, `campaign_summary.md` | Phase-by-phase node schedule, required Arm set, staged evaluation/audit/report per phase, OpenClaw export + governance decision, stop-on-block policy. |
| **OpenClaw governance operator** | Actionable deployment gate for governance role | `scripts/export_openclaw_bundle.py`, `scripts/run_openclaw_governance_agent.py` | `openclaw/report.json`, `openclaw/validation_report.json`, `openclaw/governance/governance_decision.json`, `openclaw/governance/governance_actions.jsonl` | Machine-readable contract + deployment recommendation (`BLOCK_DEPLOYMENT`, `LIMITED_SHADOW_ONLY`, `ALLOW_CONSTRAINED_DEPLOYMENT`) with owner-assigned remediations. |

**Script-level (integration) testing:** Each empirical run script (PRD-11, PRD-16, PRD-17–28, thoughts3 II–III, VIII, X, usecase II, III, IV, VIII, extendedPRD XII–XIV, XV, XVII), the findings publishing script (PRD XII buttonup), and the findings validator (PRD XVI), is tested end-to-end in `tests/test_empirical_scripts.py`: the script is executed with `--out-dir` to a temporary directory and the expected report file is asserted to exist and to contain key content (e.g. Leaderboard, pass, Summary). The BPO Domain 6.1 verification report script (`generate_verification_report.py`) is also integration-tested (output contains T3.2, T3.3, T3.4, E6.1). Public-data script (Domain 6.4) is tested to fail gracefully when kernel data is missing. No testing framework remains untested at the entry-point level.

## 7. References

- Vick (2025), `docs/Vick BoundaryPreservingOrganization 2025.pdf`
- `docs/METHODOLOGY.md`, `docs/REPRODUCIBILITY.md`, `docs/TEST_SPEC.md`
- `docs/prds/` (PRD-00, 01, 04, 05, 06, 08, **11**, **12**, **13**)
