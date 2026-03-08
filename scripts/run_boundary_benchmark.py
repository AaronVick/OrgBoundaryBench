#!/usr/bin/env python3
"""
Boundary Benchmark Harness runner (PRD-17). Empirical Test Family A.

Loads kernel (synthetic or data/processed/enron_snap), runs harness, writes
boundary_benchmark_report.txt to outputs/runs/<run_id>/ (or --out-dir).
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

from boundary_org.harness import run_harness


def load_enron_kernel(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load K, mu from kernel.npz. Returns (K, mu, info)."""
    npz_path = processed_dir / "kernel.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Missing {npz_path}. Run scripts/download_and_normalize.py first.")
    data = np.load(npz_path)
    K = np.asarray(data["K"])
    mu = np.asarray(data["mu"])
    info = {"n": int(K.shape[0]), "source": "enron_snap"}
    return K, mu, info


def make_synthetic_kernel(n: int = 12, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic kernel for harness; uniform mu to avoid near-zero block mass in greedy (PRD-17)."""
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, (n, n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(n) / n
    return K, mu


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-17: Boundary Benchmark Harness — J(q), baselines, success.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: outputs/runs/<ISO timestamp>)")
    ap.add_argument("--data", type=Path, default=None, help="Processed data dir with kernel.npz (e.g. data/processed/enron_snap)")
    ap.add_argument("--n", type=int, default=12, help="Synthetic n (used only if --data not set)")
    ap.add_argument("--alpha", type=float, default=1.0, help="J = alpha*E_cl + eta*cost")
    ap.add_argument("--eta", type=float, default=0.5, help="Cost weight")
    ap.add_argument("--n-random", type=int, default=5, help="Number of random matched baselines")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = ap.parse_args()

    if args.data is not None:
        K, mu, info = load_enron_kernel(Path(args.data))
        source = info.get("source", "file")
    else:
        K, mu = make_synthetic_kernel(n=args.n, seed=args.seed)
        source = "synthetic"
        info = {"n": K.shape[0]}

    out_dir = args.out_dir
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out_dir = ROOT / "outputs" / "runs" / ts
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    leaderboard, q_star, success = run_harness(
        K, mu,
        alpha=args.alpha,
        eta=args.eta,
        n_random=args.n_random,
        rng=rng,
    )

    lines = [
        "# Boundary Benchmark Harness (PRD-17) — Empirical Test Family A",
        f"# Source: {source}, n={K.shape[0]}",
        f"# J(q) = alpha*E_cl + eta*Cost(q); alpha={args.alpha}, eta={args.eta}",
        "",
        "## Leaderboard (lower J better)",
        "",
    ]
    for i, row in enumerate(leaderboard, 1):
        lines.append(f"{i}. {row['name']}: n_blocks={row['n_blocks']}, E_cl={row['E_cl']:.6f}, cost={row['cost']:.6f}, J={row['J']:.6f}, Q={row['Q']:.6f}")
    lines.extend([
        "",
        f"## Success (non-trivial q* beats one_block, singleton, Louvain, random): {success}",
        f"## q* n_blocks: {len(q_star)}",
        "",
    ])
    report_path = out_dir / "boundary_benchmark_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
