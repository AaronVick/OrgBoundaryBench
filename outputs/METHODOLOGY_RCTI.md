# Methodology: Relational Closure / Topology of Interiority (RCTI)

**Purpose:** Document how the RCTI empirical program turns the paper’s math into testable outputs and findings. PRD-13, *Relational Closure and the Topology of Interiority* (Vick).

---

## 1. Formal object and measures

- **Relational field:** R = (V, S, ∂); directed simplicial complex S over vertices V.
- **Construction:** Directed weighted graph G → directed flag complex dFlag(G). Filtration: edge-weight threshold (include edge if weight ≥ t); simplex birth = min edge weight in simplex.
- **Primary measures:** Homological complexity HC = Σ_k β_k; closure fidelity C2F; persistence barcode B; persistence entropy PE.

---

## 2. Conditions (paper §3.3)

| Condition | Operationalization |
|-----------|--------------------|
| **C1** | At least one β₁ bar with lifespan > τ at matched density. |
| **C2** | Self-referential inclusion → C2F = 1 − Σ_k w_k β_k(S,S') / Σ_k w_k β_k(S); S' pre-registered. |
| **C3** | Barcode stability: d_B(B(t), B(t+1)) < δ across temporal windows. |
| **C4b** | Non-trivial β_k for k ≥ 2. |

---

## 3. Falsification (F1–F5)

- **F1:** Barcode fails to separate conscious vs unconscious across ≥3 constructions → refutes central claim.
- **F2:** C2F does not correlate with self-boundary phenomenology → refutes C2.
- **F3:** LLMs satisfy C1–C4 → framework predicts consciousness (substrate neutrality).
- **F4:** HC and C2F do not dissociate → two-parameter framework collapses.
- **F5:** Topological differences vanish under matched-density control → thresholding artifact.

**Constraints:** Matched-density controls; filtration-sweep stability; convergence across ≥2 relational field constructions; filtration type named.

---

## 4. Pipeline (this repo)

1. **Input:** Directed weight matrix W (e.g. from synthetic cycle, or from directed connectivity).
2. **Directed flag:** `relational_closure.directed_flag_complex(W)` → list of (simplex, birth).
3. **Persistence:** `barcode_from_complex(...)` → barcode (gudhi if available, else cycle-rank β₁ proxy).
4. **Conditions:** `check_C1`, `check_C4b`, `compute_C2F` (with optional S').
5. **Output:** rcti_verification_report.txt, barcode_summary.json, conditions_C1_C4_C2F.yaml, falsification_F1_F5.md.

---

## 5. Run and report

- **Run:** `python scripts/run_rcti_verification.py [--out-dir outputs/runs/<id>]`
- **Report:** Tag `frameworks: [RelationalClosure]` in run_report.md; cite C1–C4, F1–F5; document construction and matched-density when applicable.
- **First empirical test (paper Appendix A):** Graded propofol EEG; directed connectivity → dFlag → barcode; calibration τ, δ, C2F cutoff; C2F predicted to degrade before C1.

---

## 6. References

- PRD-13, docs/FRAMEWORKS.md, outputs/METHODOLOGY.md §6.1
- Paper: *Relational Closure and the Topology of Interiority*, Appendix A, Tables 2–3
