#!/usr/bin/env python3
"""
Governance Stress Test (PRD-18). Empirical Test Family B.

Runs perturbation families (noise, missingness, workload_scale) on (K, μ), recomputes
closure and NMI; writes governance_stress_report.txt.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.governance_stress import run_stress_test


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-18: Governance stress — perturbations, stability, pass/fail.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    trials, summary, success = run_stress_test(
        K, mu,
        noise_strength=0.05,
        missingness_frac=0.1,
        n_trials_per_family=2,
        stability_nmi_min=0.5,
        rng=rng,
    )

    lines = [
        "# Governance Stress Test (PRD-18) — Empirical Test Family B",
        f"# n={args.n}, stability_nmi_min={summary['stability_nmi_min']}",
        "",
        "## Summary",
        f"mean_nmi: {summary['mean_nmi']:.4f}",
        f"stable_fraction: {summary['stable_fraction']:.4f}",
        f"mean_E_cl_ratio_baseline_on_pert: {summary['mean_E_cl_ratio_baseline_on_pert']:.4f}",
        f"pass: {summary['pass']}",
        "",
        "## Per-trial (family, trial, n_blocks_pert, E_cl_pert, nmi)",
    ]
    for t in trials:
        lines.append(f"  {t['family']} trial={t['trial']} n_blocks_pert={t['n_blocks_pert']} E_cl_pert={t['E_cl_pert']:.6f} nmi={t['nmi']:.4f}")

    report_path = out_dir / "governance_stress_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
