#!/usr/bin/env python3
"""
Deliverable 2 (organizational_empirical_validation.md): Enron time-windowed persistent homology
with CF_t (C2F_t) and multiple S' definitions.

Loads Enron edges, splits into T time windows (by edge order if no timestamps), builds W_t per
window, runs RCTI pipeline (barcode, HC_t, C2F_t) for at least two S' definitions, computes
classical baselines per window, writes report. Satisfies 4.4.2, 4.4.3, 4.4.4 and A8.2–A8.4.
Event-linked analysis: deferred when no timestamps (documented in report).
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from relational_closure.pipeline import run_pipeline

DATA_RAW = ROOT / "data" / "raw" / "enron_snap"
ENRON_URL = "https://snap.stanford.edu/data/email-Enron.txt.gz"
CANONICAL_OUT_DIR = ROOT / "outputs" / "runs" / "enron_timewindowed"


def load_enron_edges(raw_dir: Path) -> Tuple[List[Tuple[int, int]], int, List[int], Dict[int, int]]:
    """Load edge list from email-Enron.txt.gz. Returns (edges, n, nodes, node2idx)."""
    gz_path = raw_dir / "email-Enron.txt.gz"
    if not gz_path.exists():
        raise FileNotFoundError(f"Missing {gz_path}. Run: python3 scripts/download_and_normalize.py --source enron_snap (downloads to raw).")
    node_set = set()
    edges_raw = []
    with gzip.open(gz_path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            u, v = int(parts[0]), int(parts[1])
            if u == v:
                continue
            node_set.add(u)
            node_set.add(v)
            edges_raw.append((u, v))
    nodes = sorted(node_set)
    node2idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    # Convert to 0-indexed
    edges = [(node2idx[u], node2idx[v]) for u, v in edges_raw]
    return edges, n, nodes, node2idx


def edges_to_windows(
    edges: List[Tuple[int, int]],
    n_windows: int,
    rng: np.random.Generator,
    shuffle: bool = False,
) -> List[List[Tuple[int, int]]]:
    """Split edges into n_windows consecutive (or shuffled) bands. Returns list of edge lists."""
    if shuffle:
        idx = rng.permutation(len(edges))
        edges = [edges[i] for i in idx]
    T = n_windows
    size = len(edges)
    per = max(1, size // T)
    windows: List[List[Tuple[int, int]]] = []
    for t in range(T):
        start = t * per
        end = (t + 1) * per if t < T - 1 else size
        windows.append(edges[start:end])
    return windows


def build_W_from_edges(edges: List[Tuple[int, int]], n: int, directed: bool = True) -> np.ndarray:
    """Build n x n weight matrix from edge list. If directed, (i,j) and (j,i) both get +1."""
    W = np.zeros((n, n))
    for i, j in edges:
        if 0 <= i < n and 0 <= j < n:
            W[i, j] += 1.0
            if directed:
                W[j, i] += 1.0
    return W


def restrict_to_top_nodes(
    W_list: List[np.ndarray],
    top_n: int,
) -> Tuple[List[np.ndarray], np.ndarray]:
    """Restrict each W_t to top top_n nodes by total degree (sum over all windows). Returns (W_list_restricted, node_idx)."""
    if not W_list:
        return [], np.array([], dtype=np.int64)
    total_deg = np.zeros(W_list[0].shape[0])
    for W in W_list:
        total_deg += W.sum(axis=0) + W.sum(axis=1)
    order = np.argsort(-total_deg)[:top_n]
    out = [W[np.ix_(order, order)].copy() for W in W_list]
    return out, order


def s_prime_top_degree(W: np.ndarray, frac: float = 0.1) -> List[int]:
    """S' = top frac by degree (out+in). Returns list of vertex indices."""
    deg = W.sum(axis=0) + W.sum(axis=1)
    k = max(1, int(W.shape[0] * frac))
    return list(np.argsort(-deg)[:k])


def s_prime_random(n: int, frac: float, rng: np.random.Generator) -> List[int]:
    """S' = random frac of nodes."""
    k = max(1, int(n * frac))
    return list(rng.choice(n, size=k, replace=False))


def classical_baselines(W: np.ndarray) -> Dict[str, float]:
    """Density and mean degree (undirected interpretation: 2*edges/n)."""
    n = W.shape[0]
    edges = (W > 0).sum() // 2 if np.allclose(W, W.T) else (W > 0).sum()
    total_edges = (W > 0).sum() // 2
    density = (2 * total_edges) / (n * (n - 1)) if n > 1 else 0.0
    mean_degree = (2 * total_edges) / n if n > 0 else 0.0
    return {"density": float(density), "mean_degree": float(mean_degree), "n_edges": int(total_edges), "n": n}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Deliverable 2: Enron time-windowed CF_t pipeline.")
    ap.add_argument("--out-dir", type=Path, default=CANONICAL_OUT_DIR)
    ap.add_argument("--n-windows", type=int, default=3, help="Number of time windows (edge bands)")
    ap.add_argument("--max-nodes", type=int, default=35, help="Max nodes per window (for feasible persistence)")
    ap.add_argument("--shuffle-edges", action="store_true", help="Shuffle edges before splitting (synthetic randomness)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    edges, n_full, nodes, node2idx = load_enron_edges(DATA_RAW)
    windows = edges_to_windows(edges, args.n_windows, rng, shuffle=args.shuffle_edges)

    # Build W_t for each window (full size first)
    W_list = [build_W_from_edges(w, n_full) for w in windows]
    W_list, node_idx = restrict_to_top_nodes(W_list, args.max_nodes)
    n = len(node_idx)
    if n < 2:
        print("Too few nodes after restriction.", file=sys.stderr)
        return 1

    results: List[Dict[str, Any]] = []
    S_prime_defs = [
        ("top_degree_10pct", lambda W: s_prime_top_degree(W, 0.10)),
        ("random_10pct", lambda W: s_prime_random(n, 0.10, rng)),
    ]

    for t, W_t in enumerate(W_list):
        row = {"window": t, "HC_t": None, "C2F_t": {}, "baselines": {}}
        try:
            res = run_pipeline(W_t, threshold=None, max_dim=2, use_gudhi=True, node_sub=None)
            betti = res.get("betti", {})
            row["HC_t"] = sum(betti.get(k, 0) for k in betti)
        except Exception as e:
            row["HC_t"] = 0
            row["error"] = str(e)
        row["baselines"] = classical_baselines(W_t)

        for s_name, s_fn in S_prime_defs:
            try:
                node_sub = s_fn(W_t)
                res_s = run_pipeline(W_t, threshold=None, max_dim=2, use_gudhi=True, node_sub=node_sub)
                row["C2F_t"][s_name] = res_s.get("C2F")
            except Exception as e:
                row["C2F_t"][s_name] = None
        results.append(row)

    args.out_dir = Path(args.out_dir).resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.out_dir / "enron_timewindowed_report.txt"
    with open(report_path, "w") as f:
        f.write("# Enron time-windowed pipeline (Deliverable 2, organizational_empirical_validation.md)\n")
        f.write(f"# n_windows={args.n_windows}, max_nodes={args.max_nodes}, seed={args.seed}\n")
        f.write("# Event-linked analysis: DEFERRED (no timestamps in SNAP Enron edgelist)\n\n")
        f.write("window\tHC_t\tdensity\tmean_degree\tn_edges")
        for s_name in [x[0] for x in S_prime_defs]:
            f.write(f"\tC2F_t_{s_name}")
        f.write("\n")
        for r in results:
            bl = r.get("baselines", {})
            f.write(f"{r['window']}\t{r.get('HC_t', '')}\t{bl.get('density', '')}\t{bl.get('mean_degree', '')}\t{bl.get('n_edges', '')}")
            for s_name in [x[0] for x in S_prime_defs]:
                f.write(f"\t{r.get('C2F_t', {}).get(s_name, '')}")
            f.write("\n")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
