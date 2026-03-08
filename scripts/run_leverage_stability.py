#!/usr/bin/env python3
"""
PRD III (thoughts3): Outlier and Leverage Stability Test.

S(q) = max |Perf(q) - Perf(q^{-A})| over node-drop and edge-drop. Pass if S < threshold.
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

from boundary_org.leverage_stability import run_leverage_stability


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD III: Leverage stability — S = max |Perf(q) - Perf(q^{-A})|.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--epsilon", type=float, nargs="+", default=[0.05, 0.1], help="Drop fractions")
    ap.add_argument("--n-trials", type=int, default=2)
    ap.add_argument("--threshold", type=float, default=1.0, help="Pass if S_max < threshold")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    result, pass_ = run_leverage_stability(
        K, mu,
        epsilon_list=tuple(args.epsilon),
        n_trials_per_epsilon=args.n_trials,
        stability_threshold=args.threshold,
        rng=rng,
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PRD III: Outlier and Leverage Stability Test",
        f"# n={args.n}, epsilon={args.epsilon}, threshold={args.threshold}",
        "",
        f"Perf(q_full): {result['perf_full']:.6f}",
        f"S_max: {result['S_max']:.6f}",
        f"n_perturbations: {result['n_perturbations']}",
        "",
        f"Pass (S_max < threshold): {pass_}",
        "Falsification: S above threshold implies results not stable under removals (thoughts3 PRD III).",
    ]
    report_path = out_dir / "leverage_stability_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
