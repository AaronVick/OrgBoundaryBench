#!/usr/bin/env python3
"""
PRD-33: Objective-ablation study (primary result).

Evaluates partitions under multiple objective definitions: E_cl only, E_cl + size penalty (cost),
and modularity Q. Reports whether any variant yields a balanced, gate-relevant partition.
Publishable regardless of main claim status. Traceability: PRD-33, PRD-17 (harness), PRD-02.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.baselines import louvain_partition
from boundary_org.greedy import greedy_coarse_graining
from boundary_org.harness import score_J
from boundary_org.labeled_harness import external_agreement
from boundary_org.projection import identity_partition, single_block_partition


def block_balance(partition: list) -> float:
    """Normalized entropy of block sizes in [0,1]. Higher = more balanced."""
    k = len(partition)
    if k <= 1:
        return 0.0
    n = sum(len(b) for b in partition)
    sizes = np.array([len(b) for b in partition], dtype=np.float64)
    p = sizes / np.sum(sizes)
    ent = -float(np.sum(p * np.log(p + 1e-20)))
    return ent / np.log(k) if np.log(k) > 0 else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-33: Objective-ablation study (E_cl, E_cl+cost, Q).")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--dataset-npz", type=Path, default=None, help="Optional kernel.npz; else synthetic.")
    ap.add_argument("--n", type=int, default=30, help="Synthetic n when no dataset.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    if args.dataset_npz and args.dataset_npz.resolve().exists():
        data = np.load(args.dataset_npz, allow_pickle=False)
        K = np.asarray(data["K"], dtype=np.float64)
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.asarray(data["mu"], dtype=np.float64)
        mu = mu / np.sum(mu)
        labels = np.asarray(data["labels"], dtype=np.int64) if "labels" in data else None
        data_src = str(args.dataset_npz)
    else:
        n = args.n
        K = rng.uniform(0.1, 1.0, (n, n))
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(n) / n
        labels = rng.integers(0, 4, size=n)
        data_src = f"synthetic n={n} seed={args.seed}"

    n = K.shape[0]
    if labels is not None and np.all(labels < 0):
        labels = None

    # Partitions: greedy (E_cl only), Louvain (Q-driven), one-block, singleton
    q_greedy, _, _ = greedy_coarse_graining(K, mu)
    q_louvain = louvain_partition(K)
    if q_louvain is None:
        q_louvain = identity_partition(n)
    q_one = single_block_partition(n)
    q_singleton = identity_partition(n)

    variants = [
        ("q_star_greedy", q_greedy, "E_cl only (greedy)"),
        ("Louvain", q_louvain, "Q-driven"),
        ("one_block", q_one, "trivial"),
        ("singleton", q_singleton, "trivial"),
    ]

    rows = []
    for name, q, desc in variants:
        E_cl, cost, J_ecl_eta, Q = score_J(K, mu, q, alpha=1.0, eta=0.0)
        _, _, J_with_cost, _ = score_J(K, mu, q, alpha=1.0, eta=0.5)
        balance = block_balance(q)
        nmi_val = None
        if labels is not None:
            ag = external_agreement(q, labels, n)
            nmi_val = ag.get("nmi")
        non_trivial = 2 <= len(q) <= max(2, int(0.8 * n))
        gate_relevant = non_trivial and balance >= 0.05
        rows.append({
            "variant": name,
            "description": desc,
            "n_blocks": len(q),
            "block_balance": round(balance, 6),
            "E_cl": round(E_cl, 6),
            "J_Ecl_only": round(J_ecl_eta, 6),
            "J_Ecl_plus_cost": round(J_with_cost, 6),
            "Q": round(Q, 6),
            "nmi": round(nmi_val, 6) if nmi_val is not None else "",
            "non_trivial": non_trivial,
            "gate_relevant": gate_relevant,
        })

    out_dir = args.out_dir or (ROOT / "outputs" / "objective_ablation" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # CSV
    fieldnames = ["variant", "description", "n_blocks", "block_balance", "E_cl", "J_Ecl_only", "J_Ecl_plus_cost", "Q", "nmi", "non_trivial", "gate_relevant"]
    with (out_dir / "ablation_report.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})

    # run_report.md
    any_gate = any(r["gate_relevant"] for r in rows)
    run_report = [
        "# Run report: PRD-33 objective-ablation study",
        "",
        f"**Run:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}  ",
        "**Framework:** BPO (PRD-33).",
        "",
        "---",
        "",
        "## 1. Hypothesis",
        "",
        "Current failures may stem from objective geometry (single scalar, weighting) rather than the concept (closure/boundary). Ablation evaluates partitions under E_cl only, E_cl + size penalty (cost), and Q.",
        "",
        "## 2. Method",
        "",
        "Partitions: q* from greedy (min E_cl), Louvain (Q-driven), one-block, singleton. For each we report n_blocks, block_balance, E_cl, J(E_cl only), J(E_cl+cost), Q, and NMI when labels exist. Gate-relevant: non-trivial (2 ≤ k ≤ 0.8n) and balance ≥ 0.05.",
        "",
        "## 3. Data",
        "",
        data_src,
        "",
        "## 4. Results (ablation_report.csv)",
        "",
        "| variant | n_blocks | balance | E_cl | J_Ecl_only | J_Ecl+cost | Q | gate_relevant |",
        "|---------|----------|---------|------|------------|------------|---|---------------|",
    ]
    for r in rows:
        run_report.append(
            f"| {r['variant']} | {r['n_blocks']} | {r['block_balance']:.4f} | {r['E_cl']:.4f} | {r['J_Ecl_only']:.4f} | {r['J_Ecl_plus_cost']:.4f} | {r['Q']:.4f} | {r['gate_relevant']} |"
        )
    run_report.extend([
        "",
        "## 5. Falsification",
        "",
        "If no variant is gate_relevant, ablation supports objective mis-specification (publishable). If at least one is gate_relevant, that variant is candidate for PRD-31 full audit.",
        "",
        f"**Any variant gate_relevant:** {any_gate}",
        "",
        "---",
        "",
        "*Traceability: PRD-33, PRD-17, PRD-02, outputs/METHODOLOGY.md.*",
    ])
    (out_dir / "run_report.md").write_text("\n".join(run_report))
    print(f"Wrote {out_dir / 'ablation_report.csv'}, {out_dir / 'run_report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
