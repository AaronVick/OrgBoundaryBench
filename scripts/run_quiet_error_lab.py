#!/usr/bin/env python3
"""
Quiet Error Detection Lab (PRD-19). Empirical Test Family C.

Planted errors (row_swap) vs control; detector = closure/partition change; writes quiet_error_report.txt.
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

from boundary_org.quiet_error_lab import run_quiet_error_lab


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-19: Quiet error lab — planted errors, detection, false reassurance.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--n-planted", type=int, default=5)
    ap.add_argument("--n-control", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cases, summary, success = run_quiet_error_lab(
        K, mu,
        n_control=args.n_control,
        n_planted=args.n_planted,
        rng=rng,
    )

    lines = [
        "# Quiet Error Detection Lab (PRD-19) — Empirical Test Family C",
        f"# n={args.n}, n_control={summary['n_control']}, n_planted={summary['n_planted']}",
        "",
        "## Summary",
        f"detection_rate: {summary['detection_rate']:.4f}",
        f"false_reassurance_rate: {summary['false_reassurance_rate']:.4f}",
        f"false_positive_rate: {summary['false_positive_rate']:.4f}",
        f"pass: {summary['pass']}",
        "",
        "## Per-case (has_error, flagged)",
    ]
    for c in cases[:10]:
        lines.append(f"  has_error={c['has_error']} flagged={c['flagged']} E_cl_ratio={c.get('E_cl_ratio', 0):.4f} nmi={c.get('nmi', 0):.4f}")
    if len(cases) > 10:
        lines.append(f"  ... ({len(cases)} total)")

    report_path = out_dir / "quiet_error_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
