#!/usr/bin/env python3
"""
Write run_report.md for a run directory (unified BPO + RCTI).

Reads existing artifacts (verification_report.txt, public_data_report.txt,
rcti_verification_report.txt, etc.) and produces run_report.md with frameworks tag,
methodology, results, and findings. PRD-13, docs/FRAMEWORKS.md.
"""

from __future__ import annotations

import argparse
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_file(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text().strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Write run_report.md for a run directory.")
    ap.add_argument("--run-dir", type=Path, required=True, help="Run directory (e.g. outputs/runs/2026-03-08T001500Z)")
    ap.add_argument("--frameworks", nargs="+", default=["BPO"], choices=["BPO", "RelationalClosure"], help="Frameworks tested")
    ap.add_argument("--domains", type=str, default="6.1 (Synthetic) + 6.4 (Public data — Enron SNAP)", help="Domains run (BPO)")
    args = ap.parse_args()

    run_dir = args.run_dir.resolve()
    if not run_dir.is_dir():
        print(f"Not a directory: {run_dir}", file=sys.stderr)
        return 1

    frameworks = args.frameworks
    has_bpo = "BPO" in frameworks
    has_rcti = "RelationalClosure" in frameworks

    v_report = read_file(run_dir / "verification_report.txt")
    p_report = read_file(run_dir / "public_data_report.txt")
    rcti_report = read_file(run_dir / "rcti_verification_report.txt")
    fals_report = read_file(run_dir / "falsification_F1_F5.md")

    run_id = run_dir.name
    frameworks_str = ", ".join(frameworks)

    sections = []

    # Title and frameworks
    sections.append(f"# Run report: {run_id}\n")
    sections.append(f"**Frameworks:** {frameworks_str}")
    sections.append(f"**Domains:** {args.domains}")
    sections.append("**References:** PRD-04, PRD-05, PRD-06, PRD-08; PRD-13 (RCTI).\n")
    sections.append("---\n")

    # 1. Methodology
    sections.append("## 1. Methodology\n")
    sections.append("- **Scientific method:** Claims with operational falsification; fixed seeds; baseline comparison. See `outputs/METHODOLOGY.md`.")
    if has_rcti:
        sections.append("- **RCTI:** C1–C4, C2F, F1–F5; PRD-13; `outputs/METHODOLOGY_RCTI.md`.")
    sections.append("- **Procedure:** Tests and verification scripts as per docs/FRAMEWORKS.md.\n")

    # 2. Environment
    sections.append("## 2. Environment\n")
    sections.append("| Item | Value |")
    sections.append("|------|--------|")
    sections.append(f"| Python | {sys.version.split()[0]} |")
    sections.append(f"| Platform | {platform.system()} ({platform.machine()}) |")
    sections.append("| Install | `pip install -e \".[test]\"`; optional `.[data]` `.[rcti]` |\n")

    # 3. BPO results
    if has_bpo and v_report:
        sections.append("## 3. Test results (Domain 6.1 — BPO)\n")
        sections.append("```")
        sections.append(v_report)
        sections.append("```\n")
    if has_bpo and p_report:
        sections.append("## 4. Public data (Domain 6.4 — BPO)\n")
        sections.append("```")
        sections.append(p_report)
        sections.append("```\n")

    # 5. RCTI results
    if has_rcti and rcti_report:
        sections.append("## 5. RCTI verification (Relational Closure)\n")
        sections.append("```")
        sections.append(rcti_report)
        sections.append("```\n")
    if has_rcti and fals_report:
        sections.append("## 6. Falsification (F1–F5)\n")
        sections.append(fals_report)
        sections.append("")

    # Findings
    sections.append("## 7. Findings\n")
    findings = []
    if has_bpo:
        findings.append("1. **BPO:** Domain 6.1 and (if run) 6.4 verification as above; claim status in claim_registry_snapshot.")
    if has_rcti:
        findings.append("2. **RCTI:** C1/C4b/C2F from pipeline; F1–F5 not triggered in synthetic run (see falsification_F1_F5.md).")
    findings.append("3. **Limitations:** See methodology and PRD-09, PRD-13.")
    sections.append("\n".join(findings))
    sections.append("\n")

    # Artifacts
    sections.append("## 8. Artifacts in this run directory\n")
    artifacts = ["run_report.md"]
    if has_bpo:
        artifacts.extend(["verification_report.txt", "public_data_report.txt", "claim_registry_snapshot.yaml"])
    if has_rcti:
        artifacts.extend(["rcti_verification_report.txt", "barcode_summary.json", "conditions_C1_C4_C2F.yaml", "falsification_F1_F5.md"])
    for a in artifacts:
        sections.append(f"- `{a}`")
    sections.append("\n")

    # References
    sections.append("## 9. References\n")
    sections.append("- Vick (2025), *Boundary-Preserving Organization in Dynamical Systems*")
    sections.append("- Vick, *Relational Closure and the Topology of Interiority* (RCTI)")
    sections.append("- PRD-00–13, outputs/METHODOLOGY.md, docs/FRAMEWORKS.md\n")

    report = "\n".join(sections)
    (run_dir / "run_report.md").write_text(report)
    print("Wrote", run_dir / "run_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
