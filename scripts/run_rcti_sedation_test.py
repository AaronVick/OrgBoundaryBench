#!/usr/bin/env python3
"""
PRD-27: RCTI Real Sedation Test — condition-contrast discrimination.

Runs two+ constructions on labeled samples (synthetic or --data); computes AUC for topology
vs six baselines. Pass iff topology beats or matches baselines. Falsification: topology fails.
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

from relational_closure.sedation_discrimination import run_discrimination_multi_construction


def make_synthetic_directed(n: int, seed: int) -> np.ndarray:
    """Directed graph: cycle plus noise."""
    rng = np.random.default_rng(seed)
    W = np.zeros((n, n))
    for i in range(n):
        W[i, (i + 1) % n] = 1.0
    for i in range(n):
        for j in range(n):
            if i != j and (i + 1) % n != j and rng.random() < 0.2:
                W[i, j] = rng.uniform(0.3, 1.0)
    return W


def make_synthetic_dense_random(n: int, density: float, seed: int) -> np.ndarray:
    """Dense random directed graph (different structure from cycle)."""
    rng = np.random.default_rng(seed)
    W = rng.uniform(0, 1, (n, n))
    W *= (rng.random((n, n)) < density).astype(float)
    return W


def construction_raw(W: np.ndarray) -> np.ndarray:
    return np.asarray(W, dtype=float)


def construction_threshold(W: np.ndarray, quantile: float = 0.5) -> np.ndarray:
    W = np.asarray(W, dtype=float)
    vals = W[W > 0]
    if vals.size == 0:
        return W
    thresh = float(np.quantile(vals, quantile))
    return np.where(W >= thresh, W, 0.0)


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-27: RCTI Real Sedation Test — topology vs baselines AUC.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory")
    ap.add_argument("--n", type=int, default=6, help="Graph size per sample")
    ap.add_argument("--n-per-class", type=int, default=4, help="Samples per condition (synthetic)")
    ap.add_argument("--tau", type=float, default=0.1, help="C1 lifespan threshold")
    ap.add_argument("--no-gudhi", action="store_true", help="Disable gudhi")
    args = ap.parse_args()

    # Synthetic condition contrast: class 0 = cycle-like, class 1 = dense random (matched density optional)
    rng = np.random.default_rng(42)
    samples: list = []
    for _ in range(args.n_per_class):
        W0 = make_synthetic_directed(args.n, rng.integers(0, 10000))
        samples.append((W0, 0))
    for _ in range(args.n_per_class):
        W1 = make_synthetic_dense_random(args.n, 0.25, rng.integers(0, 10000))
        samples.append((W1, 1))

    construction_fns = [
        ("raw", lambda W: construction_raw(W)),
        ("threshold_0.5", lambda W: construction_threshold(W, 0.5)),
    ]
    results, pass_ = run_discrimination_multi_construction(
        samples, construction_fns, tau=args.tau, use_gudhi=not args.no_gudhi
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# PRD-27: RCTI Real Sedation Test — condition-contrast discrimination",
        f"# n={args.n}, n_per_class={args.n_per_class}, tau={args.tau}, use_gudhi={not args.no_gudhi}",
        "",
        "## Per-construction AUC (topology vs baselines)",
        "",
    ]
    for res in results:
        lines.append(f"### Construction: {res['construction']}")
        lines.append(f"  AUC (topology/PE): {res['auc_topology']:.4f}")
        lines.append("  AUC (baselines): " + ", ".join(f"{k}={res['auc_baselines'][k]:.4f}" for k in sorted(res["auc_baselines"])))
        lines.append("")
    lines.extend([
        f"## Pass (topology beats or matches baselines for at least one construction): {pass_}",
        "## Falsification: If topology does not beat or match baselines, run fails (PRD-27 §4).",
        "",
    ])
    report_path = out_dir / "rcti_sedation_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
