#!/usr/bin/env python3
"""
Build a remote-compute payload (JSON) for Claude API.

Loads a small kernel from dataset NPZ, runs minimal local steps to obtain
q_star and a few rival partitions, then writes payload.json (and optional
prompt snippet) for use by run_remote_compute_claude.py.

Use when local full runs are infeasible; payload size is kept small for
context limits (e.g. max_nodes 30–50, n_bootstrap 50, n_perm 50).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np

from boundary_org.baselines import louvain_partition, spectral_partition
from boundary_org.projection import identity_partition, single_block_partition


def _row_stochastic(K: np.ndarray) -> np.ndarray:
    K = np.asarray(K, dtype=np.float64)
    row_sums = K.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return K / row_sums


def _load_kernel(npz_path: Path, max_nodes: int) -> tuple:
    data = np.load(npz_path, allow_pickle=False)
    K = np.asarray(data["K"], dtype=np.float64)
    labels = np.asarray(data["labels"], dtype=np.int64) if "labels" in data else np.full(K.shape[0], -1, dtype=np.int64)
    if "mu" in data:
        mu = np.asarray(data["mu"], dtype=np.float64)
        mu = np.where(mu > 0, mu, 0.0)
        mu = mu / np.sum(mu) if np.sum(mu) > 0 else np.ones(K.shape[0], dtype=np.float64) / K.shape[0]
    else:
        mu = np.ones(K.shape[0], dtype=np.float64) / K.shape[0]
    n0 = int(K.shape[0])
    if max_nodes > 0 and max_nodes < n0:
        degree = np.asarray(K).sum(axis=1)
        keep = np.argsort(-degree)[:max_nodes]
        keep = np.sort(keep)
        K = K[np.ix_(keep, keep)]
        labels = labels[keep]
        mu = mu[keep]
        mu = mu / np.sum(mu)
    K = _row_stochastic(K)
    return K, mu, labels, int(K.shape[0])


def _partition_to_list_of_lists(partition: List[List[int]]) -> List[List[int]]:
    return [list(bl) for bl in partition]


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare remote-compute payload for Claude API.")
    ap.add_argument("--dataset-npz", type=Path, default=ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "remote_compute_payloads")
    ap.add_argument("--max-nodes", type=int, default=40, help="Keep small for context (e.g. 30–50).")
    ap.add_argument("--n-bootstrap", type=int, default=50)
    ap.add_argument("--n-perm", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--task", type=str, default="combined", choices=["bootstrap_null_dominance", "permutation_external_pvals", "combined"])
    args = ap.parse_args()

    npz_path = args.dataset_npz.resolve()
    if not npz_path.exists():
        print(f"Dataset not found: {npz_path}", file=sys.stderr)
        return 1

    K, mu, labels, n = _load_kernel(npz_path, args.max_nodes)
    labels_list = labels.tolist()

    # q_star: use spectral as a tractable boundary proxy (no full framework search to keep local compute minimal)
    q_star = spectral_partition(K)
    q_star = _partition_to_list_of_lists(q_star)

    rival_partitions: Dict[str, List[List[int]]] = {}
    rival_partitions["one_block"] = _partition_to_list_of_lists(single_block_partition(n))
    rival_partitions["singleton"] = _partition_to_list_of_lists(identity_partition(n))
    rival_partitions["spectral"] = q_star  # same as q_star here; for diversity we could use a different baseline
    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        rival_partitions["louvain"] = _partition_to_list_of_lists(q_louvain)

    payload: Dict[str, Any] = {
        "payload_version": "1.0",
        "task": args.task,
        "n": n,
        "labels": labels_list,
        "q_star": q_star,
        "rival_partitions": rival_partitions,
        "n_bootstrap": args.n_bootstrap,
        "n_perm": args.n_perm,
        "seed": args.seed,
    }

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "payload.json"
    with out_path.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
