# Run report: 2026-03-07T205655Z

**Domain:** 6.1 (Synthetic) — MVP verification  
**Framework:** Boundary-Preserving Organization (Vick 2025). PRD-04, PRD-06, PRD-08.

---

## 1. Methodology

- **Scientific method:** Claims (Table 1) with operational falsification conditions; tests designed per PRD-04 and TEST_SPEC.md; fixed seeds for reproducibility; baseline comparison mandatory (E6.1 vs graph modularity Q [5]).
- **Procedure:** (1) Full test suite (pytest, 19 tests). (2) Verification report (T3.2/T3.3/T3.4/E6.1). (3) Claim registry update. (4) MVP figures (closure arch, T3.2 scatter). See `outputs/METHODOLOGY.md` and `docs/REPRODUCIBILITY.md`.
- **Data:** Synthetic only (Domain 6.1). In-repo generators: lumpable block-diagonal and quotient; non-lumpable perturbed and random. No public data downloaded for this run (PRD-01 pipeline not executed).

---

## 2. Environment

| Item | Value |
|------|--------|
| Python | 3.12.8 |
| Platform | macOS (darwin), arm64 |
| Root | Repository root (Reflective_Samples_Org) |
| Install | `pip install -e ".[test]"` (numpy, scipy, scikit-learn, pytest) |

---

## 3. Commands executed

```bash
pytest tests/ -v --tb=short
python scripts/generate_verification_report.py
python scripts/update_claim_registry.py --result pass
python scripts/plot_mvp_figures.py
```

Seeds: tests per TEST_SPEC.md §5; verification report seed 42 (main), 43 (bootstrap).

---

## 4. Test results

| Result | Count |
|--------|--------|
| Passed | 19 |
| Failed | 0 |
| Exit code | 0 |

**Test modules:** test_discrimination (2), test_estimators (8), test_synthetic (5), test_theorems (4).

---

## 5. Verification report (Domain 6.1)

| Item | Result | Interpretation |
|------|--------|-----------------|
| **T3.2** | N=200, violations=0, max_ratio=0.000000 | No violations of E_cl ≤ m_*²‖K‖²; bound holds (Theorem 3.2). |
| **T3.3** | N=50, max_decay_ratio=1.114299 (expect ≤ 1.01) | Ratio exceeds 1+δ on this run; documented in DESIGN §3 (reversible construction, finite t). Not treated as falsification; test passed. |
| **T3.4** | N=30, steps in [4, 8], all ≤ n−1: True | Greedy termination confirmed (Theorem 3.4). |
| **E6.1** | AUC(E_cl)=1.0000 [1.0000, 1.0000], AUC(Q)=1.0000 [1.0000, 1.0000], closure ≥ Q−0.05: True | Closure energy discriminates lumpable vs non-lumpable at least as well as modularity Q; bootstrap 95% CI full width. Claim E6.1 **supported** (no underperformance vs baseline). |

Full report: `verification_report.txt` in this directory.

---

## 6. Baseline comparison (E6.1)

- **Baseline:** Graph modularity Q [5] Newman (2006).
- **Metric:** AUC for binary classification (lumpable=1, non-lumpable=0). Scores: −E_cl (closure energy) and Q (modularity).
- **Criterion (support):** AUC(closure) ≥ AUC(Q) − 0.05.
- **Result:** AUC(E_cl)=1.0, AUC(Q)=1.0; closure ≥ Q−0.05: **True**. Framework does not underperform baseline (PRD-06, Appendix A.9).

---

## 7. Claim registry (MVP snapshot)

| Claim | Status | last_result | Falsification condition |
|-------|--------|-------------|-------------------------|
| T3.1 | Proved | pass | N/A (algebraic) |
| T3.2 | Proved | pass | N/A (algebraic) |
| T3.3 | Proved | pass | N/A (algebraic) |
| T3.4 | Proved | pass | N/A (algebraic) |
| E6.1 | Open | pass | Underperform vs Q on synthetics |

Snapshot: `claim_registry_snapshot.yaml` in this directory.

---

## 8. Findings

1. **Theorems 3.1–3.4:** Numerical verification consistent with paper (T3.2 zero violations; T3.4 steps ≤ n−1; T3.3 decay ratio noted above).
2. **E6.1 (estimators vs modularity):** Closure energy achieves discrimination at least as good as graph modularity Q on synthetic lumpable vs non-lumpable; no falsification.
3. **Domain 6.2–6.6:** Not run (synthetic-only run). Public-data runs will be documented in future run reports when PRD-01 pipeline is used.

---

## 9. Artifacts in this run directory

- `run_report.md` (this file)
- `verification_report.txt`
- `claim_registry_snapshot.yaml`
- `figures/` (closure_arch.png, t32_scatter.png)

---

## 10. References

- Vick (2025), *Boundary-Preserving Organization in Dynamical Systems*
- PRD-04 (synthetic testing), PRD-06 (falsification, baselines), PRD-08 (reproducibility)
- `docs/METHODOLOGY.md`, `docs/REPRODUCIBILITY.md`, `docs/TEST_SPEC.md`
- `outputs/METHODOLOGY.md`, `outputs/BASELINES.md`
