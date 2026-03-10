# Run report: PRD-31 full null/rival/leverage audit

**Run:** 2026-03-08T233337Z  
**Framework:** BPO (thoughts3-II null/rival, thoughts3-III leverage).

---

## 1. Hypothesis

BPO partition q* (greedy coarse-graining) beats baselines and nulls including **degree-preserving rewired** graphs (D > 0 with bootstrap CI). Results are not driven by leverage points (S_max < threshold).

## 2. Method

Null/rival: Perf = NMI to labels when provided else -J(q). Baselines: one-block, singleton, Louvain. Nulls: random partition (matched k), label-permuted NMI, **row-sum-preserving rewire** (n_rewire in each bootstrap draw). Bootstrap CI for D; rewire-null gate: CI_lower > 0. Leverage: node/edge drop; S_max; pass if S_max < threshold.

## 3. Data provenance

email-Eu-core (or equivalent): /Users/aaronvick/Downloads/aboutmoxie/Reflective_Samples_Org/data/processed/email_eu_core/kernel.npz, n=50, n_original=400. Labels: present.

## 4. Results

| Gate | Result |
|------|--------|
| Rewire-null (bootstrap CI) | mean_D=-0.0062, CI=[-0.0082, -0.0047], Pass=False |
| Leverage | S_max=nan, threshold=1.0, Pass=False |

## 5. Falsification

**PRD-31:** If rewire-null gate fails (CI includes 0 or D ≤ 0), density-confounding threat remains; no organizational relevance claim. If leverage gate fails, results sensitive to few nodes/edges.

---

*Traceability: PRD-31, thoughts3-II, thoughts3-III, outputs/METHODOLOGY.md.*