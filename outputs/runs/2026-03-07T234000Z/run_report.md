# Run report: 2026-03-07T234000Z

**Domains:** 6.1 (Synthetic) + 6.4 (Public data — Enron SNAP)  
**Framework:** Boundary-Preserving Organization (Vick 2025). PRD-04, PRD-05, PRD-06, PRD-08.

---

## 1. Methodology

- **Scientific method:** Claims (Table 1) with operational falsification conditions; tests per PRD-04 (6.1), PRD-05 (6.4 Test D); fixed seeds for synthetic; baseline comparison (E6.1 vs Q [5]; 6.4 vs Louvain [6]). See `outputs/METHODOLOGY.md`.
- **Procedure:** (1) Full test suite (pytest, 19 tests). (2) Domain 6.1 verification report. (3) Domain 6.4 verification on public kernel (q*, Louvain). (4) Run report with methodology, data provenance, findings.
- **Data:** **Synthetic (6.1):** In-repo generators (PRD-04). **Public (6.4):** Enron email network (SNAP); see §3.

---

## 2. Environment

| Item | Value |
|------|--------|
| Python | 3.12.8 |
| Platform | macOS (darwin) |
| Install | `pip install -e ".[test]"`; optional `.[data]` (networkx) for Louvain |

---

## 3. Public data provenance (Domain 6.4)

| Field | Value |
|-------|--------|
| **Source** | Enron email network (SNAP) |
| **URL** | https://snap.stanford.edu/data/email-Enron.txt.gz |
| **Citation** | Leskovec et al., Community Structure in Large Networks, Internet Mathematics 6(1) 29–123, 2009; SNAP Stanford. |
| **File hash (SHA-256)** | 55cfead79b1f0161786179a48796c2a119bd7026a246238b257b6be9d8b69b68 |
| **Pipeline date (UTC)** | 2026-03-07T21:08:45Z |
| **n_original** | 36,692 nodes |
| **n_lcc** | 33,696 (largest connected component) |
| **n_used** | 60 (subgraph: top 60 nodes by degree, for feasible greedy Test D) |
| **Kernel recipe** | PRD-01 §2.5: undirected edge list → symmetric adjacency → row-normalized K; μ = stationary distribution (floored for L2(μ)); LCC then degree-subgraph. |
| **Tests enabled** | Test D (q* vs Louvain; org-chart not used in this run) |

---

## 4. Commands executed

```bash
pytest tests/ -v --tb=short
python scripts/generate_verification_report.py
python scripts/run_public_data_verification.py --out docs/public_data_report.txt
```

Seeds: synthetic per TEST_SPEC.md §5; verification report seed 42 (main), 43 (bootstrap).

---

## 5. Test results (Domain 6.1)

| Result | Count |
|--------|--------|
| Passed | 19 |
| Failed | 0 |

**Modules:** test_discrimination (2), test_estimators (8), test_synthetic (5), test_theorems (4).

---

## 6. Verification report — Domain 6.1

| Item | Result |
|------|--------|
| **T3.2** | N=200, violations=0, max_ratio=0.000000 |
| **T3.3** | N=50, max_decay_ratio=1.114299 (design note: reversible, finite t) |
| **T3.4** | N=30, steps in [4, 8], all ≤ n−1: True |
| **E6.1** | AUC(E_cl)=1.0000 [1.0000, 1.0000], AUC(Q)=1.0000 [1.0000, 1.0000], closure ≥ Q−0.05: True |

Full text: `verification_report.txt` in this directory.

---

## 7. Verification report — Domain 6.4 (Test D)

| Method | |q| | E_cl(q) | Q(q) |
|--------|-----|----------|--------|
| **q* (greedy T3.4)** | 1 block | 0.000000 | 0.000000 |
| **Louvain [6]** | 5 communities | 0.073968 | 0.234385 |

**Note:** No org-chart partition used; full Test D (precision/recall/NMI vs q_org) not applicable. Calibration: framework and baseline on same public kernel.

Full text: `public_data_report.txt` in this directory.

---

## 8. Baseline comparison

- **E6.1 (6.1):** Graph modularity Q [5]. Criterion: AUC(closure) ≥ AUC(Q) − 0.05. **Result:** Met (AUC 1.0 both).
- **6.4 (Test D):** Louvain [6]. Both E_cl and Q reported for q* and Louvain on same kernel. See `outputs/BASELINES.md`.

---

## 9. Findings

1. **Domain 6.1:** All MVP claims (T3.1–T3.4, E6.1) numerically supported; no falsification.
2. **Domain 6.4:** Public data (Enron SNAP) kernel loaded; Test D executed (q*, Louvain); E_cl and Q reported. Reproducible via manifest and pipeline scripts.
3. **Limitations:** 60-node subgraph; org-chart not used; full Test D vs q_org deferred.

---

## 10. Artifacts in this run directory

- `run_report.md` (this file)
- `verification_report.txt` (Domain 6.1)
- `public_data_report.txt` (Domain 6.4)
- `claim_registry_snapshot.yaml`

---

## 11. References

- Vick (2025), *Boundary-Preserving Organization in Dynamical Systems*
- PRD-01, PRD-04, PRD-05, PRD-06, PRD-08
- `outputs/METHODOLOGY.md`, `outputs/BASELINES.md`
- Enron SNAP: Leskovec et al. (2009); SNAP Stanford.
