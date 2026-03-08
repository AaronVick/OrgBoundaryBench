#!/usr/bin/env python3
"""
RCTI Comparative Pipeline (PRD-21). Empirical Test Family E.

Runs ≥2 relational-field constructions on the same data, computes topology (C1, C4b, C2F, PE)
and graph baselines (density, clustering, reciprocity, modularity, spectral gap, entropy).
Writes rcti_comparative_report.txt. Does not require condition labels; reports values per construction.
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

from relational_closure.pipeline import run_pipeline
from relational_closure.graph_baselines import compute_all_baselines


def make_synthetic_directed(n: int = 8, seed: int = 42) -> np.ndarray:
    """Directed cycle plus noise for non-trivial topology."""
    rng = np.random.default_rng(seed)
    W = np.zeros((n, n))
    for i in range(n):
        W[i, (i + 1) % n] = 1.0
    for i in range(n):
        for j in range(n):
            if i != j and (i + 1) % n != j:
                if rng.random() < 0.2:
                    W[i, j] = rng.uniform(0.3, 1.0)
    return W


def construction_raw(W: np.ndarray) -> np.ndarray:
    """Construction 1: raw directed weights."""
    return np.asarray(W, dtype=float)


def construction_threshold(W: np.ndarray, quantile: float = 0.5) -> np.ndarray:
    """Construction 2: threshold at quantile of positive edge weights (matched-density control)."""
    W = np.asarray(W, dtype=float)
    vals = W[W > 0]
    if vals.size == 0:
        return W
    thresh = float(np.quantile(vals, quantile))
    W2 = np.where(W >= thresh, W, 0.0)
    return W2


def construction_symmetrized(W: np.ndarray) -> np.ndarray:
    """Construction 3: symmetrized (W + W.T)/2 — same graph but symmetric; directed flag still uses it as directed (both directions)."""
    return (np.asarray(W) + np.asarray(W).T) / 2.0


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-21: RCTI Comparative — topology vs graph baselines across constructions.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: outputs/runs/<ISO timestamp>)")
    ap.add_argument("--n", type=int, default=8, help="Synthetic graph size")
    ap.add_argument("--tau", type=float, default=0.1, help="C1 lifespan threshold")
    ap.add_argument("--no-gudhi", action="store_true", help="Disable gudhi")
    args = ap.parse_args()

    W = make_synthetic_directed(n=args.n)
    constructions = [
        ("raw", construction_raw(W)),
        ("threshold_0.5", construction_threshold(W, 0.5)),
        ("symmetrized", construction_symmetrized(W)),
    ]

    out_dir = args.out_dir
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out_dir = ROOT / "outputs" / "runs" / ts
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# RCTI Comparative Pipeline (PRD-21) — Empirical Test Family E",
        f"# n={args.n}, tau={args.tau}, use_gudhi={not args.no_gudhi}",
        "",
    ]

    for name, W_c in constructions:
        res = run_pipeline(W_c, threshold=None, max_dim=4, tau=args.tau, use_gudhi=not args.no_gudhi)
        baselines = compute_all_baselines(W_c)
        lines.append(f"## Construction: {name}")
        lines.append(f"  C1: {res['C1']['message']}")
        lines.append(f"  C4b: {res['C4b']['message']}")
        lines.append(f"  Persistence entropy: {res['persistence_entropy']:.6f}")
        lines.append(f"  n_simplices: {res['n_simplices']}")
        if res.get("C2F") is not None:
            lines.append(f"  C2F: {res['C2F']:.4f}")
        lines.append("  Baselines: " + ", ".join(f"{k}={baselines[k]:.4f}" for k in sorted(baselines.keys())))
        lines.append("")

    lines.append("## Summary")
    lines.append("Topology (C1, C4b, PE) and graph baselines (density, clustering, reciprocity, modularity, spectral_gap, entropy_degrees) computed per construction. For discrimination vs condition labels, run with labeled data and compare AUC; this run reports values only.")
    report_path = out_dir / "rcti_comparative_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
