# Organizational Mapping Failure Interpretation

- Is map closer to communication closure than formal departments? `True`
  Evidence: q_star has lower closure objective than Louvain but lower department alignment (NMI).
- Is governance preservation orthogonal to org-chart recovery? `True`
  Evidence: governance-preservation test passes while external-agreement test fails.
- Does negative D mean the objective is losing to standard clustering on this benchmark? `True`
  Evidence: mean_D=-0.487963, CI lower=-0.531056.
- Is stress failure global or narrow leverage? `narrow leverage`
  Evidence: stress pass=True, leverage pass=False, leverage ratio=2.000836 vs 2.000000.

Interpretation summary:
- Current map appears to capture closure/coordination structure that is not equivalent to formal department labels.
- Governance signal and department alignment are currently decoupled in this run.
- Rival dominance failure is real on the external-label metric and cannot be rescued by wording.
