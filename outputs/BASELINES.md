# Baselines: Comparison methods and criteria

**Purpose:** Document baseline methods used in framework testing and the criteria for “framework vs baseline” comparisons. Mandatory for any claim of practical value (paper Appendix A.9, PRD-06).

**Source:** Paper Table 1, PRD-06 §3 (Baseline Comparison Matrix), PRD-04 §4.1 (E6.1).

---

## 1. Domain 6.1 (Synthetic) — MVP

| Claim | Baseline | Metric | Criterion (support) | Falsification |
|-------|----------|--------|----------------------|----------------|
| **E6.1** Estimators recover ground truth | **Graph modularity Q** [5] Newman (2006) | AUC for discriminating lumpable vs non-lumpable | AUC(closure energy) ≥ AUC(Q) − 0.05 | Consistent underperformance vs Q on synthetic benchmarks |

**Implementation:** `baselines.graph_modularity_q(K, partition)`; Q = sum over communities of (e_cc − a_c²). Higher Q = more within-block density. Discrimination: binary labels (lumpable=1, non-lumpable=0); scores: −E_cl (higher = more lumpable) and Q (higher = more modular). AUC via `discrimination_auc(labels, scores)` (sklearn roc_auc_score).

**Verification report:** E6.1 line reports AUC(E_cl), AUC(Q), bootstrap 95% CI, and whether closure ≥ Q−0.05.

---

## 2. Domains 6.2–6.6 (post-MVP)

| Domain | Claim | Baseline | Metric | Criterion |
|--------|-------|----------|--------|-----------|
| 6.2, 6.4 | q* recovers modules / org units | **Louvain** [6] Blondel et al. | Precision, recall, NMI vs ground truth | Framework no worse than Louvain at matched coarseness |
| 6.2 | Misalignment tracks decoupling | — | Monotonicity of m̂_n with decoupling level | Spearman or sign consistency |
| 6.3 | Closure at designed partition | Random partition (same m) | Percentile of E_cl(q_design) vs E_cl(q_rand) | q_design in lower tail (e.g. <5th percentile) |
| 6.5 | Closure tracks transition | Null / shuffled | Effect size or p at transition | Detectable signature or report null |
| 6.6 | Neural state tracking | **Entropy / complexity** [8] Tononi | Correlation with outcome | Framework advantage over [8]; else falsification |

---

## 3. Conjectures

| Conjecture | Baseline / comparison | Criterion |
|------------|------------------------|-----------|
| 7.3 (B_ind intermediate density) | Replication across ER, BA, SBM | Interior maximum at ρ* consistent across ensembles |
| 10.1 (lower bound) | Numerical counterexample | min(R) < 0.01 → counterexample |

---

## 4. References

- [5] Newman (2006), modularity Q.
- [6] Blondel et al., Louvain.
- [8] Tononi, IIT / complexity.
- PRD-06 §3, PRD-04 §4.1, PRD-05 §7.
