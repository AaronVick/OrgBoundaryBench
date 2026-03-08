#!/usr/bin/env python3
"""
Build temporal window kernels from public SNAP temporal edge lists.

Sources:
- email-Eu-core-temporal: https://snap.stanford.edu/data/email-Eu-core-temporal.txt.gz
- wiki-talk-temporal: https://snap.stanford.edu/data/wiki-talk-temporal.txt.gz

Output:
- data/processed/<source>/window_XX.npz (K, mu, n_edges, t_start, t_end)
- data/processed/<source>/manifest.json
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

SOURCES: Dict[str, Dict[str, str]] = {
    "email_eu_core_temporal": {
        "url": "https://snap.stanford.edu/data/email-Eu-core-temporal.txt.gz",
        "filename": "email-Eu-core-temporal.txt.gz",
    },
    "wiki_talk_temporal": {
        "url": "https://snap.stanford.edu/data/wiki-talk-temporal.txt.gz",
        "filename": "wiki-talk-temporal.txt.gz",
    },
}


def _download_if_needed(source: str) -> Path:
    cfg = SOURCES[source]
    raw_dir = DATA_RAW / source
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / cfg["filename"]
    if not out_path.exists():
        print(f"Downloading {cfg['url']} -> {out_path}")
        try:
            urllib.request.urlretrieve(cfg["url"], out_path)
        except Exception:
            # Fallback: some environments fail DNS via urllib but allow curl.
            r = subprocess.run(
                ["curl", "-s", "-L", "-o", str(out_path), cfg["url"]],
                check=False,
                capture_output=True,
                text=True,
            )
            if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
                raise RuntimeError(
                    f"Download failed for {cfg['url']} via urllib and curl (rc={r.returncode})."
                )
    else:
        print(f"Already exists: {out_path}")
    return out_path


def _iter_temporal_edges(path: Path) -> Iterable[Tuple[int, int, int]]:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                u = int(parts[0])
                v = int(parts[1])
                t = int(parts[2])
            except ValueError:
                continue
            if u == v:
                continue
            yield (u, v, t)


def _row_stochastic(M: np.ndarray) -> np.ndarray:
    M = np.asarray(M, dtype=np.float64)
    row_sum = M.sum(axis=1, keepdims=True)
    row_sum = np.where(row_sum > 0, row_sum, 1.0)
    return M / row_sum


def _stationary_distribution(K: np.ndarray, n_iter: int = 400) -> np.ndarray:
    n = K.shape[0]
    mu = np.ones(n, dtype=np.float64) / max(1, n)
    for _ in range(n_iter):
        mu = mu @ K
    mu = np.maximum(mu, 1e-12)
    mu = mu / np.sum(mu)
    return mu


def build_windows(
    source: str,
    *,
    max_nodes: int,
    n_windows: int,
    max_edges: int,
) -> Dict[str, object]:
    gz_path = _download_if_needed(source)
    with open(gz_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    print("Parsing temporal edges...")
    edges: List[Tuple[int, int, int]] = []
    degree: Dict[int, int] = {}
    for i, (u, v, t) in enumerate(_iter_temporal_edges(gz_path), start=1):
        edges.append((u, v, t))
        degree[u] = degree.get(u, 0) + 1
        degree[v] = degree.get(v, 0) + 1
        if max_edges > 0 and i >= max_edges:
            break

    if not edges:
        raise RuntimeError(f"No temporal edges parsed from {gz_path}")

    nodes_sorted = sorted(degree.items(), key=lambda kv: (-kv[1], kv[0]))
    if max_nodes > 0:
        keep_nodes = {node for node, _d in nodes_sorted[:max_nodes]}
    else:
        keep_nodes = {node for node, _d in nodes_sorted}

    filtered = [(u, v, t) for (u, v, t) in edges if u in keep_nodes and v in keep_nodes]
    if not filtered:
        raise RuntimeError("No edges remain after node filtering")

    node_list = sorted(keep_nodes)
    node_to_idx = {node: i for i, node in enumerate(node_list)}

    filtered.sort(key=lambda x: x[2])
    idx_chunks = np.array_split(np.arange(len(filtered)), n_windows)

    out_dir = DATA_PROCESSED / source
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    for w_idx, chunk in enumerate(idx_chunks):
        if chunk.size == 0:
            continue
        A = np.zeros((len(node_list), len(node_list)), dtype=np.float64)
        t0 = int(filtered[int(chunk[0])][2])
        t1 = int(filtered[int(chunk[-1])][2])
        for j in chunk.tolist():
            u, v, _t = filtered[j]
            A[node_to_idx[u], node_to_idx[v]] += 1.0
        if np.count_nonzero(A) == 0:
            continue
        K = _row_stochastic(A)
        mu = _stationary_distribution(K)
        out = out_dir / f"window_{w_idx:02d}.npz"
        np.savez_compressed(
            out,
            K=K,
            mu=mu,
            n_edges=int(chunk.size),
            t_start=t0,
            t_end=t1,
            n_nodes=int(len(node_list)),
        )
        saved += 1

    manifest = {
        "source": source,
        "raw_path": str(gz_path.resolve()),
        "file_hash_sha256": file_hash,
        "max_nodes": max_nodes,
        "max_edges": max_edges,
        "n_windows_requested": n_windows,
        "n_windows_saved": saved,
        "n_edges_loaded": len(edges),
        "n_edges_filtered": len(filtered),
        "n_nodes": len(node_list),
        "windowing": "equal-count temporal chunks after timestamp sort",
        "kernel_recipe": "directed edge-count adjacency per window; row-normalized K; mu via power iteration",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="Build temporal window kernels from public temporal edge lists.")
    ap.add_argument("--source", choices=sorted(SOURCES.keys()), required=True)
    ap.add_argument("--max-nodes", type=int, default=120)
    ap.add_argument("--n-windows", type=int, default=8)
    ap.add_argument("--max-edges", type=int, default=0, help="0 = no cap")
    args = ap.parse_args()

    build_windows(
        args.source,
        max_nodes=args.max_nodes,
        n_windows=args.n_windows,
        max_edges=args.max_edges,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
