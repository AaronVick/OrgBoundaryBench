# Scientific outputs: BPO and Relational Closure frameworks

This directory holds **scientific-method-based outputs** from both empirical frameworks: **Boundary-Preserving Organization (BPO)** (Vick 2025) and **Relational Closure / Topology of Interiority (RCTI)** (Vick, PRD-13). Methodology, run reports, findings, baseline comparisons, and claim/falsification documentation. All runs follow PRD-04/06/08 (BPO) and PRD-13 (RCTI). See **docs/FRAMEWORKS.md** for the shared pipeline (methodology → testing → output → findings).

## Layout

| Path | Purpose |
|------|---------|
| **METHODOLOGY.md** | Standing document: scientific method, BPO and cross-framework (§6.1), run procedure, seeds, reproducibility. |
| **METHODOLOGY_RCTI.md** | RCTI-specific: C1–C4, C2F, F1–F5, pipeline, first empirical test (Appendix A). |
| **BASELINES.md** | Baseline methods (graph modularity Q [5], Louvain [6], etc.) and comparison criteria for BPO claims. |
| **FINDINGS.md** | Aggregated empirical findings (BPO and RCTI) from runs; falsification status. |
| **runs/** | Timestamped run directories (e.g. `runs/2026-03-07T123456/`). Each contains: run report, verification report(s), claim/falsification artifacts. |
| **runs/<run_id>/run_report.md** | Per-run: **frameworks** tag ([BPO] and/or [RelationalClosure]), methodology, environment, test results, findings, artifacts. |
| **runs/<run_id>/verification_report.txt** | BPO: T3.2/T3.3/T3.4/E6.1 verification output. |
| **runs/<run_id>/rcti_verification_report.txt** | RCTI: C1/C4b/C2F, persistence entropy, method. |
| **runs/<run_id>/barcode_summary.json** | RCTI: persistence barcode, Betti, PE. |
| **runs/<run_id>/conditions_C1_C4_C2F.yaml** | RCTI: C1/C4b/C2F satisfaction. |
| **runs/<run_id>/falsification_F1_F5.md** | RCTI: F1–F5 checklist status. |
| **runs/<run_id>/claim_registry_snapshot.yaml** | BPO claim registry state at run time. |
| **runs/<run_id>/figures/** | Optional: closure arch, T3.2 scatter (if generated). |

**Public-facing findings (PRD XII buttonup):** Run `python scripts/build_public_findings.py` to regenerate `findings_summary.md`, `benchmark_leaderboard.csv`, `null_audit_summary.md`, `outlier_audit_summary.md`, `model_registry.csv`, `failure_gallery.md`, and `dataset_provenance.md` from `runs/`. One command; deterministic stubs when no runs present. See METHODOLOGY.md §6.2.

**Example runs:**  
- `runs/2026-03-08T001500Z/` — **BPO:** Domain 6.1 + 6.4 public data; full methodology, provenance, baselines, findings.  
- `runs/2026-03-07T214654Z/` — **RCTI:** Relational Closure synthetic (directed cycle + noise); C1/C4b, barcode, falsification F1–F5.  
- Additional BPO runs in `runs/` (6.1 MVP, 6.1+6.4 Enron).

## Data scope

- **Domain 6.1 (synthetic):** In-repo generators (PRD-04). No external download required.
- **Domain 6.4 (public data):** Enron SNAP is implemented: `scripts/download_and_normalize.py` and `scripts/run_public_data_verification.py`. Run reports document URL, hash, kernel recipe (PRD-01 §2.5), and Test D results.
- **Domains 6.2, 6.3, 6.5, 6.6:** Pipeline and tests to be added per PRD-01 §2.3 and PRD-05. **PRD-12** lists additional public datasets (Karate, Football, EU email, OpenWorm, etc.) with kernel recipes and test mapping for expanding coverage.

## References

- Paper: Vick, *Boundary-Preserving Organization in Dynamical Systems* (2025).
- PRDs: `docs/prds/` (00–10); METHODOLOGY: `docs/METHODOLOGY.md`; REPRODUCIBILITY: `docs/REPRODUCIBILITY.md`.
