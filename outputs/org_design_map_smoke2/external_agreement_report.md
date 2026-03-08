# External Agreement Report

- Dataset: `/Users/aaronvick/Downloads/aboutmoxie/Reflective_Samples_Org/data/processed/email_eu_core/kernel.npz`
- n: `80`

| Candidate | NMI | ARI | macro-F1 |
|---|---:|---:|---:|
| singleton | 0.8177 | 0.0000 | 0.0075 |
| louvain | 0.7011 | 0.3556 | 0.0000 |
| q_star | 0.2708 | 0.0588 | 0.0035 |
| spectral | 0.2708 | 0.0588 | 0.0035 |
| label_frequency | 0.2080 | 0.0239 | 0.0041 |
| random_7 | 0.1508 | 0.0088 | 0.0071 |
| random_6 | 0.1453 | 0.0136 | 0.0052 |
| rewire_spectral_3 | 0.1365 | 0.0076 | 0.0071 |
| rewire_spectral_1 | 0.1222 | 0.0037 | 0.0036 |
| random_3 | 0.1222 | 0.0085 | 0.0072 |
| rewire_spectral_0 | 0.1074 | -0.0052 | 0.0053 |
| random_0 | 0.1057 | -0.0053 | 0.0053 |
| random_1 | 0.1018 | -0.0036 | 0.0052 |
| rewire_spectral_2 | 0.1009 | -0.0014 | 0.0089 |
| random_4 | 0.0916 | -0.0078 | 0.0035 |
| random_2 | 0.0806 | -0.0104 | 0.0053 |
| random_5 | 0.0657 | -0.0093 | 0.0088 |
| degree_median | 0.0434 | 0.0015 | 0.0028 |
| one_block | 0.0000 | 0.0000 | 0.0028 |

## Chance-comparison (q_star vs permuted labels)
- NMI p-value: `0.0000`
- ARI p-value: `0.0000`
- macro-F1 p-value: `0.9600`

Pass criterion status: `False`
Fail condition: no better than baseline or null-equivalent.
