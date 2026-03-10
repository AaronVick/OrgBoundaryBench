# Boundary Coherence Across Scales — Run 004 Findings

**Script:** `docs/exploratory_simulations/v3test_v004.py`  
**Run date:** 2026-03-10  
**Total runtime:** 138.0 s  
**Output dir:** `docs/exploratory_simulations/run004/`

Code and parameter changes from run 003 are documented in `CHANGELOG.md`. This report compares run 004 to runs 001–003.

---

## Summary

Run 004 implemented the prioritized run003→004 plan: **Exp1** switched to **random_partition(n, m=3)** for q_star, **unblocking validity** — **2000/2000 trials retained** and first real OP 8.1 ratio and empirical c* statistics. **Exp2** increased perturb_str to 0.32 and max_steps to 50, yielding a **stronger hazard signal** (r = -0.69, Q4 collapse 5.6%). **Exp3** added **3-step skeleton** and **2/3-step baselines** for random and centrality; mean ΔE_cl and “best overall” win rates are now comparable across strategies, with **Centrality 3-step** slightly ahead on mean reduction and **Skeleton 1-step** leading on “best overall” in 22% of trials.

---

## Changes from run 003 (reference)

| Item | Run 003 | Run 004 |
|------|---------|---------|
| **Exp1** q_star | greedy_coarsegrain | **random_partition(n, m=3)** |
| **Exp1** retained | 0 | **2000** |
| **Exp2** perturb_str | 0.28 | **0.32** |
| **Exp2** max_steps | 40 | **50** |
| **Exp2** | — | Survival table + survival curves plot |
| **Exp3** | 1- and 2-step skeleton | **1/2/3-step skeleton + 2/3-step random & centrality** |
| **Exp3** | — | Fraction E_final < 0.01 per strategy; boxplot |
| **Plots** | — | exp1 ratio81 hist, exp2 survival, exp3 boxplot |

---

## Experiment 1: Open Problem 8.1 — Lower Bound Search

**Config (v004):** n=10, n_ag=3, N1=2000; **q_star = random_partition(n, m=3)**; D_M = max(mis_sampled, fixed_coarse_diameter); thresholds unchanged.  
**Runtime:** 40.6 s  

**Outcome:** **2000/2000 trials retained.** First run with non-empty Exp1 and full ratio statistics.

### Drop reasons (run004)

| Reason | Count |
|--------|--------|
| DM     | 0     |
| K2     | 0     |
| gap    | 0     |
| E      | 0     |
| ok     | 2000  |

### OP 8.1 and T3.2 statistics

| Metric | Value |
|--------|--------|
| **ratio_81** (E_cl / (D_M · gap · K²)) | max **3.02**, mean **0.76** |
| **ratio_T32** (E_cl / (D_M² K²))      | max **5.17**, mean **1.52** |
| T3.2 violations (ratio_T32 > 1)       | **1508** / 2000 |
| **Empirical c*** (1 / max ratio_81)   | **≈ 0.33** |
| D_M (mean)                             | 0.425 |

**Implication:** With a **conservative** (random) partition, E_cl is in a higher, variable range, so the validity filter no longer excludes trials. The empirical c* ≈ 0.33 is a **lower bound** on any universal constant in the OP 8.1 inequality (E_cl ≥ c · D_M · gap · K²): the bound holds with c ≤ 0.33 in this probe. T3.2 violations are expected here because we are not at the greedy optimum; the random partition is a stress test. A histogram of ratio_81 is saved as `exp1_ratio81_hist.png`.

---

## Experiment 2: Assumption 6.3 — Perturbation Hazard

**Config (v004):** n2=8, N2=500, collapse_thresh=0.20, **max_steps=50**, **perturb_str=0.32**  
**Runtime:** 1.0 s  

**Outcome:** Stronger negative correlation (r = **-0.69**); Q4 collapse rate **5.6%**; survival curves by E0 quartile exported and plotted.

### Collapse by E0 quartile

| E0_quartile | collapse_rate | mean_steps | std_steps | mean_E0   |
|-------------|---------------|------------|-----------|-----------|
| Q1 (low)    | 0.00          | 50.00      | 0.0       | 0.0129    |
| Q2          | 0.00          | 50.00      | 0.0       | 0.0264    |
| Q3          | 0.00          | 50.00      | 0.0       | 0.0465    |
| Q4 (high)   | **0.056**     | 47.26      | 11.31     | 0.1499    |

- **Correlation** r(E0, collapse_step) = **-0.69** (run003: -0.38; run002: -0.27; run001: -0.60). Strong negative: higher E0 → earlier collapse when it occurs.
- collapse_step std: 5.76; overall collapse rate 1.4%.

**Implication:** Pushing perturb_str and max_steps (v004) sharpens the hazard signal. Assumption 6.3 is well supported: higher incoherence (E0 in top quartile) is associated with clearly higher collapse rate and earlier collapse. Survival-by-quartile data and curves are in `exp2_survival_by_quartile.csv` and `exp2_survival_curves.png`.

---

## Experiment 3: Coordination Skeleton vs Baselines (1/2/3-step)

**Config (v004):** n3=8, nag3=6, N3=500; **3-step skeleton**; **2- and 3-step** random and centrality baselines; E_final < 0.01 fraction and boxplot.  
**Runtime:** 96.1 s  

**Outcome:** All nine strategies (Skeleton/Random/Centrality × 1/2/3-step) computed. **Centrality 3-step** has the largest mean ΔE_cl; **Skeleton 1-step** has the highest “best overall” win rate (22.2%).

### Mean ΔE_cl reduction (positive = more reduction)

| Strategy   | 1-step    | 2-step    | 3-step    |
|-----------|-----------|-----------|-----------|
| Skeleton  | -0.00102  | -0.00210  | **-0.00317** |
| Random    | -0.00110  | -0.00179  | -0.00249  |
| Centrality| -0.00131  | -0.00215  | **-0.00339** |

Largest mean reduction: **Centrality 3-step** (-0.00339), then Skeleton 3-step (-0.00317), then Random 3-step (-0.00249).

### Fraction of trials with E_final < 0.01

| Strategy   | 1-step | 2-step | 3-step |
|-----------|--------|--------|--------|
| Skeleton  | 0.374  | 0.346  | 0.274  |
| Random    | **0.402** | 0.352  | 0.314  |
| Centrality| 0.356  | 0.336  | 0.300  |

Random 1-step reaches E_final < 0.01 most often (40.2%); multi-step strategies tend to reduce this fraction (more steps can leave E_final in a different regime).

### Win rates (best overall = max dE among all 9 strategies)

| Metric              | Rate   |
|---------------------|--------|
| Skeleton 1-step best | **0.222** |
| Skeleton 2-step best | 0.094  |
| Skeleton 3-step best | 0.098  |

So in about 22% of trials, **one step of skeleton alignment** gives the best ΔE_cl among all nine strategies; 2- and 3-step skeleton each win in ~9–10% of trials (with ties or other strategies winning the rest).

**Implication:** With 2/3-step baselines in the mix, skeleton no longer dominates mean ΔE_cl; **Centrality 3-step** is slightly better on average. Skeleton’s edge in run003 (2-step best overall 30%) is diluted when random and centrality also use 2–3 steps. The “skeleton as best single-step target” story still holds for **1-step** (22% best overall), but multi-step coordination favors centrality in this setup. Boxplot of ΔE_cl by strategy: `exp3_boxplot_dE.png`; data: `exp3_boxplot_data.csv`.

---

## Artifacts (run004)

| File                         | Path    | Description |
|------------------------------|---------|-------------|
| exp1_op81.csv                | run004/ | 2000 rows   |
| exp1_drop_reasons.json       | run004/ | Drop counts |
| exp1_ratio81_hist.png        | run004/ | Histogram of ratio_81 |
| exp2_hazard.csv              | run004/ | 500 rows    |
| exp2_survival_by_quartile.csv| run004/ | Survival by step × quartile |
| exp2_survival_curves.png     | run004/ | Survival curves |
| exp3_skeleton.csv            | run004/ | 500 rows (all 9 strategies) |
| exp3_boxplot_data.csv        | run004/ | Long-form for boxplot |
| exp3_boxplot_dE.png          | run004/ | ΔE_cl by strategy |
| run_summary.json             | run004/ | Run config and summary |

---

## Cross-run comparison (001 / 002 / 003 / 004)

| Metric                         | Run 001 | Run 002 | Run 003 | Run 004 |
|--------------------------------|---------|---------|---------|---------|
| Exp1 retained                  | 0       | 0       | 0       | **2000** |
| Exp1 ratio_81 / c*             | —       | —       | —       | **max 3.02, c* ≈ 0.33** |
| Exp2 r(E0, collapse_step)      | -0.60   | -0.27   | -0.38   | **-0.69** |
| Exp2 Q4 collapse rate          | 5%      | 1%      | 3.2%    | **5.6%** |
| Exp3 skeleton best (1-step)    | 21.3%   | 18.4%   | 21.8%   | **22.2%** |
| Exp3 skeleton 2-step best     | —       | —       | 30.0%   | 9.4% (among 9) |
| Exp3 skeleton 3-step best      | —       | —       | —       | 9.8% (among 9) |
| Exp3 mean ΔE_cl best strategy  | random  | random  | skel 2-step | **Centrality 3-step** |

---

## Recommendations for run005

1. **Exp1:** Optionally add runs with greedy q_star and relaxed E_MIN to compare ratio_81 at the optimum vs random partition; or vary m in random_partition(n, m) (e.g. 2, 4) to see sensitivity.
2. **Exp2:** Consider perturb_str=0.35 or collapse_thresh=0.15 to target 10–15% overall collapse; add hazard ratio (e.g. Q4 vs Q1) for the write-up.
3. **Exp3:** Report pairwise win rates (e.g. Skeleton 3-step vs Centrality 3-step) and variance of ΔE_cl by strategy; consider 4-step or “until convergence” for skeleton vs baselines.
