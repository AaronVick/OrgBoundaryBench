# Boundary Coherence Across Scales — Run 005 Findings

**Script:** `docs/exploratory_simulations/v3test_v005.py`  
**Run date:** 2026-03-10  
**Total runtime:** 161.6 s  
**Output dir:** `docs/exploratory_simulations/run005/`

Code and parameter changes from run 004 are documented in `CHANGELOG.md`. This report compares run 005 to runs 001–004.

---

## Summary

Run 005 implemented run004 recommendations and added enhancements: **Exp1** runs in **dual mode** — random partitions with m∈{2,3,4} (500 each, 1500 retained) and greedy partitions with relaxed E_MIN (500 trials; 0 retained, all E below 1e-18). Sensitivity of ratio_81 to m is reported; c* ≈ 0.31 for random. **Exp2** uses stronger perturbation (perturb_str=0.35, collapse_thresh=0.15), yielding **7.2% Q4 collapse** and **hazard ratio** (Q4 vs Q1) exported. **Exp3** adds **4-step skeleton** and reports **10 strategies** (Skel 1–4, Rand 1–3, Cen 1–3) with **pairwise win rates** and a **strategy summary** (mean, std, frac E<0.01, best_overall_pct). **Skeleton 4-step** has the largest mean ΔE_cl; **Centrality 1-step** has the highest share of “best overall” in a trial.

---

## Changes from run 004 (reference)

| Item | Run 004 | Run 005 |
|------|---------|---------|
| **Exp1** | random m=3 only, 2000 trials | **Dual-mode:** random m=2,3,4 (500 each) + greedy 500; q_mode, m_blocks in CSV |
| **Exp1** | single hist | **exp1_summary_by_mode.csv**; hist **by mode** (random vs greedy) |
| **Exp2** | perturb_str=0.32, thresh=0.20 | **perturb_str=0.35**, **collapse_thresh=0.15** |
| **Exp2** | — | **exp2_hazard_ratio.json** (Q4/Q1 collapse rate) |
| **Exp3** | 9 strategies (Skel 1–3, Rand 1–3, Cen 1–3) | **10 strategies:** **Skel 4** added |
| **Exp3** | — | **exp3_pairwise_win_rates.csv**; **exp3_strategy_summary.csv** (mean, std, frac E<0.01, best_pct) |
| **Exp3** | 9-strategy boxplot | **10-strategy** boxplot |

---

## Experiment 1: Open Problem 8.1 — Dual-Mode (Random m=2,3,4 + Greedy)

**Config (v005):** n=10, N1_random=1500 (m=2,3,4 × 500), N1_greedy=500; E_MIN_random=1e-14, E_MIN_greedy=1e-18.  
**Runtime:** 43.6 s  

**Outcome:** **1500 random retained**, **0 greedy retained** (all greedy trials had E ≤ 1e-18).

### Drop reasons (run005)

| Reason      | Count |
|------------|--------|
| E (greedy) | 500    |
| ok_random  | 1500   |
| ok_greedy  | 0      |

### ratio_81 by mode and by m (random)

| q_mode | m_blocks | n_trials | ratio_81 max | ratio_81 mean | c* ≈   |
|--------|----------|----------|--------------|---------------|--------|
| random | —        | 1500     | **3.23**     | 0.74          | **0.31** |
| random | 2        | 500      | 1.54         | 0.45          | 0.65   |
| random | 3        | 500      | 2.78         | 0.78          | 0.36   |
| random | 4        | 500      | 3.23         | 0.99          | 0.31   |

**Implication:** **Sensitivity to m:** more blocks (m=4) yield higher ratio_81 (max 3.23, mean 0.99) than m=2 (max 1.54, mean 0.45). Empirical c* ≈ 0.31 for the random mode. Greedy mode again produced E below 1e-18 for every trial, so no greedy ratio_81 statistics; the dual-mode design is documented for future runs (e.g. even lower E_MIN or different n).

---

## Experiment 2: Assumption 6.3 — Perturbation Hazard

**Config (v005):** n2=8, N2=500, **collapse_thresh=0.15**, max_steps=50, **perturb_str=0.35**  
**Runtime:** 1.0 s  

**Outcome:** **7.2% Q4 collapse** (up from 5.6% in run004); r(E0, collapse_step) = **-0.61**; **hazard ratio** (Q4 vs Q1) exported (Q1=0, so ratio is large / undefined in the usual sense).

### Collapse by E0 quartile

| E0_quartile | collapse_rate | mean_steps | std_steps | mean_E0   |
|-------------|---------------|------------|-----------|-----------|
| Q1 (low)    | 0.00          | 50.00      | 0.0       | 0.0136    |
| Q2          | 0.00          | 50.00      | 0.0       | 0.0273    |
| Q3          | 0.00          | 50.00      | 0.0       | 0.0443    |
| Q4 (high)   | **0.072**     | 46.47      | 12.72     | 0.1359    |

- **Correlation** r(E0, collapse_step) = **-0.61** (run004: -0.69). Strong negative: higher E0 → earlier collapse.
- **Hazard ratio (Q4/Q1):** Q4 collapse 7.2%, Q1 collapse 0% → ratio not defined numerically (exported as large value); only Q4 shows collapses, consistent with Assumption 6.3.

**Implication:** Stronger perturbation and lower threshold increase Q4 collapse to 7.2%. The “higher E0 → more hazard” story holds; hazard_ratio.json supports methods/appendix reporting.

---

## Experiment 3: Coordination Skeleton — 10 Strategies, Pairwise, Summary

**Config (v005):** n3=8, nag3=6, N3=500; **4-step skeleton**; 10 strategies (Skel 1–4, Rand 1–3, Cen 1–3).  
**Runtime:** 116.8 s  

**Outcome:** **Skeleton 4-step** has the **largest mean ΔE_cl** (-0.00407); **Centrality 1-step** has the **highest best_overall_pct** (17.6%). Pairwise win rates and full strategy summary exported.

### Strategy summary (mean_dE, std_dE, frac E<0.01, best_overall_pct)

| strategy | mean_dE   | std_dE | frac_E_below_001 | best_overall_pct |
|----------|-----------|--------|-------------------|------------------|
| Skel 1   | -0.00103  | 0.00323| 0.392             | 0.118            |
| Skel 2   | -0.00223  | 0.00483| 0.336             | 0.068            |
| Skel 3   | -0.00306  | 0.00586| 0.310             | 0.064            |
| **Skel 4**   | **-0.00407**  | 0.00703| 0.300             | 0.078            |
| Rand 1   | -0.00118  | 0.00331| 0.386             | 0.124            |
| Rand 2   | -0.00240  | 0.00487| 0.348             | 0.076            |
| Rand 3   | -0.00346  | 0.00601| 0.300             | 0.084            |
| **Cen 1**   | -0.00076  | 0.00326| **0.424**         | **0.176**        |
| Cen 2    | -0.00146  | 0.00452| 0.390             | 0.142            |
| Cen 3    | -0.00227  | 0.00543| 0.370             | 0.130            |

### Pairwise win rates (key pairs)

| strategy_a      | strategy_b      | p_a_wins | p_b_wins |
|-----------------|------------------|----------|----------|
| dE_skeleton_3   | dE_centrality_3  | 0.442    | 0.556    |
| dE_skeleton_3   | dE_random_3      | 0.518    | 0.482    |
| dE_skeleton_4   | dE_centrality_3  | 0.408    | 0.592    |
| dE_skeleton_4   | dE_random_3      | 0.464    | 0.536    |
| dE_skeleton_4   | dE_skeleton_3    | 0.362    | 0.638    |

- **Skel 4-step best overall:** 7.8% of trials (max dE among 10 strategies).
- **P(Skel 3 > Cen 3)** = 44.2%; **P(Skel 4 > Cen 3)** = 40.8% (Centrality 3-step wins more often head-to-head).
- **P(Skel 3 > Rand 3)** = 51.8% (skeleton 3-step slightly ahead of random 3-step).

**Implication:** Adding a 4th step gives skeleton the **largest mean closure-energy reduction**, but “best overall” in a given trial is often a 1-step strategy (Cen 1, Rand 1, Skel 1). Pairwise, **Centrality 3-step** beats Skeleton 3- and 4-step in most trials; Skeleton 3-step beats Random 3-step in a slight majority. The full strategy summary and pairwise tables support a nuanced methods narrative.

---

## Artifacts (run005)

| File                         | Path    | Description |
|------------------------------|---------|-------------|
| exp1_op81.csv                | run005/ | 1500 rows (q_mode, m_blocks, ratio_81, …) |
| exp1_drop_reasons.json       | run005/ | Drop counts |
| exp1_summary_by_mode.csv     | run005/ | Summary by q_mode and m_blocks |
| exp1_ratio81_hist_by_mode.png| run005/ | Histograms random vs greedy |
| exp2_hazard.csv               | run005/ | 500 rows |
| exp2_hazard_ratio.json       | run005/ | Q4/Q1 collapse, hazard_ratio |
| exp2_survival_by_quartile.csv| run005/ | Survival by step × quartile |
| exp2_survival_curves.png     | run005/ | Survival curves |
| exp3_skeleton.csv            | run005/ | 500 rows (10 strategies) |
| exp3_pairwise_win_rates.csv  | run005/ | Key pairwise p_a_wins, p_b_wins |
| exp3_strategy_summary.csv    | run005/ | mean_dE, std_dE, frac_E_below_001, best_overall_pct |
| exp3_boxplot_data.csv        | run005/ | Long-form for 10 strategies |
| exp3_boxplot_dE.png          | run005/ | ΔE_cl by strategy |
| run_summary.json             | run005/ | Run config and summary |

---

## Cross-run comparison (001 / 002 / 003 / 004 / 005)

| Metric                         | Run 001 | Run 002 | Run 003 | Run 004 | Run 005 |
|--------------------------------|---------|---------|---------|---------|---------|
| Exp1 retained                  | 0       | 0       | 0       | 2000    | **1500** (random only) |
| Exp1 ratio_81 / c*             | —       | —       | —       | max 3.02, c*≈0.33 | **by m: 1.54–3.23, c*≈0.31** |
| Exp2 r(E0, collapse_step)      | -0.60   | -0.27   | -0.38   | -0.69   | **-0.61** |
| Exp2 Q4 collapse rate         | 5%      | 1%      | 3.2%    | 5.6%    | **7.2%** |
| Exp2 hazard ratio (Q4/Q1)     | —       | —       | —       | —       | **exported (Q1=0)** |
| Exp3 strategies                | 3       | 3       | 4       | 9       | **10** (Skel 4) |
| Exp3 mean ΔE_cl best           | random  | random  | skel 2  | Cen 3   | **Skel 4** |
| Exp3 best_overall leader       | —       | —       | —       | Skel 1  | **Cen 1** (17.6%) |

---

## Recommendations for run006

1. **Exp1:** Try E_MIN_greedy=1e-20 or n=12 to get a non-empty greedy sample; or fix m=2 and m=4 only with larger N for tighter ratio_81 confidence intervals.
2. **Exp2:** Add a second threshold (e.g. 0.10) and report hazard ratio for “early” vs “late” collapse; or E0 quintiles for finer survival.
3. **Exp3:** Report full pairwise matrix (all 10×10) or “Skel k vs Cen k” for k=1,2,3,4; consider 5-step or convergence loop for skeleton vs baselines.
