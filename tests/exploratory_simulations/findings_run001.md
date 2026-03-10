# Boundary Coherence Across Scales — Run 001 Findings

**Script:** `docs/exploratory_simulations/v3test.py`  
**Run date:** 2026-03-10  
**Total runtime:** ~19.2 s

---

## Summary

Single run of the fixed computational study (Experiments 1–3: OP 8.1, Assumption 6.3, Coordination Skeleton). Experiment 1 yielded **no valid trials** under the current filters; Experiments 2 and 3 completed and produced interpretable results.

---

## Experiment 1: Open Problem 8.1 — Lower Bound Search

**Config:** `n=6`, `n_ag=3`, `N1=800` trials  
**Runtime:** 9.2 s  

**Outcome:** **0 trials** retained.

Trials are dropped unless all of the following hold: `D_M > 1e-10`, `K2 > 1e-10`, `g > 1e-10`, `E > 1e-12`. In this run, every trial failed at least one of these (likely `D_M` from `mis_sampled` or the combination of `E`/`g`/`K2`), so no rows were written to `exp1_op81_fixed.csv`.

**Implication:** The fixed OP 8.1 pipeline is too strict for the current `(n, n_ag, N1)` and sampling. To get empirical lower-bound statistics (e.g. T3.2 check, OP 8.1 ratio, empirical c*), either:

- Relax or re-check the validity thresholds, or  
- Increase `N1` and/or adjust `n`/`n_ag`/Dirichlet `c` so more trials pass, or  
- Revisit `mis_sampled` (e.g. more samples `S`, or different `m`) so `D_M` is less often near zero.

---

## Experiment 2: Assumption 6.3 — Perturbation Hazard

**Config:** `n2=8`, `N2=400`, `collapse_thresh=0.30`, `max_steps=30`, `perturb_str=0.12`  
**Runtime:** 0.5 s  

**Outcome:** 400 trials completed; collapse was rare and concentrated in high initial closure energy.

### Collapse by E0 quartile

| E0_quartile | collapse_rate | mean_steps | mean_E0   |
|-------------|---------------|------------|-----------|
| Q1 (low)    | 0.00          | 30.00      | 0.0128    |
| Q2          | 0.00          | 30.00      | 0.0258    |
| Q3          | 0.00          | 30.00      | 0.0466    |
| Q4 (high)   | 0.05          | 28.55      | 0.1464    |

- **Correlation** `r(E0, collapse_step) = -0.5996`: higher initial closure energy is associated with earlier collapse (fewer steps to reach threshold when collapse occurs).
- Only the top quartile of E0 showed any collapses (5%); no collapses in Q1–Q3.

**Implication:** Consistent with Assumption 6.3: higher closure energy at the chosen partition is associated with greater perturbation hazard (faster collapse under repeated perturbation). The effect is present but weak at this perturbation strength and threshold; increasing `perturb_str` or run length might sharpen the signal.

**Artifacts:** `docs/exp2_hazard_fixed.csv` (400 rows).

---

## Experiment 3: Coordination Skeleton vs Baselines

**Config:** `n3=6`, `nag3=4`, `N3=300`  
**Runtime:** 5.1 s  

**Outcome:** Skeleton alignment did **not** outperform baselines on average in this run.

### Mean ΔE_cl reduction (positive = more closure energy reduction)

| Strategy   | Mean ΔE_cl  |
|-----------|-------------|
| Skeleton  | **-0.001901** |
| Random    | -0.002925   |
| Centrality| -0.002555   |

So on average, one-step alignment by the **skeleton** (max-misalignment pair) reduced closure energy **less** than both random and centrality-based alignment (more negative = larger reduction).

### Win rates

- Skeleton > Random: **55.0%**
- Skeleton > Centrality: **29.0%**
- Skeleton best overall (strictly better than both): **21.3%**

**Implication:** In this run the coordination skeleton was slightly better than random in pairwise comparison (55%) but much worse than centrality (29%), and rarely best overall (21.3%). So the “skeleton as best one-step target” hypothesis is not supported here; centrality-based targeting was stronger. Possible reasons: small `n3`/`nag3`, single-step horizon, or the particular random kernel/partition sampling. Re-runs or different hyperparameters may change the balance.

**Artifacts:** `docs/exp3_skeleton_fixed.csv` (300 rows).

---

## Artifacts

| File                        | Location        | Rows   |
|----------------------------|-----------------|--------|
| exp1_op81_fixed.csv        | `docs/`         | 0      |
| exp2_hazard_fixed.csv      | `docs/`         | 400    |
| exp3_skeleton_fixed.csv    | `docs/`         | 300    |

---

## Recommendations for next runs

1. **Experiment 1:** Relax or debug filters so some trials pass; consider larger `N1` or different `mis_sampled`/partition settings to get non-empty OP 8.1 statistics.
2. **Experiment 2:** Optionally increase `perturb_str` or steps to amplify collapse rate and clarify E0–hazard relationship.
3. **Experiment 3:** Try larger `n3`/`nag3`, more trials, or multi-step alignment to re-test whether skeleton ever dominates; consider reporting variance/quantiles as well as means.
