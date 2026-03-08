# External Agreement Report

- Dataset: `/Users/aaronvick/Downloads/aboutmoxie/Reflective_Samples_Org/data/processed/email_eu_core/kernel.npz`
- n: `80`

| Candidate | NMI | ARI | macro-F1 |
|---|---:|---:|---:|
| singleton | 0.8177 | 0.0000 | 0.0075 |
| louvain | 0.7011 | 0.3556 | 0.0000 |
| q_star | 0.3589 | 0.0820 | 0.0069 |
| spectral | 0.2708 | 0.0588 | 0.0035 |
| random_5 | 0.2086 | 0.0054 | 0.0084 |
| label_frequency | 0.2080 | 0.0239 | 0.0041 |
| random_6 | 0.1906 | 0.0089 | 0.0094 |
| random_1 | 0.1854 | -0.0005 | 0.0105 |
| random_7 | 0.1832 | -0.0041 | 0.0094 |
| random_2 | 0.1771 | -0.0099 | 0.0054 |
| random_4 | 0.1728 | -0.0045 | 0.0049 |
| random_0 | 0.1631 | -0.0072 | 0.0080 |
| random_3 | 0.1386 | -0.0107 | 0.0103 |
| rewire_spectral_3 | 0.1365 | 0.0076 | 0.0071 |
| rewire_spectral_1 | 0.1222 | 0.0037 | 0.0036 |
| rewire_spectral_0 | 0.1074 | -0.0052 | 0.0053 |
| rewire_spectral_2 | 0.1009 | -0.0014 | 0.0089 |
| degree_median | 0.0434 | 0.0015 | 0.0028 |
| one_block | 0.0000 | 0.0000 | 0.0028 |

## Chance-comparison (q_star vs permuted labels)
- NMI p-value: `0.0000`
- ARI p-value: `0.0000`
- macro-F1 p-value: `0.4000`

Pass criterion status: `False`
Fail condition: no better than baseline or null-equivalent.
