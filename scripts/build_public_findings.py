#!/usr/bin/env python3
"""
PRD XII (buttonup): Findings and Outputs Publishing Layer.

One command regenerates all public-facing summaries from raw run outputs.
Required artifacts: findings_summary.md, benchmark_leaderboard.csv, null_audit_summary.md,
outlier_audit_summary.md, model_registry.csv, failure_gallery.md, dataset_provenance.md.
Deterministic: if no runs present, writes stub content so artifacts exist and are citable.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_dirs(runs_dir: Path) -> list[Path]:
    """Subdirs of runs_dir that look like run IDs (e.g. ISO timestamp or prd23_synthetic)."""
    if not runs_dir.exists():
        return []
    out = []
    for p in sorted(runs_dir.iterdir()):
        if p.is_dir():
            out.append(p)
    return out


def _collect_pass_fail(report_path: Path) -> str | None:
    """Extract Pass/Success True/False from report if present."""
    if not report_path.exists():
        return None
    text = report_path.read_text()
    # Accept variants like:
    #   Pass: True
    #   Pass (D > 0): False
    #   Overall pass (null/rival and leverage): False
    m = re.search(r"\bpass[^\n:]*:\s*(true|false)\b", text, re.I)
    if m:
        return m.group(1).capitalize()
    # Benchmark reports often use "Success" instead of "Pass".
    m = re.search(r"\bsuccess[^\n:]*:\s*(true|false)\b", text, re.I)
    return m.group(1).capitalize() if m else None


def _report_paths(runs_dir: Path, report_name: str) -> list[Path]:
    """Find report files recursively under runs_dir."""
    if not runs_dir.exists():
        return []
    return sorted(p for p in runs_dir.rglob(report_name) if p.is_file())


def _collect_reports(runs_dir: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """Gather (run_id, report_type, path, pass_fail) for leaderboard, null, outlier, failures."""
    leaderboard_rows = []
    null_rows = []
    outlier_rows = []
    failures = []
    # Boundary / benchmark
    for name in ("boundary_benchmark_report.txt", "nontrivial_boundary_report.txt"):
        for p in _report_paths(runs_dir, name):
            run_id = p.parent.relative_to(runs_dir).as_posix()
            pf = _collect_pass_fail(p)
            leaderboard_rows.append({"run_id": run_id, "report": name, "pass": pf or ""})
            if pf == "False":
                failures.append({"run_id": run_id, "report": name, "reason": "Pass: False"})

    # Null audit
    for p in _report_paths(runs_dir, "null_rival_audit_report.txt"):
        run_id = p.parent.relative_to(runs_dir).as_posix()
        pf = _collect_pass_fail(p)
        null_rows.append({"run_id": run_id, "pass": pf or ""})

    # Outlier / leverage
    for p in _report_paths(runs_dir, "leverage_stability_report.txt"):
        run_id = p.parent.relative_to(runs_dir).as_posix()
        pf = _collect_pass_fail(p)
        outlier_rows.append({"run_id": run_id, "pass": pf or ""})
    return leaderboard_rows, null_rows, outlier_rows, failures


def build_findings_summary(out_dir: Path, runs_dir: Path, has_runs: bool) -> None:
    """Write findings_summary.md: rollup of findings; if no runs, stub with pointer to FINDINGS.md."""
    path = out_dir / "findings_summary.md"
    if has_runs:
        lines = [
            "# Findings Summary (Public)",
            "",
            "Regenerated from run outputs. For full narrative see `outputs/FINDINGS.md`.",
            "",
            "## Source",
            f"- Runs directory: `{runs_dir}`",
            "- Methodology: outputs/METHODOLOGY.md",
            "",
            "## Status",
            "Findings are aggregated from latest successful runs; negative results included.",
            "",
        ]
    else:
        lines = [
            "# Findings Summary (Public)",
            "",
            "No run directories found. Run empirical scripts (see outputs/METHODOLOGY.md) then re-run this script.",
            "",
            "Full methodology and findings narrative: `outputs/FINDINGS.md`.",
            "",
        ]
    path.write_text("\n".join(lines))


def build_benchmark_leaderboard(out_dir: Path, rows: list[dict]) -> None:
    """Write benchmark_leaderboard.csv."""
    path = out_dir / "benchmark_leaderboard.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "report", "pass"])
        w.writeheader()
        if rows:
            w.writerows(rows)
        else:
            w.writerow({"run_id": "none", "report": "no runs", "pass": ""})


def build_null_audit_summary(out_dir: Path, rows: list[dict]) -> None:
    """Write null_audit_summary.md."""
    path = out_dir / "null_audit_summary.md"
    lines = ["# Null Audit Summary", ""]
    if rows:
        for r in rows:
            lines.append(f"- Run `{r['run_id']}`: Pass = {r['pass']}")
    else:
        lines.append("No null_rival_audit_report.txt found in run directories.")
    path.write_text("\n".join(lines))


def build_outlier_audit_summary(out_dir: Path, rows: list[dict]) -> None:
    """Write outlier_audit_summary.md (leverage stability)."""
    path = out_dir / "outlier_audit_summary.md"
    lines = ["# Outlier / Leverage Audit Summary", ""]
    if rows:
        for r in rows:
            lines.append(f"- Run `{r['run_id']}`: Pass = {r['pass']}")
    else:
        lines.append("No leverage_stability_report.txt found in run directories.")
    path.write_text("\n".join(lines))


def build_model_registry(out_dir: Path, runs_dir: Path) -> None:
    """Write model_registry.csv stub or from claim_registry_snapshot."""
    path = out_dir / "model_registry.csv"
    rows = []
    for run_path in _run_dirs(runs_dir):
        p = run_path / "claim_registry_snapshot.yaml"
        rows.append({"run_id": run_path.name, "claim_registry": "yes" if p.exists() else "no"})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run_id", "claim_registry"])
        w.writeheader()
        if rows:
            w.writerows(rows)
        else:
            w.writerow({"run_id": "none", "claim_registry": "no"})


def build_failure_gallery(out_dir: Path, failures: list[dict]) -> None:
    """Write failure_gallery.md: failed cases with explanation."""
    path = out_dir / "failure_gallery.md"
    lines = ["# Failure Gallery", "", "Runs or reports where Pass: False (negative results).", ""]
    if failures:
        for f in failures:
            lines.append(f"- **{f['run_id']}** / {f['report']}: {f['reason']}")
    else:
        lines.append("No failed reports collected (or no runs).")
    path.write_text("\n".join(lines))


def build_dataset_provenance(out_dir: Path, runs_dir: Path) -> None:
    """Write dataset_provenance.md stub."""
    path = out_dir / "dataset_provenance.md"
    lines = [
        "# Dataset Provenance",
        "",
        "Public datasets used in runs. Per-run provenance in run_report.md and manifest files.",
        "",
        "| Dataset | Domain | Source |",
        "|---------|--------|--------|",
        "| Synthetic (6.1) | 6.1 | Generated per PRD-04 |",
        "| Enron SNAP | 6.4 | SNAP Stanford |",
        "| email-Eu-core | 6.4 / thoughts3 | SNAP Stanford |",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD XII: Regenerate public-facing findings from run outputs.")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs", help="Output directory for artifacts")
    ap.add_argument("--runs-dir", type=Path, default=None, help="Runs directory (default: out-dir/runs)")
    args = ap.parse_args()
    out_dir = Path(args.out_dir).resolve()
    runs_dir = Path(args.runs_dir).resolve() if args.runs_dir else (out_dir / "runs")
    out_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = _run_dirs(runs_dir)
    has_runs = len(run_dirs) > 0
    leaderboard_rows, null_rows, outlier_rows, failures = _collect_reports(runs_dir)

    build_findings_summary(out_dir, runs_dir, has_runs)
    build_benchmark_leaderboard(out_dir, leaderboard_rows)
    build_null_audit_summary(out_dir, null_rows)
    build_outlier_audit_summary(out_dir, outlier_rows)
    build_model_registry(out_dir, runs_dir)
    build_failure_gallery(out_dir, failures)
    build_dataset_provenance(out_dir, runs_dir)

    print(f"Wrote 7 artifacts to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
