#!/usr/bin/env python3
"""
PRD-28: Cross-Construction Invariance and Artifact Audit.

Multiple constructions (raw, threshold, symmetrized); bootstrap stability of topology (PE);
fail if conclusions reverse under mild construction change.
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

from relational_closure.cross_construction_invariance import (
    construction_raw,
    construction_threshold,
    construction_symmetrized,
    run_cross_construction_invariance,
)


def make_synthetic_W(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    W = np.zeros((n, n))
    for i in range(n):
        W[i, (i + 1) % n] = 1.0
    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < 0.2:
                W[i, j] = rng.uniform(0.2, 1.0)
    return W


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-28: Cross-construction invariance — topology stability across constructions.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n-samples", type=int, default=8, help="Number of graphs (for rank correlation)")
    ap.add_argument("--n", type=int, default=6, help="Graph size")
    ap.add_argument("--tau", type=float, default=0.1)
    ap.add_argument("--rank-correlation-min", type=float, default=0.3)
    ap.add_argument("--no-gudhi", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    samples = [make_synthetic_W(args.n, rng.integers(0, 100000)) for _ in range(args.n_samples)]

    construction_fns = [
        ("raw", construction_raw),
        ("threshold_0.5", lambda W: construction_threshold(W, 0.5)),
        ("symmetrized", construction_symmetrized),
    ]
    result, pass_ = run_cross_construction_invariance(
        samples,
        construction_fns,
        tau=args.tau,
        use_gudhi=not args.no_gudhi,
        rank_correlation_min=args.rank_correlation_min,
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# PRD-28: Cross-Construction Invariance and Artifact Audit",
        f"# n_samples={result['n_samples']}, n_constructions={result['n_constructions']}, n_nodes={args.n}",
        "",
        "## Construction names: " + ", ".join(result["construction_names"]),
        "## Mean PE per construction: " + ", ".join(f"{x:.4f}" for x in result["mean_PE_per_construction"]),
        "",
        f"## Rank correlation (PE across constructions): {result['rank_correlation_pe']:.4f}",
        f"## Conclusions agree (no reversal): {result['conclusions_agree']}",
        "",
        f"## Pass: {pass_}",
        "## Falsification: Conclusions reverse under mild construction change, or low bootstrap stability (PRD-28 §4).",
        "",
    ]
    report_path = out_dir / "cross_construction_invariance_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
