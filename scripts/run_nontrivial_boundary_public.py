#!/usr/bin/env python3
"""
PRD-23: Nontrivial Boundary on Public Labeled Graphs.

Loads kernel + labels (email-Eu-core or synthetic), runs labeled harness (J(q) + NMI/ARI/macro-F1 vs labels),
writes nontrivial_boundary_report.txt with leaderboard, external agreement table, and meaningful vs useless statement.
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

from boundary_org.labeled_harness import run_nontrivial_boundary_labeled


def load_labeled_kernel(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Load K, mu, labels from kernel.npz (PRD-23: email-Eu-core format). Returns (K, mu, labels, info)."""
    npz_path = processed_dir / "kernel.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Missing {npz_path}. Run: python scripts/download_and_normalize.py --source email_eu_core")
    data = np.load(npz_path, allow_pickle=False)
    K = np.asarray(data["K"])
    mu = np.asarray(data["mu"])
    labels = np.asarray(data["labels"], dtype=np.int32) if "labels" in data else np.full(K.shape[0], 0, dtype=np.int32)
    info = {"n": int(K.shape[0]), "source": "email_eu_core"}
    return K, mu, labels, info


def make_synthetic_labeled(n: int = 12, n_classes: int = 3, seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic (K, mu) and random labels for testing PRD-23 without download."""
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, (n, n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(n) / n
    labels = rng.integers(0, n_classes, size=n)
    return K, mu, labels


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-23: Nontrivial Boundary on Public Labeled Graphs — J(q), baselines, external agreement.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: outputs/runs/<ISO timestamp>)")
    ap.add_argument("--data", type=Path, default=None, help="Processed dir with kernel.npz containing K, mu, labels (e.g. data/processed/email_eu_core)")
    ap.add_argument("--n", type=int, default=12, help="Synthetic n (used only if --data not set)")
    ap.add_argument("--n-classes", type=int, default=3, help="Synthetic label classes (only if --data not set)")
    ap.add_argument("--alpha", type=float, default=1.0, help="J = alpha*E_cl + eta*cost")
    ap.add_argument("--eta", type=float, default=0.5, help="Cost weight")
    ap.add_argument("--n-random", type=int, default=3, help="Number of random matched baselines")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = ap.parse_args()

    if args.data is not None:
        data_path = Path(args.data)
        K, mu, labels, info = load_labeled_kernel(data_path)
        source = info.get("source", "file")
    else:
        K, mu, labels = make_synthetic_labeled(n=args.n, n_classes=args.n_classes, seed=args.seed)
        source = "synthetic"
    n = K.shape[0]

    out_dir = args.out_dir
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out_dir = ROOT / "outputs" / "runs" / ts
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    leaderboard, q_star, success, meaningful = run_nontrivial_boundary_labeled(
        K, mu, labels,
        alpha=args.alpha,
        eta=args.eta,
        n_random=args.n_random,
        rng=rng,
    )

    lines = [
        "# PRD-23: Nontrivial Boundary on Public Labeled Graphs",
        f"# Source: {source}, n={n}",
        f"# J(q) = alpha*E_cl + eta*Cost(q); alpha={args.alpha}, eta={args.eta}",
        "",
        "## Leaderboard (lower J better)",
        "",
    ]
    for i, row in enumerate(leaderboard, 1):
        ag = row.get("agreement", {})
        lines.append(
            f"{i}. {row['name']}: n_blocks={row['n_blocks']}, E_cl={row['E_cl']:.6f}, cost={row['cost']:.6f}, J={row['J']:.6f}, Q={row['Q']:.6f}"
        )
    lines.extend([
        "",
        "## External agreement (vs ground-truth labels)",
        "",
        "| Candidate | NMI | ARI | macro_F1 |",
        "|-----------|-----|-----|----------|",
    ])
    for row in leaderboard:
        ag = row.get("agreement", {})
        nmi = ag.get("nmi", 0)
        ari = ag.get("ari", 0)
        f1 = ag.get("macro_f1", 0)
        lines.append(f"| {row['name']} | {nmi:.4f} | {ari:.4f} | {f1:.4f} |")
    lines.extend([
        "",
        f"## Success (harness): {success}",
        f"## Meaningful boundary (nontrivial and agreement no worse than best baseline): {meaningful}",
        f"## q* n_blocks: {len(q_star)}",
        "",
    ])
    if meaningful:
        lines.append("## Statement: Meaningful organizational boundary (nontrivial q* and external agreement at least as good as baselines).")
    else:
        lines.append("## Statement: Useless collapse or below-baseline agreement (q* trivial or external agreement worse than best baseline).")
    lines.append("")

    report_path = out_dir / "nontrivial_boundary_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if (success and meaningful) else 1


if __name__ == "__main__":
    sys.exit(main())
