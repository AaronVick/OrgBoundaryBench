#!/usr/bin/env python3
"""PRD II (thoughts3): Null-Model and Rival-Theory Audit. D = Perf(q*) - max(baselines U nulls)."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.null_rival_audit import run_null_rival_audit, run_null_rival_audit_bootstrap


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD II: Null and rival audit.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--with-labels", action="store_true")
    ap.add_argument("--bootstrap", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n
    labels = rng.integers(0, 3, size=args.n) if args.with_labels else None

    if args.bootstrap > 0:
        result, pass_ = run_null_rival_audit_bootstrap(K, mu, labels, n_bootstrap=args.bootstrap, rng=rng)
        lines = [
            "# PRD II: Null-Model and Rival-Theory Audit (bootstrap)",
            f"mean_D: {result['mean_D']:.6f}",
            f"CI_lower: {result['ci_lower']:.6f}, CI_upper: {result['ci_upper']:.6f}",
            f"Pass: {pass_}",
        ]
    else:
        result, pass_ = run_null_rival_audit(K, mu, labels, rng=rng)
        lines = [
            "# PRD II: Null-Model and Rival-Theory Audit",
            f"Perf(q*): {result['perf_star']:.6f}",
            f"max(baselines U nulls): {result['max_baseline_or_null']:.6f}",
            f"D: {result['D']:.6f}",
            f"Pass (D > 0): {pass_}",
        ]

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "null_rival_audit_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
