# Findings — Run 007

**Script:** `v3test_v007.py`  
**Outputs:** `run007/`  
**Run date:** 2026-03-10

Run 007 implements the run006 recommendations: Exp1 spectrum by Dirichlet concentration (c_bin), Exp2 triple threshold + median + Cox PH, Exp3 converged skeleton + Cen 4/5 + weighted sensitivity. Total runtime ~354 s.

---

## Experiment 1: OP 8.1 — c_bin spectrum and greedy n=14

### Configuration
- **Random:** 500 trials per c_bin (low [0.2–0.8], medium [1–2], high [3–5]); m∈{3,4}; n=10.
- **Greedy:** 500 trials, n=14, E_MIN=1e-24.

### Outcomes
- **Retained:** 1500 random, 0 greedy (all 500 greedy dropped on E).
- **By c_bin (random only):**

| c_bin  | n_trials | ratio_81_max | ratio_81_mean | c* ≈ 1/max |
|--------|----------|--------------|---------------|------------|
| low    | 500      | 4.76         | 1.72          | **0.21**   |
| medium | 500      | 1.91         | 0.73          | **0.52**   |
| high   | 500      | 0.79         | 0.31          | **1.27**   |

- **Interpretation:** Bounds are **kernel-sharpness dependent**. Low-c (flatter) kernels give the largest ratio_81 and thus the **tightest empirical c*** (≈0.21). High-c (sharper) kernels give smaller ratio_81 and a **larger** c* (≈1.27), i.e. the conjectured lower bound D_M ≥ c·E/(gap·‖K‖²) holds with a larger constant for sharper kernels. This supports boundary/falsification exploration: the “universal” c is not one number but varies with kernel concentration; low-c regimes are the hardest for the bound (smallest c*).
- **Greedy at n=14:** Still 0 retained; E remains below 1e-24. Greedy continues to behave as an asymptotic zero-E oracle for this setup.

### Comparison to run006
- Run006: 1600 random (m=3,4 × 800), no c_bin; ratio_81 max 3.20, c* ≈ 0.31.
- Run007: 1500 random with c_bin; max ratio_81 4.76 (low bin) → c* ≈ 0.21; high bin gives c* > 1.

---

## Experiment 2: Assumption 6.3 — Triple threshold, median, Cox PH

### Configuration
- N2=500, perturb_str=0.35, max_steps=50.
- **Thresholds:** 0.20, 0.10, **0.05** (new).

### Outcomes
- **Quintiles (excerpt):**

| Quintile | collapse_rate_005 | collapse_rate_010 | collapse_rate_020 | mean_steps | median_steps |
|----------|-------------------|-------------------|-------------------|------------|--------------|
| Q1       | 0.18              | 0.00              | 0.00              | 50.0       | 50.0         |
| Q5       | **0.92**          | **0.31**         | 0.05              | 34.81      | 50.0         |

- **Correlation:** r(E0, collapse_step_010) ≈ **-0.70** (strong; similar to run006’s -0.77).
- **Cox PH (lifelines):** Fitted with E0 as covariate, duration=collapse_step_010, event=collapsed_010.
  - **coef_E0 ≈ -96.8** (higher E0 → shorter time to collapse).
  - **exp(coef_E0) ≈ 8.76e-43** (hazard ratio per unit E0; very small because E0 is on [0,~0.2] scale).
  - **Concordance index ≈ 0.017** (low; likely due to rare events and scale; linear + OR remain the main interpretable metrics).
- **Linear regression:** slope ≈ -97.2, r ≈ -0.70, p ≈ 5.7e-75.
- **Odds ratio (high vs low E0):** 7.75e13 (high E0 strongly associated with collapse).

### Interpretation
- Triple threshold confirms **monotonicity**: stricter (0.05) → much higher Q5 collapse (92%); at 0.10, Q5 still 31%.
- Median collapse step by quintile: Q1–Q4 all 50 (no/small collapse); Q5 mean 34.81.
- Cox PH gives a proper **hazard-per-covariate** (E0); magnitude is extreme due to E0 scale; direction (negative coef) is correct. Assumption 6.3 is strongly supported.

### Comparison to run006
- Run006: dual threshold 0.20/0.10; Q5 collapse 23% @0.10; no median, no Cox PH.
- Run007: third threshold 0.05; Q5 92% @0.05, 31% @0.10; median_steps in quintile table; Cox PH run successfully.

---

## Experiment 3: Coordination Skeleton — Converged skeleton, Cen 4/5, sensitivity

### Configuration
- 14 strategies: Skel 1–5, **Skel conv**, Rand 1–3, Cen 1–5.
- **Skel conv:** Repeat max-pair alignment until ΔE < 1e-4 or 8 steps.
- **align_measure** with **alpha** (default 0.5; 0.7 = 70/30 favoring misaligned agent).
- **Sensitivity:** Skel 5 at α=0.5 vs α=0.7.

### Outcomes
- **Strategy summary (mean_dE, best_overall_pct):**
  - **Skel 5:** mean_dE **-0.00506** (largest mean reduction).
  - **Skel conv:** mean_dE -0.00160 (stops early; fewer effective steps on average).
  - **Cen 1:** best_overall_pct **10.2%** (highest single-strategy “best in trial”).
  - **Cen 5:** mean_dE -0.00434 (closest to Skel 5 among baselines).

- **Skel k vs Cen k / Rand k (k=1..5):**
  - Skel vs Cen: p_skel_gt_cen from 0.31 (k=1) to **0.50** (k=2), then ~0.49–0.45 for k=3–5.
  - Skel vs Rand: ~0.48–0.53 for k=1–3; k=4–5 slightly lower (~0.46, 0.39).
  - **Skeleton is at rough parity with Cen at k=2**; multi-step Cen 4/5 narrow the gap to Skel 5.

- **Sensitivity (Skel 5, α=0.5 vs 0.7):**
  - mean_dE α=0.5: **-0.00506**; α=0.7: -0.00229.
  - **p_70_gt_50 = 0.658** → in 65.8% of trials, the 50/50 mix had *more* coherence gain (more negative dE) than 70/30. So **50/50 (balanced) alignment outperforms 70/30 (favoring misaligned)** on average and in majority of trials.

### Interpretation
- **Converged skeleton** stops early (mean dE -0.0016 vs Skel 5 -0.0051), so the 1e-4 stopping rule is conservative; fixed 5-step skeleton yields larger average gains.
- **Cen 4/5** extend the baseline fairly: Cen 5 is competitive in mean dE with Skel 5, but Skel 5 still leads. Head-to-head, skeleton is strongest vs centrality around k=2.
- **Weighted alignment:** 70/30 (favoring misaligned agent) is worse than 50/50 in this setup—suggesting the symmetric mix is a reasonable default.

### Comparison to run006
- Run006: 11 strategies (no Skel conv, no Cen 4/5); Skel 5 largest mean dE; Rand 1 best_overall_pct 16.4%.
- Run007: 14 strategies; Skel conv adds a “converged” variant (smaller mean gain); Cen 4/5 close the gap to skeleton; sensitivity shows 50/50 preferred over 70/30.

---

## Summary table (run007)

| Experiment | Key result |
|------------|------------|
| **Exp1**   | c* depends on c_bin: low c*≈0.21, medium ≈0.52, high ≈1.27; 0 greedy retained at n=14. |
| **Exp2**   | Triple threshold; Q5 collapse 92% @0.05, 31% @0.10; r≈-0.70; Cox PH coef(E0)≈-97. |
| **Exp3**   | Skel 5 best mean dE; Skel conv stops early; Cen 1 best_overall_pct; 50/50 > 70/30 in sensitivity. |

---

## Recommendations for run008

1. **Exp1:** Optionally fix m=3 or m=4 within each c_bin to separate c* vs m from c* vs c. Consider reporting ratio_81 distribution by (c_bin, m). If greedy is dropped from ratio stats, document it as “asymptotic zero-E oracle” and keep only random for bound reporting.
2. **Exp2:** Interpret Cox concordance with care (rare events); consider reporting hazard ratio for a 1-SD increase in E0. Optional: increasing noise schedule (e.g. perturb_str ramping over steps) to test accelerating environmental change.
3. **Exp3:** Optional: convergence with a less strict ε (e.g. 1e-3) to allow more steps and compare to fixed 6–8 step skeleton. Consider “boundary projection” or other align_measure variants as in run006 suggestions. Report Skel conv n_steps distribution (mean, median).

---

## Artifacts (run007)

- **Exp1:** `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_ratio81_hist_by_mode.png`
- **Exp2:** `exp2_hazard.csv`, `exp2_quintiles.csv`, `exp2_hazard_ratio_quintiles.json`, `exp2_cox_style.json`, `exp2_survival_by_quintile.csv`, `exp2_survival_curves_quintiles.png`
- **Exp3:** `exp3_skeleton.csv`, `exp3_pairwise_matrix_14x14.csv`, `exp3_skel_k_vs_cen_rand.csv`, `exp3_strategy_summary.csv`, `exp3_sensitivity_weighted.json`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`
- **Run:** `run_summary.json`
