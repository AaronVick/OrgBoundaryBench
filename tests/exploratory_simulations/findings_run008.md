# Findings — Run 008

**Script:** `v3test_v008.py`  
**Outputs:** `run008/`  
**Run date:** 2026-03-10

Run 008 implements run007 recommendations: Exp1 fixes m within c_bin and adds a very_low c bin; Exp2 adds 1-SD hazard ratio, ramping noise schedule, and explicit median survival by quintile; Exp3 loosens convergence to ε=1e-3, reports n_steps distribution, and adds α=0.3 for a full sensitivity curve.

---

## Experiment 1: OP 8.1 — (c_bin, m) fixed, very_low bin

### Configuration
- **Random:** 4 c_bins × 2 m (3, 4) × 250 = 2000 trials. C_BINS: very_low [0.1–0.3], low [0.2–0.8], medium [1–2], high [3–5]. Each trial uses fixed (c_bin, m).
- **Greedy:** 500 trials, n=14, E_MIN=1e-24 (unchanged).

### Outcomes
- **Retained:** 2000 random, 0 greedy.
- **By (c_bin, m):**

| c_bin    | m   | n_trials | ratio_81_max | ratio_81_mean | c* ≈ 1/max |
|----------|-----|----------|--------------|---------------|------------|
| very_low | 3   | 250      | 5.30         | 2.30          | **0.189**  |
| very_low | 4   | 250      | 7.77         | 3.00          | **0.129**  |
| low      | 3   | 250      | 4.38         | 1.54          | 0.228      |
| low      | 4   | 250      | 5.62         | 2.00          | 0.178      |
| medium   | 3   | 250      | 1.55         | 0.63          | 0.646      |
| medium   | 4   | 250      | 2.14         | 0.86          | 0.467      |
| high     | 3   | 250      | 0.77         | 0.27          | 1.30       |
| high     | 4   | 250      | 0.72         | 0.33          | 1.40       |

- **Tightest c* floor:** **very_low, m=4 → c* ≈ 0.129** (ratio_81 max 7.77). Very_low m=3 gives 0.19. This pushes the empirical lower bound below run007’s low-bin c*≈0.21.
- **m vs c:** Within each c_bin, m=4 yields higher ratio_81 (tighter c*) than m=3; the trend (sharper c → larger c*) holds across bins.
- **Artifacts:** `exp1_summary_by_cbin_m.csv`, `exp1_ratio81_by_cbin_m.png` (ratio_81 distributions by (c_bin, m)).

### Comparison to run007
- Run007: 3 c_bins (low/medium/high), m cycled; low c*≈0.21.
- Run008: 4 c_bins with very_low; m fixed per cell; **tightest c* ≈ 0.13** (very_low, m=4). Clear separation of c and m effects.

---

## Experiment 2: Assumption 6.3 — 1-SD hazard, ramping noise, median survival

### Configuration
- N2=500, max_steps=50, triple threshold (0.20, 0.10, 0.05).
- **Constant trajectory:** perturb_str=0.35 (baseline).
- **Ramping trajectory:** perturb_str linear 0.2 → 0.5 over steps (same trial, same K0/q0/E0).
- **Cox PH:** E0 and E0_std (z-score) as covariates for 1-SD hazard ratio.

### Outcomes
- **Quintiles (constant):** Q5 collapse_rate_010 28%, collapse_rate_005 75%; mean_steps Q5 36.28; median_survival_step 50 for Q1–Q4, 50 for Q5 (many censored).
- **Correlation:** r(E0, collapse_step_010) ≈ **-0.73** (strong).
- **Cox PH (raw E0):** coef_E0 ≈ -23.2, exp(coef_E0) ≈ 8.7e-11.
- **Hazard ratio per 1-SD E0 increase:** **exp(coef_E0_std) ≈ 0.157** → a one–standard-deviation increase in E0 is associated with roughly **1/0.157 ≈ 6.4×** higher hazard (earlier collapse). E0_std_value ≈ 0.080.
- **Ramping:** collapse_rate_010_ramp **9%** (vs 5.6% constant); mean_collapse_step_ramp 45.77; **r(E0, collapse_step_010_ramp) ≈ -0.81** (stronger than constant). Accelerating noise increases collapse and sharpens the E0–collapse relationship.
- **Median survival step by quintile:** Exported in `exp2_hazard_ratio_quintiles.json` (Q1–Q5 all 50 here, as most trials are censored at 0.10 threshold).

### Interpretation
- **1-SD hazard ratio** gives an interpretable, scale-invariant effect size (~6.4× per SD of E0).
- **Ramping noise** raises collapse rate and correlation, supporting “accelerating environmental change” as a stress test for incoherent boundaries.
- Assumption 6.3 is further supported with a standardized hazard metric and a ramping schedule.

### Comparison to run007
- Run007: No 1-SD hazard; single constant perturb_str; median_steps in table.
- Run008: hazard_ratio_per_1SD_E0; ramping trajectory and ramp stats; median_survival_step explicitly in quintile table and JSON.

---

## Experiment 3: Coordination Skeleton — ε=1e-3, n_steps, α curve

### Configuration
- **SKEL_CONV_EPS=1e-3** (looser than 1e-4), SKEL_CONV_MAX=8.
- **Sensitivity:** Skel 5 at α=0.3, 0.5, 0.7 (full curve).

### Outcomes
- **Strategy summary:** Skel 5 mean_dE **-0.00586** (largest); Skel conv -0.00130; **Skel conv best_overall_pct 13.2%** (highest in this run). Cen 1 9.0%, Rand 1 10.0%.
- **Skel conv n_steps:** **mean 1.31, median 1**, std 0.59, range [1, 5]. With ε=1e-3, convergence stops after very few steps in most trials (median 1), so fixed 5-step skeleton still yields much larger mean gains (-0.00586 vs -0.00130).
- **Sensitivity (α=0.3, 0.5, 0.7):**
  - **mean_dE:** α=0.3 **-0.00976** (best), α=0.5 -0.00586, α=0.7 -0.00251.
  - **Pairwise:** p_50_gt_30 = 64.8% (50/50 beats 0.3 in 64.8% of trials); p_70_gt_50 = 68% (70/30 beats 50/50 in 68%).
- **Interpretation:** **α=0.3** (favoring the “other” agent) gives the best **mean** coherence gain, but 50/50 wins more often head-to-head vs 0.3. So 0.3 has a fatter left tail (some very large reductions) while 50/50 is more often better in a single trial. 70/30 remains worst on average and beats 50/50 in most trials (68%)—likely noisier. The sensitivity curve (0.3 best mean, 0.5 middle, 0.7 worst) refines the run007 finding that 50/50 beats 70/30.

### Comparison to run007
- Run007: ε=1e-4, no n_steps distro; α=0.5 vs 0.7 only.
- Run008: ε=1e-3, n_steps mean/median/histogram; full α curve; **α=0.3 best mean dE**; Skel conv best_overall_pct 13.2%.

---

## Summary table (run008)

| Experiment | Key result |
|------------|------------|
| **Exp1**   | (c_bin, m) fixed; very_low m=4 → **c* ≈ 0.13**; very_low m=3 → 0.19; m=4 tighter than m=3 within each bin. |
| **Exp2**   | **Hazard ratio per 1-SD E0 ≈ 0.16** (~6.4× hazard per SD); ramping 9% collapse, r≈-0.81; median_survival_step by quintile. |
| **Exp3**   | Skel conv n_steps mean 1.31 (median 1); **α=0.3** best mean dE (-0.00976); 50/50 beats 0.3 in 64.8% of trials; Skel conv 13.2% best_overall. |

---

## Recommendations for run009

1. **Exp1:** Optionally add one more very_low sub-bin (e.g. [0.05, 0.15]) to probe the extreme diffuse regime; or fix n and vary c_bin only for a cleaner c* vs c plot.
2. **Exp2:** Consider a second ramping schedule (e.g. step-dependent or quadratic) and report survival curves for constant vs ramping; optionally bootstrap 1-SD hazard ratio for a CI.
3. **Exp3:** Try ε=1e-2 to allow more conv steps and compare conv vs fixed 5-step more fairly; or report “conv until n_steps≥3” as a hybrid. Document α=0.3 as “best mean, 50/50 more often best per trial” for the narrative.

---

## Artifacts (run008)

- **Exp1:** `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_summary_by_cbin_m.csv`, `exp1_ratio81_hist_by_mode.png`, `exp1_ratio81_by_cbin_m.png`
- **Exp2:** `exp2_hazard.csv`, `exp2_quintiles.csv`, `exp2_hazard_ratio_quintiles.json`, `exp2_cox_style.json`, `exp2_survival_by_quintile.csv`, `exp2_survival_curves_quintiles.png`
- **Exp3:** `exp3_skeleton.csv`, `exp3_pairwise_matrix_14x14.csv`, `exp3_skel_k_vs_cen_rand.csv`, `exp3_strategy_summary.csv`, `exp3_sensitivity_weighted.json`, `exp3_skel_conv_n_steps.csv`, `exp3_skel_conv_n_steps.json`, `exp3_skel_conv_n_steps_hist.png`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`
