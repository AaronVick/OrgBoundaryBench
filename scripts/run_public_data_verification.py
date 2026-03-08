#!/usr/bin/env python3
"""
Domain 6.4 (Enron SNAP) verification: q* vs Louvain [6]. PRD-05 Test D, PRD-06.

Loads kernel from data/processed/enron_snap/ (run scripts/download_and_normalize.py first).
Computes: greedy q*, E_cl(q*), Q(q*); Louvain partition (if available), E_cl(Louvain), Q(Louvain).
Writes public_data_report.txt and optional path for run dir.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.operators import closure_energy
from boundary_org.greedy import greedy_coarse_graining
from boundary_org.baselines import graph_modularity_q, louvain_partition

# Cap greedy steps for large graphs so Test D finishes in reasonable time (PRD-05).
MAX_BLOCKS_FOR_LARGE = 20  # stop when this many blocks remain
LARGE_GRAPH_N = 80


def load_enron_kernel(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Load K, mu from kernel.npz; read manifest if present. Returns (K, mu, info)."""
    npz_path = processed_dir / "kernel.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Run scripts/download_and_normalize.py first. Missing {npz_path}")
    data = np.load(npz_path)
    K = data["K"]
    mu = data["mu"]
    info = {"n": int(data.get("n", K.shape[0])), "n_full": int(data.get("n_full", 0)), "n_lcc": int(data.get("n_lcc", 0))}
    return K, mu, info


def run_verification(processed_dir: Path, out_path: Path | None) -> str:
    """Run Test D metrics; return report text. If out_path, write file."""
    K, mu, info = load_enron_kernel(processed_dir)
    n = K.shape[0]
    lines = [
        "# Domain 6.4 (Enron SNAP) — Test D verification",
        f"# n_used={info['n']}, n_lcc={info.get('n_lcc', 'N/A')}, n_full={info.get('n_full', 'N/A')}",
        "",
    ]
    # Greedy q* (cap steps for n > LARGE_GRAPH_N for feasibility)
    if n > LARGE_GRAPH_N:
        max_steps = n - MAX_BLOCKS_FOR_LARGE
        q_star, _, _ = greedy_coarse_graining(K, mu, max_steps=max_steps)
        lines.append(f"# Greedy capped at {MAX_BLOCKS_FOR_LARGE} blocks (n={n} > {LARGE_GRAPH_N})")
    else:
        q_star, _, _ = greedy_coarse_graining(K, mu)
    E_cl_star = float(closure_energy(K, mu, q_star))
    Q_star = float(graph_modularity_q(K, q_star))
    lines.append(f"q* (greedy T3.4): |q*|={len(q_star)} blocks, E_cl(q*)= {E_cl_star:.6f}, Q(q*)= {Q_star:.6f}")
    lines.append("")
    # Louvain
    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        E_cl_louvain = float(closure_energy(K, mu, q_louvain))
        Q_louvain = float(graph_modularity_q(K, q_louvain))
        lines.append(f"Louvain [6]: |q|= {len(q_louvain)} communities, E_cl(q)= {E_cl_louvain:.6f}, Q(q)= {Q_louvain:.6f}")
        # Comparison: framework no worse than Louvain (PRD-06) — for Test D we compare vs org; without org we report both
        lines.append("# Baseline comparison (no org-chart): both E_cl and Q reported; Test D full requires q_org.")
    else:
        lines.append("# Louvain: not available (install networkx for baseline comparison).")
    lines.append("")
    report = "\n".join(lines)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(report)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Domain 6.4 verification (Enron SNAP): q* vs Louvain.")
    ap.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed" / "enron_snap", help="Path to processed Enron kernel")
    ap.add_argument("--out", type=Path, default=None, help="Write report to this path (default: print only)")
    args = ap.parse_args()
    try:
        report = run_verification(args.processed_dir, args.out)
        print(report)
        if args.out:
            print(f"Wrote {args.out}")
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
