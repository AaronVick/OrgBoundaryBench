# External Agreement Report

- Dataset: `/Users/aaronvick/Downloads/aboutmoxie/Reflective_Samples_Org/data/processed/email_eu_core/kernel.npz`
- n: `40`

| Candidate | NMI | ARI | macro-F1 |
|---|---:|---:|---:|
| singleton | 0.8778 | 0.0000 | 0.0167 |
| louvain | 0.7614 | 0.3524 | 0.0487 |
| spectral | 0.2937 | 0.0437 | 0.0045 |
| degree_median | 0.0461 | -0.0014 | 0.0000 |
| q_star | 0.0000 | 0.0000 | 0.0000 |
| one_block | 0.0000 | 0.0000 | 0.0000 |
| random_0 | 0.0000 | 0.0000 | 0.0000 |

## Chance-comparison (q_star vs permuted labels)
- NMI p-value: `1.0000`
- ARI p-value: `1.0000`
- macro-F1 p-value: `1.0000`

Pass criterion status: `False`
Fail condition: no better than baseline or null-equivalent.
