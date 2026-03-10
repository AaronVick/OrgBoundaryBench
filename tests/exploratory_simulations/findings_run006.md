# Boundary Coherence Across Scales — Run 006 Findings

**Script:** `docs/exploratory_simulations/v3test_v006.py`  
**Run date:** 2026-03-10  
**Total runtime:** 224.4 s  
**Output dir:** `docs/exploratory_simulations/run006/`

Code and parameter changes from run 005 are documented in `CHANGELOG.md`. This report compares run 006 to runs 001–005.

---

## Summary

Run 006 implements the run005→006 priorities: **Exp1** focuses on **m=3 and m=4** with **800 trials per m** (1600 random), adds **spectral D_M** (2nd eigenvector of symmetrized K) so D_M = max(sampled, fixed, spectral), and runs greedy with **n=12** and **E_MIN=1e-22** (0 greedy retained). **Exp2** uses **quintiles**, **dual thresholds** (0.20 and 0.10), and **Cox-style** reporting (linear regression collapse_step~E0, odds ratio high vs low E0). **Exp3** adds **5-step skeleton** for **11 strategies** (Skel 1–5, Rand 1–3, Cen 1–3), **full 11×11 pairwise** win matrix, **Skel k vs Cen k / Rand k** for k=1..5, and strategy **frac E_final < 0.005 and < 0.001**. Results: **c* ≈ 0.31** (Exp1); **r = -0.77** and **Q5 collapse 23%** (Exp2); **Skel 5** has largest mean ΔE_cl; skeleton is roughly even with baselines at k=3 and loses at k=1,2,4,5 head-to-head.

---

## Changes from run 005 (reference)

| Item | Run 005 | Run 006 |
|------|---------|---------|
| **Exp1** m | 2,3,4 × 500 | **3,4 only × 800** |
| **Exp1** D_M | max(sampled, fixed) | **max(sampled, fixed, spectral)** |
| **Exp1** greedy | n=10, E_MIN=1e-18 | **n=12, E_MIN=1e-22** |
| **Exp2** bins | Quartiles | **Quintiles** |
| **Exp2** threshold | Single 0.15 | **Dual 0.20 and 0.10** |
| **Exp2** | hazard_ratio Q4/Q1 | **exp2_quintiles.csv, exp2_cox_style.json** (slope, OR) |
| **Exp3** steps | Skel 1–4 | **Skel 1–5** |
| **Exp3** strategies | 10 | **11** |
| **Exp3** pairwise | Key pairs CSV | **Full 11×11 matrix** + **Skel k vs Cen/Rand k** |
| **Exp3** E_final | frac < 0.01 | **+ frac < 0.005, < 0.001** |

---

## Experiment 1: OP 8.1 — m=3,4 × 800, Spectral D_M, Greedy n=12

**Config (v006):** n=10 (random), n_greedy=12 (greedy); N_per_m=800, M_VALS=[3,4]; D_M = max(mis_sampled, fixed_coarse_diameter, **spectral_diameter(K, pi, n)**); E_MIN_greedy=1e-22.  
**Runtime:** 87.0 s  

**Outcome:** **1600 random retained**, **0 greedy retained**.

### Drop reasons (run006)

| Reason      | Count |
|-------------|--------|
| E (greedy)  | 500    |
| ok_random   | 1600   |
| ok_greedy   | 0      |

### ratio_81 by mode and by m (random)

| q_mode | m_blocks | n_trials | ratio_81 max | ratio_81 mean | c* ≈   |
|--------|----------|----------|--------------|---------------|--------|
| random | —        | 1600     | **3.20**     | 0.82          | **0.31** |
| random | 3        | 800      | 2.24         | 0.73          | 0.45   |
| random | 4        | 800      | 3.20         | 0.91          | 0.31   |

**Implication:** Spectral D_M is in use; ratio_81 max remains ~3.2 (c* ≈ 0.31), consistent with run005. Focusing on m=3,4 with 800 per m gives tighter stats; greedy at n=12 still yields E below 1e-22 for all trials, so the greedy floor persists. Preliminary numerical support for a **positive lower bound** on misalignment diameter (c ≳ 0.31) in this regime holds.

---

## Experiment 2: Assumption 6.3 — Quintiles, Dual Threshold, Cox-Style

**Config (v006):** n2=8, N2=500, perturb_str=0.35, max_steps=50; **collapse_thresh 0.20 and 0.10**; **E0 quintiles**.  
**Runtime:** 2.2 s  

**Outcome:** **Q5 collapse 23%** (thresh 0.10) and **9%** (thresh 0.20); **r(E0, collapse_step) = -0.77**; Cox-style slope and odds ratio exported.

### Collapse by E0 quintile (threshold 0.10)

| E0_quintile | collapse_rate_010 | collapse_rate_020 | mean_steps | mean_E0   |
|-------------|-------------------|--------------------|------------|-----------|
| Q1          | 0.00              | 0.00               | 50.00      | 0.0108    |
| Q2          | 0.00              | 0.00               | 50.00      | 0.0208    |
| Q3          | 0.00              | 0.00               | 50.00      | 0.0324    |
| Q4          | 0.00              | 0.00               | 50.00      | 0.0524    |
| Q5          | **0.23**          | **0.09**           | 38.73      | 0.1568    |

- **Correlation** r(E0, collapse_step_010) = **-0.77** (strongest so far).
- **Cox-style (exp2_cox_style.json):** slope(collapse_step ~ E0) ≈ **-110**, r = -0.77, p ≈ 3.8e-98; odds_ratio_highE0_vs_lowE0 is very large (Q1–Q4 have 0% collapse).
- **Hazard ratio Q5/Q1** (thresh 0.10): Q1=0% → ratio undefined/large (only Q5 collapses).

**Implication:** Quintiles and dual thresholds sharpen the picture: collapse is **concentrated in the top E0 quintile**. Linear slope quantifies “per-unit increase in E0, collapse step decreases by ~110 steps per unit E0” (on this scale). Appendix-ready evidence for **perturbation vulnerability** of high-incoherence boundaries.

---

## Experiment 3: Coordination Skeleton — 11 Strategies, 5-Step, Full Pairwise

**Config (v006):** n3=8, nag3=6, N3=500; **5-step skeleton**; 11 strategies (Skel 1–5, Rand 1–3, Cen 1–3).  
**Runtime:** 135.0 s  

**Outcome:** **Skel 5** has the **largest mean ΔE_cl** (-0.00568); **Rand 1** has the **highest best_overall_pct** (16.4%). Skel k vs Cen k / Rand k: skeleton is roughly even at k=3 (~48–49%), weaker at k=1,2 and k=4,5.

### Strategy summary (excerpt: mean_dE, frac E<0.005, E<0.001, best_pct)

| strategy | mean_dE   | frac_E_below_0005 | frac_E_below_0001 | best_overall_pct |
|----------|-----------|-------------------|-------------------|------------------|
| Skel 1   | -0.00127  | 0.080             | 0.0               | 0.112            |
| Skel 2   | -0.00227  | 0.080             | 0.0               | 0.088            |
| Skel 3   | -0.00348  | 0.074             | 0.0               | 0.064            |
| Skel 4   | -0.00463  | 0.056             | 0.0               | 0.032            |
| **Skel 5**   | **-0.00568**  | 0.040             | 0.0               | 0.048            |
| **Rand 1**   | -0.00096  | 0.112             | 0.0               | **0.164**        |
| Rand 2   | -0.00209  | 0.080             | 0.0               | 0.086            |
| Rand 3   | -0.00334  | 0.070             | 0.0               | 0.086            |
| Cen 1    | -0.00096  | 0.092             | 0.0               | 0.128            |
| Cen 2    | -0.00188  | 0.096             | 0.0               | 0.116            |
| Cen 3    | -0.00265  | 0.076             | 0.0               | 0.134            |

### Skel k vs Cen k / Rand k (p_skel wins)

| k | p_skel_gt_cen | p_skel_gt_rand |
|---|----------------|----------------|
| 1 | 0.30           | 0.43           |
| 2 | 0.45           | 0.46           |
| 3 | **0.49**       | **0.48**       |
| 4 | 0.43           | 0.40           |
| 5 | 0.37           | 0.35           |

**Implication:** **Skeleton 5-step** gives the largest **average** closure-energy reduction, but **Rand 1** wins the most **individual** trials (best_overall_pct). Head-to-head: skeleton is **closest to baselines at k=3** (~48–49%); at k=1 it loses to both Cen and Rand; at k=4,5 it loses again. Supports a **nuanced** story: skeleton is best for **cumulative multi-step** gain; single-trial “best intervention” often goes to 1-step strategies (especially random/centrality). Full 11×11 pairwise matrix in `exp3_pairwise_matrix_11x11.csv` supports methods/appendix.

---

## Artifacts (run006)

| File                             | Path    | Description |
|----------------------------------|---------|-------------|
| exp1_op81.csv                    | run006/ | 1600 rows (q_mode, m_blocks, D_M_spectral, ratio_81, …) |
| exp1_drop_reasons.json           | run006/ | Drop counts |
| exp1_summary_by_mode.csv         | run006/ | Summary by mode and m |
| exp1_ratio81_hist_by_mode.png    | run006/ | Histograms by mode |
| exp2_hazard.csv                  | run006/ | 500 rows (collapse_step_020, _010, quintile) |
| exp2_quintiles.csv               | run006/ | Collapse rates by quintile (both thresholds) |
| exp2_hazard_ratio_quintiles.json | run006/ | Dual threshold, hazard Q5/Q1 |
| exp2_cox_style.json              | run006/ | Linear slope, r, p; odds ratio high vs low E0 |
| exp2_survival_by_quintile.csv    | run006/ | Survival by step × quintile |
| exp2_survival_curves_quintiles.png | run006/ | Survival curves (quintiles) |
| exp3_skeleton.csv                | run006/ | 500 rows (11 strategies) |
| exp3_pairwise_matrix_11x11.csv   | run006/ | Full 11×11 pairwise win rates |
| exp3_skel_k_vs_cen_rand.csv      | run006/ | Skel k vs Cen k / Rand k, k=1..5 |
| exp3_strategy_summary.csv        | run006/ | mean_dE, std_dE, frac E<0.01/0.005/0.001, best_pct |
| exp3_boxplot_data.csv            | run006/ | Long-form for 11 strategies |
| exp3_boxplot_dE.png              | run006/ | ΔE_cl by strategy |
| run_summary.json                 | run006/ | Run config and summary |

---

## Cross-run comparison (001–006)

| Metric                         | 001 | 002 | 003 | 004 | 005 | 006 |
|--------------------------------|-----|-----|-----|-----|-----|-----|
| Exp1 retained                  | 0   | 0   | 0   | 2000| 1500| **1600** |
| Exp1 ratio_81 max / c*         | —   | —   | —   | 3.02/0.33 | 3.23/0.31 | **3.20/0.31** |
| Exp1 D_M                       | —   | —   | —   | fixed+sampled | same | **+spectral** |
| Exp2 r(E0, collapse_step)      | -0.60| -0.27| -0.38| -0.69| -0.61| **-0.77** |
| Exp2 top-bin collapse          | 5%  | 1%  | 3.2%| 5.6%| 7.2%| **23% (Q5)** |
| Exp2 Cox-style                 | —   | —   | —   | —   | —   | **slope, OR** |
| Exp3 strategies                | 3   | 3   | 4   | 9   | 10  | **11** |
| Exp3 mean ΔE_cl best           | rand| rand| skel2| Cen3| Skel4| **Skel 5** |
| Exp3 best_overall leader       | —   | —   | —   | Skel1| Cen1| **Rand 1** |

---

## Recommendations for run007

1. **Exp1:** Try n=14 or n=16 for greedy only to see if any trials clear E_MIN; or run a **spectrum** of Dirichlet c (e.g. c∈[0.2,0.5], [1,2], [2.5,5]) and report ratio_81 by c_bin for boundary/falsification exploration.
2. **Exp2:** Add **E0 as continuous covariate** in a proper survival model (e.g. Cox PH) if software allows; or report **median collapse step by quintile** and hazard ratio at a second threshold (e.g. 0.05).
3. **Exp3:** Add **convergence criterion** (skeleton until ΔE < ε or max 6 steps) and compare “converged” vs fixed-step; report **full Skel k vs Cen k** for k=1..5 (Cen 4,5 can be defined as 4th/5th centrality step if desired); consider **weighted align_measure** (e.g. 60/40) as a sensitivity check.
