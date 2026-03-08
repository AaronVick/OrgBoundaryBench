# Run report: 2026-03-07T214654Z

**Frameworks:** RelationalClosure
**Domains:** RCTI synthetic (directed cycle + noise)
**References:** PRD-04, PRD-05, PRD-06, PRD-08; PRD-13 (RCTI).

---

## 1. Methodology

- **Scientific method:** Claims with operational falsification; fixed seeds; baseline comparison. See `outputs/METHODOLOGY.md`.
- **RCTI:** C1–C4, C2F, F1–F5; PRD-13; `outputs/METHODOLOGY_RCTI.md`.
- **Procedure:** Tests and verification scripts as per docs/FRAMEWORKS.md.

## 2. Environment

| Item | Value |
|------|--------|
| Python | 3.12.8 |
| Platform | Darwin (arm64) |
| Install | `pip install -e ".[test]"`; optional `.[data]` `.[rcti]` |

## 5. RCTI verification (Relational Closure)

```
# RCTI verification report (Relational Closure / Topology of Interiority)
# Pipeline: directed_flag → persistence → C1/C4b/C2F
# Method: cycle_rank_proxy

C1: C1: satisfied (max β₁ lifespan=0.5000 > τ=0.1)
C4b: C4b: no higher-dimensional features (β_k=0 for k≥2)
Persistence entropy: 0.693147
n_simplices: 14
```

## 6. Falsification (F1–F5)

# Falsification checklist (PRD-13 §3)

| ID | Condition | Status |
|----|-----------|--------|
| F1 | Barcode discrimination (conscious vs unconscious) | Not tested (synthetic only) |
| F2 | C2F decorrelation with self-boundary phenomenology | Not tested |
| F3 | Transformer surprise (C1–C4 satisfied by LLM) | Not tested |
| F4 | Dissociation (HC vs C2F) | Not tested (single run) |
| F5 | Density artifact (matched-density control) | N/A (single threshold) |

Methodological constraints: matched-density and multi-construction required for neural/real-data runs.

## 7. Findings

2. **RCTI:** C1/C4b/C2F from pipeline; F1–F5 not triggered in synthetic run (see falsification_F1_F5.md).
3. **Limitations:** See methodology and PRD-09, PRD-13.


## 8. Artifacts in this run directory

- `run_report.md`
- `rcti_verification_report.txt`
- `barcode_summary.json`
- `conditions_C1_C4_C2F.yaml`
- `falsification_F1_F5.md`


## 9. References

- Vick (2025), *Boundary-Preserving Organization in Dynamical Systems*
- Vick, *Relational Closure and the Topology of Interiority* (RCTI)
- PRD-00–13, outputs/METHODOLOGY.md, docs/FRAMEWORKS.md
