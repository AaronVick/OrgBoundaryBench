# External Agreement Diagnostic

- Dataset: `/Users/aaronvick/Downloads/aboutmoxie/Reflective_Samples_Org/data/processed/email_eu_core/kernel.npz` (n=120)
- q_star NMI: `0.313592`
- spectral NMI: `0.313592`
- louvain NMI: `0.724738`
- random matched mean NMI: `0.082681`

Interpretation:
- q_star is above random matched partitions but materially below Louvain for department-label alignment.
- This indicates q_star is extracting structure, but not the same structure as formal department labels.
- Is q_star learning a different interpretable structure than departments? `True`
