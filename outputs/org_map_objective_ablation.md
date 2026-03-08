# Objective Ablation Study

- Candidate partitions evaluated: `15`
- Objectives tested: closure only, closure+robust closure, closure+governance, closure+factorization, full objective.

Summary findings:
- `closure_only` selected `one_block` (k=1), NMI=0.000000, stress_pass=True, rival_dominance_pass=False, governance_pass=False.
- `closure_plus_robust` selected `one_block` (k=1), NMI=0.000000, stress_pass=True, rival_dominance_pass=False, governance_pass=False.
- `closure_plus_governance` selected `singleton` (k=120), NMI=0.782217, stress_pass=True, rival_dominance_pass=True, governance_pass=False.
- `closure_plus_factorization` selected `one_block` (k=1), NMI=0.000000, stress_pass=True, rival_dominance_pass=False, governance_pass=False.
- `full_objective` selected `singleton` (k=120), NMI=0.782217, stress_pass=True, rival_dominance_pass=True, governance_pass=False.

Interpretation:
- Objective ablations collapse to trivial extremes (`one_block` or `singleton`) rather than a balanced organizational map.
- No ablation simultaneously achieves nontriviality, governance preservation, and strong external/rival performance.
