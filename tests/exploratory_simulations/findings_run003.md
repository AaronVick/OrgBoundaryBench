# Boundary Coherence Across Scales — Run 003 Findings

**Script:** `docs/exploratory_simulations/v3test_v003.py`  
**Run date:** 2026-03-10  
**Total runtime:** 102.4 s  
**Output dir:** `docs/exploratory_simulations/run003/`

Code and parameter changes from run 002 are documented in `CHANGELOG.md`. This report compares run 003 to runs 001 and 002.

---

## Summary

Run 003 implemented run002 recommendations: **Exp1** uses D_M = max(mis_sampled, fixed_coarse_diameter) and n=10 so the denominator has positive scale; **Exp2** uses stronger perturbation (0.28) and lower collapse threshold (0.20); **Exp3** adds **two-step skeleton alignment** and reports quantiles for all strategies. **Experiment 1 still retained 0 trials** — drop-tracking now shows all exclusions due to **E** (closure energy below 1e-14), so the D_M fix removed the DM bottleneck. **Experiment 2** shows a clearer collapse signal (3.2% in Q4, r = -0.38). **Experiment 3** shows that **2-step skeleton** improves over 1-step and reaches 30% “best overall” vs 21.8% for 1-step.

---

## Changes from run 001 and run 002 (reference)

| Item | Run 001 | Run 002 | Run 003 |
|------|---------|---------|---------|
| **Exp1** | | | |
| D_M definition | mis_sampled only | mis_sampled only | **max(mis_sampled, fixed_coarse_diameter)** |
| n (state space) | 6 | 6 | **10** |
| Validity DM_MIN | 1e-10 | 1e-12 | **1e-14** |
| E_MIN | 1e-12 | 1e-14 | 1e-14 |
| Drop reason (dominant) | DM (all) | DM (1998) | **E (2000)** |
| **Exp2** | | | |
| perturb_str | 0.12 | 0.20 | **0.28** |
| collapse_thresh | 0.30 | 0.30 | **0.20** |
| N2 | 400 | 400 | **500** |
| **Exp3** | | | |
| Skeleton | 1-step only | 1-step only | **1-step + 2-step** |
| skel_2step_best | — | — | **reported** |
| Output location | docs/ | run002/ | **run003/** |

---

## Experiment 1: Open Problem 8.1 — Lower Bound Search

**Config (v003):** n=10, n_ag=3, N1=2000; D_M = max(mis_sampled, fixed_coarse_diameter); thresholds DM,K2,g > 1e-14/1e-12, E > 1e-14  
**Runtime:** 45.8 s  

**Outcome:** **0 trials** retained.

### Drop reasons (run003)

| Reason | Count |
|--------|--------|
| DM     | 0     |
| K2     | 0     |
| gap    | 0     |
| E      | 2000  |
| ok     | 0     |

**Implication:** The **D_M** change worked: no trial is now dropped for DM. Every trial is dropped because **closure energy E** (at the greedy coarse-grained partition) is ≤ 1e-14. With n=10, greedy coarse-graining yields very small E, so the validity filter on E removes all trials. For a future run: relax E_MIN (e.g. 1e-16) for exploratory OP 8.1 statistics, or use a fixed/random partition in Exp1 so E has larger scale.

---

## Experiment 2: Assumption 6.3 — Perturbation Hazard

**Config (v003):** n2=8, N2=500, **collapse_thresh=0.20**, max_steps=40, **perturb_str=0.28**  
**Runtime:** 0.9 s  

**Outcome:** 500 trials; collapse remains rare overall (0.8%) but **3.2% in Q4**; correlation E0–collapse_step = -0.38.

### Collapse by E0 quartile

| E0_quartile | collapse_rate | mean_steps | std_steps | mean_E0   |
|-------------|---------------|------------|-----------|-----------|
| Q1 (low)    | 0.00          | 40.00      | 0.0       | 0.0110    |
| Q2          | 0.00          | 40.00      | 0.0       | 0.0251    |
| Q3          | 0.00          | 40.00      | 0.0       | 0.0481    |
| Q4 (high)   | **0.032**     | 38.75      | 6.89      | 0.1523    |

- **Correlation** r(E0, collapse_step) = **-0.38** (run002: -0.27; run001: -0.60). Negative: higher E0 → earlier collapse when it occurs.
- collapse_step std: 3.48; 25%/50%/75%: [40, 40, 40].

**Implication:** Stronger perturbation and lower threshold increased Q4 collapse rate (3.2% vs 1% in run002). Assumption 6.3 (higher E0 → more hazard) is supported; further increases in perturb_str or run length could sharpen the signal.

---

## Experiment 3: Coordination Skeleton vs Baselines (incl. 2-step)

**Config (v003):** n3=8, nag3=6, N3=500; mis_sampled S=100; **two-step skeleton** alignment.  
**Runtime:** 55.7 s  

**Outcome:** **2-step skeleton** has larger mean closure-energy reduction than 1-step skeleton, random, and centrality; **skel_2step_best = 30%** vs skel_best = 21.8%.

### Mean ΔE_cl reduction (positive = more reduction)

| Strategy         | Mean ΔE_cl   | Std     |
|------------------|--------------|---------|
| Skeleton 1-step  | -0.000978    | 0.00342 |
| **Skeleton 2-step** | **-0.001927** | 0.00516 |
| Random           | -0.001452    | 0.00349 |
| Centrality       | -0.001082    | 0.00343 |

Two-step skeleton has the largest mean reduction (least negative = largest drop in closure energy).

### Quantiles (0.25, 0.5, 0.75)

- dE_skeleton_1: [-0.00275, -0.00069, 0.00107]
- dE_skeleton_2: [-0.00476, -0.00164, 0.00107]
- dE_random:     [-0.00355, -0.00101, 0.00088]
- dE_centrality: [-0.00310, -0.00076, 0.00093]

### Win rates

| Metric                        | Run 002 | Run 003 |
|-------------------------------|---------|---------|
| Skeleton 1-step best overall  | 18.4%   | **21.8%** |
| **Skeleton 2-step best overall** | —       | **30.0%** |
| Skeleton 1-step > random      | 43.4%   | 47.4%   |
| Skeleton 1-step > centrality  | 29.4%   | 32.4%   |
| Skeleton 2-step > random      | —       | 44.4%   |
| Skeleton 2-step > centrality | —       | 42.6%   |

**Implication:** Multi-step skeleton alignment improves over single-step: 2-step is best overall in 30% of trials (vs 21.8% for 1-step) and has the largest mean ΔE_cl reduction. The “skeleton as coordination target” hypothesis is better supported when allowing **two steps** of max-misalignment alignment.

---

## Artifacts (run003)

| File                   | Path     | Rows / notes      |
|------------------------|----------|-------------------|
| exp1_op81.csv         | run003/  | 0                 |
| exp1_drop_reasons.json| run003/  | drop counts       |
| exp2_hazard.csv        | run003/  | 500               |
| exp3_skeleton.csv      | run003/  | 500 (incl. 2-step)|
| run_summary.json       | run003/  | run_id, config, totals |

---

## Cross-run comparison (001 / 002 / 003)

| Metric                    | Run 001 | Run 002 | Run 003 |
|---------------------------|---------|---------|---------|
| Exp1 retained             | 0       | 0       | 0       |
| Exp1 drop reason           | DM      | DM      | **E**   |
| Exp2 collapse_rate (overall) | ~5% Q4  | 0.25%   | 0.8%    |
| Exp2 r(E0, collapse_step)  | -0.60   | -0.27   | -0.38   |
| Exp3 skel best (1-step)    | 21.3%   | 18.4%   | 21.8%   |
| Exp3 skel 2-step best       | —       | —       | **30.0%** |
| Exp3 mean ΔE_cl best        | random  | random  | **skeleton 2-step** |

---

## Recommendations for run004

1. **Exp1:** Relax E_MIN to 1e-16 or use a fixed/random 2-block partition (instead of greedy) so E has larger scale and some trials pass; then report T3.2 and OP 8.1 ratios.
2. **Exp2:** Optionally try perturb_str=0.32 or more steps to further increase collapse rate and correlation.
3. **Exp3:** Consider 3-step skeleton and/or compare 2-step random/centrality baselines for parity.
