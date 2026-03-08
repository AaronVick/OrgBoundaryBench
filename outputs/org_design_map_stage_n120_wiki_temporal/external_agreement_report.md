# External Agreement Report

- Dataset: `/Users/aaronvick/Downloads/aboutmoxie/Reflective_Samples_Org/data/processed/email_eu_core/kernel.npz`
- n: `120`

| Candidate | NMI | ARI | macro-F1 |
|---|---:|---:|---:|
| singleton | 0.7822 | 0.0000 | 0.0012 |
| louvain | 0.7247 | 0.4522 | 0.0000 |
| q_star | 0.3136 | 0.0830 | 0.0058 |
| spectral | 0.3136 | 0.0830 | 0.0058 |
| label_frequency | 0.2007 | 0.0247 | 0.0052 |
| random_9 | 0.1176 | 0.0142 | 0.0048 |
| random_14 | 0.1122 | 0.0176 | 0.0071 |
| rewire_spectral_6 | 0.1103 | 0.0022 | 0.0071 |
| rewire_spectral_7 | 0.1102 | 0.0051 | 0.0049 |
| random_11 | 0.0928 | 0.0020 | 0.0087 |
| random_12 | 0.0916 | 0.0001 | 0.0091 |
| random_1 | 0.0897 | 0.0056 | 0.0060 |
| random_13 | 0.0889 | 0.0017 | 0.0060 |
| random_5 | 0.0888 | 0.0016 | 0.0058 |
| random_4 | 0.0885 | -0.0022 | 0.0083 |
| random_3 | 0.0863 | -0.0001 | 0.0080 |
| rewire_spectral_4 | 0.0799 | -0.0023 | 0.0069 |
| rewire_spectral_1 | 0.0795 | 0.0039 | 0.0080 |
| rewire_spectral_2 | 0.0786 | 0.0011 | 0.0051 |
| rewire_spectral_5 | 0.0780 | -0.0006 | 0.0060 |
| rewire_spectral_3 | 0.0780 | -0.0040 | 0.0060 |
| random_10 | 0.0777 | -0.0000 | 0.0069 |
| rewire_spectral_0 | 0.0729 | -0.0068 | 0.0059 |
| random_2 | 0.0718 | -0.0011 | 0.0055 |
| random_8 | 0.0696 | -0.0027 | 0.0032 |
| random_7 | 0.0629 | -0.0029 | 0.0070 |
| random_6 | 0.0621 | -0.0038 | 0.0060 |
| random_15 | 0.0614 | -0.0063 | 0.0050 |
| random_0 | 0.0610 | -0.0014 | 0.0051 |
| degree_median | 0.0547 | 0.0013 | 0.0023 |
| one_block | 0.0000 | 0.0000 | 0.0022 |

## Chance-comparison (q_star vs permuted labels)
- NMI p-value: `0.0000`
- ARI p-value: `0.0000`
- macro-F1 p-value: `0.7167`

Pass criterion status: `False`
Fail condition: no better than baseline or null-equivalent.
