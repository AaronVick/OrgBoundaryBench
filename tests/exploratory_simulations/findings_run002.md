# Boundary Coherence Across Scales — Run 002 Findings

**Script:** `docs/exploratory_simulations/v3test_v002.py`  
**Run date:** 2026-03-10  
**Total runtime:** 102.5 s  
**Output dir:** `docs/exploratory_simulations/run002/`

Code and parameter changes from run 001 are documented in `CHANGELOG.md`.

---

## Summary

Run 002 applied the run001 recommendations: relaxed Exp1 validity thresholds, increased sampling (S, N1), stronger Exp2 perturbation and more steps, and larger Exp3 scale with variance/quantile reporting. **Experiment 1 still retained 0 trials** — drop-tracking shows almost all exclusions are due to `D_M` falling below the new threshold. Experiments 2 and 3 completed with expanded reporting; Exp2 collapse rate remained low; Exp3 skeleton again did not dominate baselines.

---

## Changes from Run 001 (reference)

| Item | Run 001 | Run 002 |
|------|---------|---------|
| Exp1 validity | DM,K2,g > 1e-10, E > 1e-12 | DM,K2,g > 1e-12, E > 1e-14 |
| Exp1 mis_sampled S | 80 | 200 |
| Exp1 N1 | 800 | 2000 |
| Exp1 drop tracking | none | per-reason counts → `exp1_drop_reasons.json` |
| Exp2 perturb_str | 0.12 | 0.20 |
| Exp2 max_steps | 30 | 40 |
| Exp2 reporting | quartile table only | + std_steps, collapse_step std & quantiles |
| Exp3 n3 / nag3 / N3 | 6, 4, 300 | 8, 6, 500 |
| Exp3 mis_sampled S (M) | 60 | 100 |
| Exp3 reporting | means only | + std and quantiles for ΔE_cl |
| Output location | `docs/` (flat) | `run002/` (versioned) |

---

## Experiment 1: Open Problem 8.1 — Lower Bound Search

**Config (v002):** n=6, n_ag=3, N1=2000; mis_sampled S=200; thresholds DM,K2,g > 1e-12, E > 1e-14  
**Runtime:** 64.4 s  

**Outcome:** **0 trials** retained.

### Drop reasons (run002)

| Reason | Count |
|--------|--------|
| DM     | 1998  |
| K2     | 0     |
| gap    | 0     |
| E      | 2     |
| ok     | 0     |

**Implication:** Relaxing thresholds did not yield any valid trials; **D_M** from `mis_sampled` is almost always below 1e-12. The infimum over partition pairs is likely very small for these n=6, m=2 settings. For a future run (e.g. run003): (1) consider a different **D_M** definition (e.g. fixed partition distance or higher m), (2) or relax DM_MIN further (e.g. 1e-14) for exploratory OP 8.1 statistics, (3) or increase n so partition distances have larger scale.

---

## Experiment 2: Assumption 6.3 — Perturbation Hazard

**Config (v002):** n2=8, N2=400, collapse_thresh=0.30, **max_steps=40**, **perturb_str=0.20**  
**Runtime:** 0.6 s  

**Outcome:** 400 trials; collapse remained rare (0.25% overall); correlation E0–collapse_step weaker than run001.

### Collapse by E0 quartile

| E0_quartile | collapse_rate | mean_steps | std_steps | mean_E0   |
|-------------|---------------|------------|-----------|-----------|
| Q1 (low)    | 0.00          | 40.00      | 0.0       | 0.0147    |
| Q2          | 0.00          | 40.00      | 0.0       | 0.0272    |
| Q3          | 0.00          | 40.00      | 0.0       | 0.0494    |
| Q4 (high)   | 0.01          | 39.61      | 3.9       | 0.1435    |

- **Correlation** r(E0, collapse_step) = **-0.27** (run001: -0.60). Still negative: higher E0 → earlier collapse when it occurs, but weaker.
- **collapse_step** std: 1.95; 25%/50%/75%: [40, 40, 40] — most runs never collapse.

**Implication:** Stronger perturbation (0.20) and more steps (40) did not increase collapse rate meaningfully; only 1% in Q4. Assumption 6.3 direction (higher E0 → more hazard) still holds. To sharpen the signal, consider even larger perturb_str, lower collapse_thresh, or more steps.

---

## Experiment 3: Coordination Skeleton vs Baselines

**Config (v002):** n3=8, nag3=6, N3=500; mis_sampled S=100 for M  
**Runtime:** 37.4 s  

**Outcome:** Skeleton again did not dominate; mean closure-energy reduction was similar across strategies; skeleton win rates lower than run001.

### Mean ΔE_cl reduction (positive = more reduction)

| Strategy   | Mean ΔE_cl   | Std     |
|-----------|--------------|---------|
| Skeleton  | -0.001174    | 0.00335 |
| Random    | -0.001249    | 0.00355 |
| Centrality| -0.000696    | 0.00333 |

Random had the largest mean reduction; skeleton and centrality were slightly less effective.  
**Quantiles (0.25, 0.5, 0.75) dE_skeleton:** [-0.00301, -0.00096, 0.00076].

### Win rates

- Skeleton > Random: **43.4%** (run001: 55.0%)
- Skeleton > Centrality: **29.4%** (run001: 29.0%)
- Skeleton best overall: **18.4%** (run001: 21.3%)

**Implication:** With larger n3/nag3 and more trials, skeleton is **worse** than random on average and rarely best overall. Centrality has the smallest mean reduction (least effective) but skeleton still loses to it in most head-to-head comparisons. The “skeleton as best one-step target” hypothesis is not supported in run002.

---

## Artifacts (run002)

| File                   | Path                    | Rows / notes      |
|------------------------|-------------------------|--------------------|
| exp1_op81.csv         | `run002/`               | 0                  |
| exp1_drop_reasons.json | `run002/`               | drop counts        |
| exp2_hazard.csv       | `run002/`               | 400                |
| exp3_skeleton.csv     | `run002/`               | 500                |
| run_summary.json      | `run002/`               | run_id, config, totals |

---

## Recommendations for run003

1. **Exp1:** Address D_M: use a different definition (e.g. distance for a fixed coarse partition), or set DM_MIN to 1e-14 / 1e-16 for exploratory bounds, or increase n (e.g. n=10) so partition distances are larger.
2. **Exp2:** Try perturb_str=0.25–0.30 and/or collapse_thresh=0.20 to increase collapse rate and clarify E0–hazard relationship.
3. **Exp3:** Consider multi-step alignment or alternative skeleton definitions; continue reporting variance/quantiles for comparison across runs.
