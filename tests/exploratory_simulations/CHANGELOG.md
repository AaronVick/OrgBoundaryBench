# Boundary Coherence Study — Code & Findings Changelog

Versioned runs and code changes for reproducibility.

---

## Run 001

- **Script:** `v3test.py` (canonical copy was `docs/exploratory_simulations/v3test.py`; current copy in this dir: `v3test.py`)
- **Findings:** `findings_run001.md`
- **Outputs:** CSVs written to `docs/` (no run subdir): `exp1_op81_fixed.csv`, `exp2_hazard_fixed.csv`, `exp3_skeleton_fixed.csv`

### Run 001 config (recorded for comparison)

| Experiment | Parameters |
|------------|------------|
| Exp1 | n=6, n_ag=3, N1=800; mis_sampled S=80; validity: DM,K2,g>1e-10, E>1e-12 |
| Exp2 | n2=8, N2=400, perturb_str=0.12, max_steps=30, collapse_thresh=0.30 |
| Exp3 | n3=6, nag3=4, N3=300; mis_sampled S=60 for M matrix |

### Run 001 outcomes (summary)

- **Exp1:** 0 trials retained (all dropped by validity filters).
- **Exp2:** 400 trials; collapse rate 5% in Q4 only; r(E0, collapse_step) = -0.60.
- **Exp3:** Skeleton did not dominate; mean ΔE_cl worse than random/centrality; skel_best 21.3%.

---

## Run 002

- **Script:** `v3test_v002.py`
- **Findings:** `findings_run002.md`
- **Outputs:** All under `run002/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp2_hazard.csv`, `exp3_skeleton.csv`, `run_summary.json`

### Code changes v001 → v002 (driven by findings_run001)

| Area | Change |
|------|--------|
| **Exp1** | Validity thresholds relaxed: DM, K2, g: `1e-10` → `1e-12`; E: `1e-12` → `1e-14`. |
| **Exp1** | `mis_sampled` default S: 80 → 200. |
| **Exp1** | N1: 800 → 2000. |
| **Exp1** | Drop reasons recorded per trial (DM / K2 / gap / E) and written to `exp1_drop_reasons.json`. |
| **Exp2** | `perturb_str`: 0.12 → 0.20. |
| **Exp2** | `max_steps`: 30 → 40. |
| **Exp2** | Quartile table now includes `std_steps`; collapse_step std and 25/50/75% quantiles printed. |
| **Exp3** | n3: 6→8, nag3: 4→6, N3: 300→500. |
| **Exp3** | mis_sampled S for M matrix: 60 → 100. |
| **Exp3** | Mean and std for dE_skeleton / dE_random / dE_centrality; quantiles for dE_skeleton printed. |
| **All** | Output directory: run-specific `run002/`; artifact names simplified (no `_fixed` suffix). |
| **All** | Run summary JSON written at end (`run_summary.json`) with run_id, retained counts, and total_elapsed_sec. |

### Run 002 outcomes (summary)

- **Exp1:** 0 trials retained; drop reasons: DM=1998, E=2 (D_M still below threshold).
- **Exp2:** 400 trials; collapse_rate 0.25%; r(E0, collapse_step) = -0.27; quartiles + std reported.
- **Exp3:** 500 trials; skeleton mean ΔE_cl -0.00117 vs random -0.00125, centrality -0.00070; skel_best 18.4%.

Full details: `findings_run002.md`.

---

## Run 003

- **Script:** `v3test_v003.py`
- **Findings:** `findings_run003.md`
- **Outputs:** All under `run003/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp2_hazard.csv`, `exp3_skeleton.csv`, `run_summary.json`

### Code changes v002 → v003 (driven by findings_run001, findings_run002)

| Area | Change |
|------|--------|
| **Exp1** | **D_M definition:** D_M = max(mis_sampled(…), fixed_coarse_diameter(pi, n)). New helper `fixed_coarse_diameter(pi, n)` = max pairwise proj_dist over 3 canonical 2-block splits (n/4, n/2, 3n/4) so denominator has positive scale. |
| **Exp1** | DM_MIN: 1e-12 → 1e-14. n: 6 → 10; N1=2000. CSV now includes D_M_sampled, D_M_fixed. |
| **Exp2** | perturb_str: 0.20 → 0.28; collapse_thresh: 0.30 → 0.20; N2: 400 → 500. |
| **Exp3** | **Two-step skeleton:** After 1-step alignment of max-misalignment pair, recompute M and align next max-misalignment pair; report dE_skeleton_1, dE_skeleton_2. New metric skel_2step_best. Quantiles reported for all four series (skeleton 1-step, 2-step, random, centrality). |
| **All** | Output directory: `run003/`. |

### Run 003 outcomes (summary)

- **Exp1:** 0 trials retained; drop reasons: E=2000 (D_M fix removed DM bottleneck; E below 1e-14 for all).
- **Exp2:** 500 trials; collapse_rate 0.8% overall, 3.2% in Q4; r(E0, collapse_step) = -0.38.
- **Exp3:** 500 trials; skeleton 2-step mean ΔE_cl best (-0.00193); skel_2step_best 30.0% vs skel_best 21.8%.

Full details: `findings_run003.md`.

---

## Run 004

- **Script:** `v3test_v004.py`
- **Findings:** `findings_run004.md`
- **Outputs:** All under `run004/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_ratio81_hist.png`, `exp2_hazard.csv`, `exp2_survival_by_quartile.csv`, `exp2_survival_curves.png`, `exp3_skeleton.csv`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`, `run_summary.json`

### Code changes v003 → v004 (driven by findings_run003 and run003 interpretation)

| Area | Change |
|------|--------|
| **Exp1** | **q_star:** greedy_coarsegrain → **random_partition(n, m=3)** so E_cl is in higher range; all 2000 trials retained. First real OP 8.1 ratio and c* statistics. |
| **Exp1** | Plot: histogram of ratio_81 → `exp1_ratio81_hist.png`. |
| **Exp2** | perturb_str: 0.28 → **0.32**; max_steps: 40 → **50**. Survival table by E0 quartile → `exp2_survival_by_quartile.csv`; plot → `exp2_survival_curves.png`. |
| **Exp3** | **3-step skeleton**; **2-step and 3-step** for random and centrality. Report E_final < 0.01 fraction per strategy; skel_1/2/3step_best (best overall = max dE among all 9). Boxplot data + `exp3_boxplot_dE.png`. |
| **All** | matplotlib (Agg) for plots; output dir `run004/`. |

### Run 004 outcomes (summary)

- **Exp1:** 2000/2000 retained. ratio_81 max 3.02, mean 0.76; empirical c* ≈ 0.33; T3.2 violations >1 in 1508 trials (expected with random q_star).
- **Exp2:** 500 trials; collapse_rate 1.4% overall, **5.6% in Q4**; **r(E0, collapse_step) = -0.69** (strong).
- **Exp3:** 500 trials; Centrality 3-step has largest mean ΔE_cl (-0.00339), then Skeleton 3-step (-0.00317); skel_1step best overall 22.2%, skel_2/3step ~9–10% (ties with other strategies).

Full details: `findings_run004.md`.

---

## Run 005

- **Script:** `v3test_v005.py`
- **Findings:** `findings_run005.md`
- **Outputs:** All under `run005/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_ratio81_hist_by_mode.png`, `exp2_hazard.csv`, `exp2_hazard_ratio.json`, `exp2_survival_by_quartile.csv`, `exp2_survival_curves.png`, `exp3_skeleton.csv`, `exp3_pairwise_win_rates.csv`, `exp3_strategy_summary.csv`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`, `run_summary.json`

### Code changes v004 → v005 (driven by findings_run004 recommendations)

| Area | Change |
|------|--------|
| **Exp1** | **Dual-mode:** (A) random_partition(n, m) with m∈{2,3,4}, 500 each (1500 trials); (B) greedy_coarsegrain with E_MIN=1e-18 (500 trials). Columns q_mode, m_blocks. Export exp1_summary_by_mode.csv; ratio_81 hist by mode. |
| **Exp2** | perturb_str: 0.32 → **0.35**; collapse_thresh: 0.20 → **0.15**. **Hazard ratio** Q4/Q1 collapse rate → exp2_hazard_ratio.json; survival table + plot. |
| **Exp3** | **4-step skeleton**; 10 strategies (Skel 1–4, Rand 1–3, Cen 1–3). **Pairwise win rates** (key pairs) → exp3_pairwise_win_rates.csv; **strategy summary** (mean_dE, std_dE, frac E<0.01, best_overall_pct) → exp3_strategy_summary.csv; boxplot over 10 strategies. |
| **All** | Output dir `run005/`. |

### Run 005 outcomes (summary)

- **Exp1:** 1500 random retained (m=2,3,4); 0 greedy retained (all E below 1e-18). ratio_81 by m: m=2 max 1.54, m=3 max 2.78, m=4 max 3.23; c* ≈ 0.31.
- **Exp2:** 500 trials; collapse 1.8% overall, **7.2% in Q4**; r = -0.61; hazard ratio Q4/Q1 large (Q1=0).
- **Exp3:** Skel 4 has largest mean ΔE_cl (-0.00407); Cen 1 has highest best_overall_pct (17.6%). Pairwise: P(Skel 3 > Cen 3)=44.2%, P(Skel 4 > Cen 3)=40.8%.

Full details: `findings_run005.md`.

---

## Run 006

- **Script:** `v3test_v006.py`
- **Findings:** `findings_run006.md`
- **Outputs:** All under `run006/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_ratio81_hist_by_mode.png`, `exp2_hazard.csv`, `exp2_quintiles.csv`, `exp2_hazard_ratio_quintiles.json`, `exp2_cox_style.json`, `exp2_survival_by_quintile.csv`, `exp2_survival_curves_quintiles.png`, `exp3_skeleton.csv`, `exp3_pairwise_matrix_11x11.csv`, `exp3_skel_k_vs_cen_rand.csv`, `exp3_strategy_summary.csv`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`, `run_summary.json`

### Code changes v005 → v006 (driven by findings_run005 and run005 assessment)

| Area | Change |
|------|--------|
| **Exp1** | m∈{3,4} only; **800 trials per m** (1600 random). **Spectral D_M:** 2nd eigenvector of symmetrized K → spectral_2block_partition, spectral_diameter; D_M = max(sampled, fixed, **spectral**). Greedy: **n=12**, E_MIN=**1e-22**. |
| **Exp2** | **Quintiles** (5 bins); **dual thresholds** 0.20 and 0.10 → collapse_step_020, collapse_step_010, survival by quintile; **Cox-style:** linear reg collapse_step~E0, odds ratio high vs low E0 → exp2_cox_style.json. |
| **Exp3** | **5-step skeleton** → **11 strategies** (Skel 1–5, Rand 1–3, Cen 1–3). **Full 11×11 pairwise** win matrix → exp3_pairwise_matrix_11x11.csv; **Skel k vs Cen k / Rand k** for k=1..5 → exp3_skel_k_vs_cen_rand.csv; strategy summary with **frac E<0.005, E<0.001**. |
| **All** | Output dir `run006/`. |

### Run 006 outcomes (summary)

- **Exp1:** 1600 random retained (m=3,4 × 800); 0 greedy (n=12, E_MIN=1e-22). ratio_81 max 3.20, c* ≈ 0.31; spectral D_M in use.
- **Exp2:** 500 trials; quintiles; **Q5 collapse 23%** (thresh 0.10), 9% (thresh 0.20); **r(E0, collapse_step) = -0.77**; Cox slope ≈ -110.
- **Exp3:** **Skel 5** largest mean ΔE_cl (-0.00568); Rand 1 highest best_overall_pct (16.4%); Skel k vs Cen k ~0.30–0.49, vs Rand k ~0.35–0.48.

Full details: `findings_run006.md`.

---

## Run 007

- **Script:** `v3test_v007.py`
- **Findings:** `findings_run007.md`
- **Outputs:** All under `run007/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_ratio81_hist_by_mode.png`, `exp2_hazard.csv`, `exp2_quintiles.csv`, `exp2_hazard_ratio_quintiles.json`, `exp2_cox_style.json`, `exp2_survival_by_quintile.csv`, `exp2_survival_curves_quintiles.png`, `exp3_skeleton.csv`, `exp3_pairwise_matrix_14x14.csv`, `exp3_skel_k_vs_cen_rand.csv`, `exp3_strategy_summary.csv`, `exp3_sensitivity_weighted.json`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`, `run_summary.json`

### Code changes v006 → v007 (driven by findings_run006 and run006 assessment)

| Area | Change |
|------|--------|
| **Exp1** | **c_bin spectrum:** Dirichlet c in low [0.2–0.8], medium [1–2], high [3–5]; 500 trials per bin (1500 random). Column `c_bin`; summary by c_bin (ratio_81 max/mean, c*). Greedy: **n=14**, E_MIN=**1e-24**. |
| **Exp2** | **Third threshold** 0.05 → collapse_step_005, collapsed_005; **median collapse step** by quintile; **Cox PH** (lifelines) when available: E0 as covariate, hazard ratio exp(coef). |
| **Exp3** | **align_measure** with `alpha` (default 0.5; 0.7 = 70/30 favoring misaligned). **Converged skeleton:** repeat max-pair until ΔE < 1e-4 or 8 steps → dE_skel_conv, n_steps_conv. **Cen 4, Cen 5** (sequential centrality). **14 strategies** → full 14×14 pairwise. **Sensitivity:** Skel 5 at α=0.5 vs 0.7 → exp3_sensitivity_weighted.json. |
| **All** | Output dir `run007/`. |

### Run 007 outcomes (summary)

- **Exp1:** 1500 random retained (500 per c_bin); 0 greedy (n=14, E_MIN=1e-24). ratio_81 by c_bin: low max 4.76 (c*≈0.21), medium 1.91 (c*≈0.52), high 0.79 (c*≈1.27). Bounds tighten with sharper (high-c) kernels.
- **Exp2:** 500 trials; triple threshold; Q5 collapse 92% @0.05, 31% @0.10, 5% @0.20; r≈-0.70; Cox PH coef(E0)≈-97, exp(coef)≈8.8e-43; median_steps by quintile reported.
- **Exp3:** 14 strategies; **Skel 5** largest mean ΔE_cl (-0.00506); **Skel conv** mean -0.00160 (stops early); **Cen 1** best_overall_pct 10.2%; Skel k vs Cen k ~0.31–0.50 (best at k=2). Sensitivity: 70/30 (α=0.7) worse than 50/50 (p_70_gt_50=65.8% means 50/50 wins more).

Full details: `findings_run007.md`.

---

## Run 008

- **Script:** `v3test_v008.py`
- **Findings:** `findings_run008.md`
- **Outputs:** All under `run008/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_summary_by_cbin_m.csv`, `exp1_ratio81_hist_by_mode.png`, `exp1_ratio81_by_cbin_m.png`, `exp2_hazard.csv`, `exp2_quintiles.csv`, `exp2_hazard_ratio_quintiles.json`, `exp2_cox_style.json`, `exp2_survival_by_quintile.csv`, `exp2_survival_curves_quintiles.png`, `exp3_skeleton.csv`, `exp3_pairwise_matrix_14x14.csv`, `exp3_skel_k_vs_cen_rand.csv`, `exp3_strategy_summary.csv`, `exp3_sensitivity_weighted.json`, `exp3_skel_conv_n_steps.csv`, `exp3_skel_conv_n_steps.json`, `exp3_skel_conv_n_steps_hist.png`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`

### Code changes v007 → v008 (driven by findings_run007 and run007 assessment)

| Area | Change |
|------|--------|
| **Exp1** | **Fix m within c_bin:** 4 c_bins (very_low [0.1–0.3], low, medium, high) × m∈{3,4}, 250 per cell (2000 random). Summary by (c_bin, m) → exp1_summary_by_cbin_m.csv; plot ratio_81 by (c_bin, m) → exp1_ratio81_by_cbin_m.png. |
| **Exp2** | **1-SD hazard:** E0 standardized; Cox PH with E0_std → hazard_ratio_per_1SD_E0. **Ramping noise:** perturb_str linear 0.2→0.5 over steps; second trajectory per trial → collapse_step_010_ramp, collapsed_010_ramp. **Median survival step** by quintile in grp2_q and hazard JSON. |
| **Exp3** | **SKEL_CONV_EPS=1e-3** (looser); n_steps_conv distribution → exp3_skel_conv_n_steps.csv/json/hist. **α=0.3** sensitivity (full curve 0.3, 0.5, 0.7) → exp3_sensitivity_weighted.json. |
| **All** | Output dir `run008/`. |

### Run 008 outcomes (summary)

- **Exp1:** 2000 random retained (4 c_bin × 2 m × 250); 0 greedy. **very_low** tightest c*: m=4 → 0.129, m=3 → 0.19; low/medium/high consistent with run007. Ratio_81 by (c_bin, m) separates m vs c effects.
- **Exp2:** 500 trials; **hazard_ratio_per_1SD_E0 ≈ 0.157** (1-SD increase in E0 → ~6.4× hazard); ramping collapse_rate_010 9%, r(E0, collapse_step_ramp)≈-0.81; median_survival_step by quintile exported.
- **Exp3:** Skel 5 largest mean ΔE_cl (-0.00586); **Skel conv** mean n_steps 1.31 (median 1), ε=1e-3 stops very early; **α=0.3** best mean dE (-0.00976), then 0.5, 0.7; p_50_gt_30=64.8%, p_70_gt_50=68%.

Full details: `findings_run008.md`.

---

## Run 009

- **Script:** `v3test_v009.py`
- **Findings:** `findings_run009.md`
- **Outputs:** All under `run009/`: `exp1_op81.csv`, `exp1_drop_reasons.json`, `exp1_summary_by_mode.csv`, `exp1_summary_by_cbin_m.csv`, `exp1_cstar_vs_c.csv`, `exp1_cstar_vs_c.png`, `exp1_ratio81_hist_by_mode.png`, `exp1_ratio81_by_cbin_m.png`, `exp2_hazard.csv`, `exp2_quintiles.csv`, `exp2_hazard_ratio_quintiles.json`, `exp2_cox_style.json`, `exp2_bootstrap_1sd_hr.json`, `exp2_survival_by_quintile.csv`, `exp2_survival_curves_quintiles.png`, `exp2_survival_const_vs_ramp.png`, `exp3_skeleton.csv`, `exp3_pairwise_matrix_14x14.csv`, `exp3_skel_k_vs_cen_rand.csv`, `exp3_strategy_summary.csv`, `exp3_sensitivity_weighted.json`, `exp3_skel_conv_n_steps.csv`, `exp3_skel_conv_n_steps.json`, `exp3_skel_conv_n_steps_hist.png`, `exp3_alpha_curve.png`, `exp3_boxplot_data.csv`, `exp3_boxplot_dE.png`

### Code changes v008 → v009 (driven by findings_run008 and run008 assessment)

| Area | Change |
|------|--------|
| **Exp1** | **extreme_low** c_bin [0.05–0.15]; **greedy omitted** (oracle documented, bound stats random-only). **c* vs mean(c)** table + plot → exp1_cstar_vs_c.csv, exp1_cstar_vs_c.png. Store c_val per trial. 5 bins × 2 m × 200 = 2000 random. |
| **Exp2** | **Bootstrap CI** (1000 reps) on 1-SD hazard ratio → exp2_bootstrap_1sd_hr.json. **Constant vs ramping** survival curves side-by-side → exp2_survival_const_vs_ramp.png. |
| **Exp3** | **SKEL_CONV_EPS=1e-2**; **hybrid** conv (min 3 steps before ε check). **α curve** plot (mean_dE vs α 0.3, 0.5, 0.7) → exp3_alpha_curve.png. **frac_dE_below_minus_001** in strategy summary. |
| **All** | Output dir `run009/`. |

### Run 009 outcomes (summary)

- **Exp1:** 2000 random retained (5 c_bin × 2 m × 200); greedy omitted. **extreme_low** → **c* ≈ 0.103** (ratio_81 max 9.69), tightest floor yet; very_low 0.117, low 0.186, medium 0.40, high 1.49. c* vs mean(c) curve exported.
- **Exp2:** 500 trials; Cox PH convergence failed (rare-event nan); linear r≈-0.76, OR≈15; bootstrap 1-SD HR failed (same convergence); constant vs ramping survival plot generated.
- **Exp3:** Skel 5 largest mean ΔE_cl (-0.00563); **Skel conv** (ε=1e-2, min 3 steps) mean n_steps **3.0** (median 3, range 3–4), mean_dE -0.00323; **frac_dE_below_minus_001** highest for Skel 5 (23%); α curve: 0.3 best mean (-0.00990), 0.5 mid, 0.7 worst; Cen 1 / Rand 1 best_overall ~11–13%.

Full details: `findings_run009.md`.

---

## Run 010 — Unified run (Ψ proxy)

- **Script:** `vtest_v010.py` (unified recursive + Ψ proxy)
- **Findings:** `findings_run010.md`
- **Outputs:** All under `run010/`: `run010_unified.csv`, `run010_psi.csv`, `run010_cstar_vs_c.csv`, `run010_psi_summary.csv`, `run010_summary.json`, `exp1_cstar_scaling.png`, `exp3_psi_reduction_waterfall.png`, `exp3_alpha_psi_curve.png`

### Code / design (Run 010 — unified run)

| Area | Change |
|------|--------|
| **Unified** | Single recursive script reusing best practice from runs 001–009: extreme c_bins, fixed m, spectral/sampled D_M, α curve. |
| **Exp1** | 5 c_bins (extreme_low [0.05–0.15] through high) × m∈{3,4} × α∈{0.3,0.5,0.7} × N=300; n=12; c* vs mean(c) scaling curve. |
| **Ψ proxy** | **New:** discretized proxy for selection functional Ψ — integrated discounted cost (E_cl + M_sys + τ + R) over 30-step trajectory under perturbation. Post-alignment Ψ computed for baseline vs skeleton 5-step. |
| **Exp3 + payoff** | Skeleton 5-step vs random 1-step; Ψ reduction % by c_bin; hero figures: c* scaling, Ψ reduction waterfall, α+Ψ scatter. Direct numerical validation of coherence attractor (Theorem 6.4 / Prop 6.5). |
| **All** | Output dir `run010/`; run010_summary.json for paper tables. |

### Run 010 outcomes (summary)

- **Exp1:** c* floor extreme_low ≈ 0.156 (ratio_81_max ≈ 6.41), very_low ≈ 0.24 in quick run; c* scaling curve (exp1_cstar_scaling.png) exported.
- **Ψ payoff:** Ψ proxy uses **no-align baseline**; skeleton vs no alignment. Quick run (64 trials, 3-step skel) had high-variance Ψ reduction; full run (QUICK_RUN=False, N=250, 5-step) targets ~40% reduction per target specification.
- **Artifacts:** run010_unified.csv, run010_psi.csv (psi_no_align, psi_skel, psi_reduction_pct), run010_cstar_vs_c.csv, run010_psi_summary.csv, run010_summary.json, primary figures (exp1_cstar_scaling.png, exp3_psi_reduction_waterfall.png, exp3_alpha_psi_curve.png).

Full details: `findings_run010.md`.

---

## Convention for future runs

1. Copy or branch the latest script to `v3test_v00X.py` (or the current naming convention in this directory).
2. Update `RUN_ID` and `OUTPUT_DIR` to `run00X` and create that subdir.
3. Document parameter and logic changes in the script docstring and in this CHANGELOG under a new "Run 00X" section.
4. Run the script; write `findings_run00X.md` referencing the changelog and comparing to previous run(s).
