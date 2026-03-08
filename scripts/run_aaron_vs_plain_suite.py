#!/usr/bin/env python3
"""
PRD XVII (extendedPRD.md): Aaron-vs-Plain-LLM Public Use-Case Suite.

Runs boundary benchmark, null/rival audit, leverage stability into one run dir;
regenerates public findings (leaderboard, governance, failure gallery, model registry);
writes aaron_vs_plain_suite_report.txt with arms and outcomes.

Arms (structural proxy): framework (q*) vs one-block, singleton, Louvain, random.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD XVII: Aaron-vs-plain suite — benchmark + null + leverage + findings.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    run_dir = out_dir / "aaron_vs_plain_suite_run"
    run_dir.mkdir(parents=True, exist_ok=True)

    scripts_dir = ROOT / "scripts"
    py = sys.executable

    # Run boundary benchmark, null/rival, leverage into same run_dir
    for script, extra in [
        ("run_boundary_benchmark.py", ["--n", str(args.n), "--n-random", "1"]),
        ("run_null_rival_audit.py", ["--n", str(args.n), "--seed", str(args.seed)]),
        ("run_leverage_stability.py", ["--n", str(args.n), "--n-trials", "1"]),
    ]:
        r = subprocess.run(
            [py, str(scripts_dir / script), "--out-dir", str(run_dir)] + extra,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if r.returncode not in (0, 1):
            print(f"Warning: {script} exited {r.returncode}", file=sys.stderr)

    # Regenerate public findings from this run dir (runs_dir = out_dir so it finds run_dir)
    r = subprocess.run(
        [py, str(scripts_dir / "build_public_findings.py"), "--out-dir", str(out_dir), "--runs-dir", str(out_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"Warning: build_public_findings exited {r.returncode}: {r.stderr}", file=sys.stderr)

    # Summarize arms and outcomes for PRD XVII
    arms = "Framework (q*), one-block, singleton, Louvain, random (null/rival); leverage = node/edge drop."
    lines = [
        "# PRD XVII: Aaron-vs-Plain Use-Case Suite",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Hypothesis",
        "Structural proxy: boundary/closure framework (q*) should outperform one-block, singleton, Louvain, random.",
        "Results should be robust to leverage (outlier removal).",
        "",
        "## 2. Methods",
        "Ran boundary_benchmark, null_rival_audit, leverage_stability into one run dir;",
        "then build_public_findings for leaderboard, null_audit_summary, outlier_audit_summary, failure_gallery, model_registry.",
        "",
        "## 3. Public data used",
        f"Synthetic: n={args.n}, seed={args.seed}. For full PRD XVII use GH Archive, wiki-talk-temporal, email-Eu-core.",
        "",
        "## 4. Baseline (arms)",
        arms,
        "",
        "## 5. Outcomes",
        "",
        f"Run dir: {run_dir}",
        "Artifacts: boundary_benchmark_report.txt, null_rival_audit_report.txt, leverage_stability_report.txt.",
        "Public findings (in out_dir): findings_summary.md, benchmark_leaderboard.csv, null_audit_summary.md, outlier_audit_summary.md, model_registry.csv, failure_gallery.md, dataset_provenance.md.",
        "",
        "## 6. Falsification",
        "If q* does not beat baselines (D ≤ 0) or leverage sensitivity (S_max ≥ threshold), claim fails.",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Gains from extra orchestration rather than math; use sham-complexity control (Arm C).",
        "• LLM arms not included; this is structural proxy only.",
    ]
    report_path = out_dir / "aaron_vs_plain_suite_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
