#!/usr/bin/env python3
"""
PRD-01: Data pipeline — acquire, normalize, build kernel.

Enron SNAP (Domain 6.4): download email-Enron.txt.gz, build (S, K, μ) per PRD-01 §2.5.
Output: data/processed/enron_snap/kernel.npz + manifest.yaml.
Optional: --max-nodes N to restrict to largest-degree N nodes (LCC) for Test D feasibility.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

import numpy as np

# Repository root
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

ENRON_SNAP_URL = "https://snap.stanford.edu/data/email-Enron.txt.gz"
ENRON_SNAP_SOURCE_ID = "enron_snap"
DOMAIN = "6.4"

# PRD-23: email-Eu-core (labeled graph)
EMAIL_EUCORE_EDGES_URL = "https://snap.stanford.edu/data/email-Eu-core.txt.gz"
EMAIL_EUCORE_LABELS_URL = "https://snap.stanford.edu/data/email-Eu-core-department-labels.txt.gz"
EMAIL_EUCORE_SOURCE_ID = "email_eu_core"

# Apache (organizational replication): edgelist from data/raw/apache/ or optional URL
APACHE_SOURCE_ID = "apache"


def _stationary_distribution(K: np.ndarray, *, floor: float = 1e-12) -> np.ndarray:
    """Invariant measure μ: left eigenvector eigenvalue 1. Def 2.1. Floor so block masses valid for L2(μ)."""
    eigvals, eigvecs = np.linalg.eig(K.T)
    idx = np.argmin(np.abs(eigvals - 1.0))
    mu = np.real(eigvecs[:, idx]).ravel()
    mu = np.maximum(mu, floor)
    total = mu.sum()
    if total <= 0:
        mu = np.ones(K.shape[0]) / K.shape[0]
    else:
        mu = mu / total
    # Ensure every state has enough mass for projection_matrix (PRD-02 L2(μ))
    n = len(mu)
    mu = np.maximum(mu, 1e-10)
    mu = mu / mu.sum()
    return mu.astype(np.float64)


def _normalize_rows(M: np.ndarray) -> np.ndarray:
    """Stochastic: each row sums to 1. Zero rows -> uniform."""
    row_sums = M.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return (M / row_sums).astype(np.float64)


def download_enron_snap(dest_dir: Path) -> Path:
    """Download email-Enron.txt.gz to dest_dir. Returns path to local file."""
    import urllib.request
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_path = dest_dir / "email-Enron.txt.gz"
    if out_path.exists():
        print(f"Already exists: {out_path}")
        return out_path
    print(f"Downloading {ENRON_SNAP_URL} -> {out_path}")
    urllib.request.urlretrieve(ENRON_SNAP_URL, out_path)
    return out_path


def parse_edgelist_plain(path: Path) -> tuple[list[tuple[int, int]], int, list[int], dict[int, int]]:
    """
    Parse plain or gzip edgelist: lines 'from to' (whitespace-separated). Returns (edges, n, nodes, node2idx).
    Same 4-tuple as parse_enron_edgelist for use with build_adjacency_lcc.
    """
    node_set = set()
    edges_raw = []
    open_fn = gzip.open if path.suffix == ".gz" or path.name.endswith(".gz") else open
    mode = "rt" if open_fn == gzip.open else "r"
    with open_fn(path, mode, encoding="utf-8", errors="replace") as f:
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
    edges = set()
    for u, v in edges_raw:
        i, j = node2idx[u], node2idx[v]
        if i > j:
            i, j = j, i
        edges.add((i, j))
    return list(edges), n, nodes, node2idx


def parse_enron_edgelist(path: Path) -> tuple[list[tuple[int, int]], int]:
    """
    Parse SNAP email-Enron format: lines "from\\tto" (node IDs). Build undirected edge set.
    Returns (edges as (i,j) with i<j), num_nodes (max node id + 1 or unique count).
    We use 0-indexed internal IDs; return edges as (u, v) with u, v in range(n).
    """
    node_set = set()
    edges_raw = []
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
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
    edges = set()
    for u, v in edges_raw:
        i, j = node2idx[u], node2idx[v]
        if i > j:
            i, j = j, i
        edges.add((i, j))
    return list(edges), n, nodes, node2idx


def parse_edgelist_plain(path: Path) -> tuple[list[tuple[int, int]], int, list[int], dict[int, int]]:
    """
    Parse plain or gzip edgelist: lines 'from to' (whitespace-separated). Returns (edges, n, nodes, node2idx).
    Use for Apache or other file-based org datasets.
    """
    node_set = set()
    edges_raw = []
    if path.suffix == ".gz" or path.name.endswith(".gz"):
        f = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    else:
        f = open(path, "r", encoding="utf-8", errors="replace")
    with f:
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
    edges = set()
    for u, v in edges_raw:
        i, j = node2idx[u], node2idx[v]
        if i > j:
            i, j = j, i
        edges.add((i, j))
    return list(edges), n, nodes, node2idx


def build_adjacency_lcc(edges: list[tuple[int, int]], n: int) -> tuple[np.ndarray, np.ndarray]:
    """Build symmetric adjacency A from edge list; restrict to largest connected component."""
    from collections import defaultdict
    neigh = defaultdict(set)
    for i, j in edges:
        neigh[i].add(j)
        neigh[j].add(i)
    # Largest connected component via BFS
    visited = np.zeros(n, dtype=bool)
    comp_sizes = []
    comp_labels = np.zeros(n, dtype=np.int32) - 1
    comp_id = 0
    for start in range(n):
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        comp_labels[start] = comp_id
        size = 1
        while stack:
            u = stack.pop()
            for v in neigh[u]:
                if not visited[v]:
                    visited[v] = True
                    comp_labels[v] = comp_id
                    stack.append(v)
                    size += 1
        comp_sizes.append((comp_id, size))
        comp_id += 1
    comp_sizes.sort(key=lambda x: -x[1])
    lcc_id = comp_sizes[0][0]
    lcc_nodes = np.where(comp_labels == lcc_id)[0]
    # Build A on LCC only
    lcc_set = set(lcc_nodes)
    A_lcc = np.zeros((len(lcc_nodes), len(lcc_nodes)), dtype=np.float64)
    for i, j in edges:
        if i in lcc_set and j in lcc_set:
            ii, jj = np.searchsorted(lcc_nodes, i), np.searchsorted(lcc_nodes, j)
            A_lcc[ii, jj] += 1
            A_lcc[jj, ii] += 1
    return A_lcc, lcc_nodes


def build_kernel_from_adjacency(A: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Row-normalize A -> K; compute μ = stationary distribution. PRD-01 §2.5."""
    K = _normalize_rows(A)
    mu = _stationary_distribution(K)
    return K, mu


def subgraph_by_degree(A: np.ndarray, max_nodes: int) -> np.ndarray:
    """Restrict to top max_nodes by degree sum (in+out). Returns A_sub, index array."""
    n = A.shape[0]
    if max_nodes >= n:
        return A, np.arange(n)
    deg = A.sum(axis=0) + A.sum(axis=1)
    top = np.argsort(-deg)[:max_nodes]
    return A[np.ix_(top, top)], top


def download_email_eu_core(dest_dir: Path) -> tuple[Path, Path]:
    """Download email-Eu-core edges and department labels. Returns (edges_path, labels_path)."""
    import urllib.request
    dest_dir.mkdir(parents=True, exist_ok=True)
    edges_path = dest_dir / "email-Eu-core.txt.gz"
    labels_path = dest_dir / "email-Eu-core-department-labels.txt.gz"
    for url, path in [(EMAIL_EUCORE_EDGES_URL, edges_path), (EMAIL_EUCORE_LABELS_URL, labels_path)]:
        if not path.exists():
            print(f"Downloading {url} -> {path}")
            urllib.request.urlretrieve(url, path)
        else:
            print(f"Already exists: {path}")
    return edges_path, labels_path


def parse_eu_core_edgelist(path: Path) -> tuple[list[tuple[int, int]], int, list[int], dict[int, int]]:
    """Parse SNAP email-Eu-core edges (same format as Enron). Returns (edges, n, nodes, node2idx)."""
    return parse_enron_edgelist(path)


def parse_eu_core_labels(path: Path) -> dict[int, int]:
    """Parse email-Eu-core-department-labels: NODEID DEPARTMENT (space/tab). Returns {original_node_id: department_id}."""
    label_by_orig_id: dict[int, int] = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            node_id, dept = int(parts[0]), int(parts[1])
            label_by_orig_id[node_id] = dept
    return label_by_orig_id


def run_email_eu_core(max_nodes: int | None, out_dir: Path) -> dict:
    """
    Download email-Eu-core, build (K, mu) and department labels. PRD-23 data source.
    Writes kernel.npz (K, mu, labels) and manifest.yaml. Labels aligned to rows of K.
    """
    raw_dir = DATA_RAW / EMAIL_EUCORE_SOURCE_ID
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    edges_path, labels_path = download_email_eu_core(raw_dir)
    with open(edges_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    edges, n_full, nodes, node2idx = parse_eu_core_edgelist(edges_path)
    label_by_orig_id = parse_eu_core_labels(labels_path)
    # Label per 0-indexed node (order of nodes = sorted original IDs)
    label_for_index = np.array([label_by_orig_id.get(nodes[i], -1) for i in range(n_full)], dtype=np.int32)

    A_lcc, lcc_nodes = build_adjacency_lcc(edges, n_full)
    n_lcc = A_lcc.shape[0]
    labels_lcc = label_for_index[lcc_nodes]

    if max_nodes is not None and max_nodes < n_lcc:
        A_sub, sub_idx = subgraph_by_degree(A_lcc, max_nodes)
        A_final = A_sub
        labels_final = labels_lcc[sub_idx]
        n_used = max_nodes
        note = f"Subgraph: top {max_nodes} nodes by degree (from LCC size {n_lcc})"
    else:
        A_final = A_lcc
        labels_final = labels_lcc
        n_used = n_lcc
        note = f"Full LCC: n={n_lcc} (original nodes {n_full})"

    K, mu = build_kernel_from_adjacency(A_final)
    n_labeled = int(np.sum(labels_final >= 0))
    np.savez(
        out_dir / "kernel.npz",
        K=K,
        mu=mu,
        labels=labels_final,
        n=n_used,
        n_full=n_full,
        n_lcc=n_lcc,
    )
    manifest = {
        "domain": DOMAIN,
        "source_id": EMAIL_EUCORE_SOURCE_ID,
        "edges_url": EMAIL_EUCORE_EDGES_URL,
        "labels_url": EMAIL_EUCORE_LABELS_URL,
        "citation": "Leskovec et al., Graph Evolution: Densification and Shrinking Diameters, ACM TKDD 2007; Yin et al., Local Higher-order Graph Clustering, KDD 2017.",
        "file_hash_sha256": file_hash,
        "pipeline_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_original": int(n_full),
        "n_lcc": int(n_lcc),
        "n_used": int(n_used),
        "n_labeled": int(n_labeled),
        "note": note,
        "kernel_recipe": "PRD-01 §2.5; PRD-23: row-normalized adjacency; μ stationary; labels = department (0..41).",
        "tests_enabled": ["PRD-23"],
    }
    manifest_path = out_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        f.write("# PRD-23 manifest: email-Eu-core (Domain 6.4, labeled)\n")
        for k, v in manifest.items():
            f.write(f"{k}: {repr(v)}\n")
    print(f"Wrote {out_dir / 'kernel.npz'} (with labels) and {manifest_path}")
    return manifest


def run_enron_snap(max_nodes: int | None, out_dir: Path) -> dict:
    """
    Download Enron SNAP, build (S, K, μ), optionally restrict to max_nodes.
    Writes kernel.npz and manifest.yaml. Returns manifest dict for caller.
    """
    raw_dir = DATA_RAW / ENRON_SNAP_SOURCE_ID
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    gz_path = download_enron_snap(raw_dir)
    with open(gz_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    edges, n_full, nodes, node2idx = parse_enron_edgelist(gz_path)
    A_lcc, lcc_nodes = build_adjacency_lcc(edges, n_full)
    n_lcc = A_lcc.shape[0]

    if max_nodes is not None and max_nodes < n_lcc:
        A_sub, sub_idx = subgraph_by_degree(A_lcc, max_nodes)
        A_final = A_sub
        n_used = max_nodes
        note = f"Subgraph: top {max_nodes} nodes by degree (from LCC size {n_lcc})"
    else:
        A_final = A_lcc
        n_used = n_lcc
        note = f"Full LCC: n={n_lcc} (original nodes {n_full})"

    K, mu = build_kernel_from_adjacency(A_final)
    np.savez(
        out_dir / "kernel.npz",
        K=K,
        mu=mu,
        n=n_used,
        n_full=n_full,
        n_lcc=n_lcc,
    )

    # Manifest
    manifest = {
        "domain": DOMAIN,
        "source_id": ENRON_SNAP_SOURCE_ID,
        "url": ENRON_SNAP_URL,
        "citation": "Leskovec et al., Community Structure in Large Networks, Internet Mathematics 6(1) 29-123, 2009; SNAP Stanford.",
        "file_hash_sha256": file_hash,
        "pipeline_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_original": int(n_full),
        "n_lcc": int(n_lcc),
        "n_used": int(n_used),
        "note": note,
        "kernel_recipe": "PRD-01 §2.5: row-normalized adjacency (undirected); μ = stationary distribution; LCC then optional degree-subgraph.",
        "tests_enabled": ["D"],
    }
    # Write manifest as simple YAML
    manifest_path = out_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        f.write("# PRD-01 manifest: Enron SNAP (Domain 6.4)\n")
        for k, v in manifest.items():
            f.write(f"{k}: {repr(v)}\n")
    print(f"Wrote {out_dir / 'kernel.npz'} and {manifest_path}")
    return manifest


def run_apache(max_nodes: int | None, out_dir: Path) -> dict:
    """
    Build kernel from Apache (or any org) edgelist for replication (A8.5: ≥2 datasets).
    Reads data/raw/apache/edges.txt or edges.txt.gz (format: from to, one per line).
    No labels. Output: kernel.npz + manifest.yaml.
    """
    raw_dir = DATA_RAW / APACHE_SOURCE_ID
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    edgelist_path = raw_dir / "edges.txt"
    if not edgelist_path.exists():
        edgelist_path = raw_dir / "edges.txt.gz"
    if not edgelist_path.exists():
        raise FileNotFoundError(
            f"Apache edgelist not found: {raw_dir / 'edges.txt'} or edges.txt.gz. "
            "Add an edgelist (from to per line) for replication. A sample is in data/raw/apache/README."
        )
    edges, n_full, nodes, node2idx = parse_edgelist_plain(edgelist_path)
    if len(edges) < 2:
        raise ValueError("Apache edgelist has too few edges")
    A_lcc, lcc_nodes = build_adjacency_lcc(edges, n_full)
    n_lcc = A_lcc.shape[0]
    if max_nodes is not None and max_nodes < n_lcc:
        A_sub, _ = subgraph_by_degree(A_lcc, max_nodes)
        A_final = A_sub
        n_used = max_nodes
        note = f"Subgraph: top {max_nodes} nodes by degree (from LCC size {n_lcc})"
    else:
        A_final = A_lcc
        n_used = n_lcc
        note = f"Full LCC: n={n_lcc}"
    K, mu = build_kernel_from_adjacency(A_final)
    np.savez(out_dir / "kernel.npz", K=K, mu=mu, n=n_used, n_full=n_full, n_lcc=n_lcc)
    manifest = {
        "source_id": APACHE_SOURCE_ID,
        "path": str(edgelist_path),
        "pipeline_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_original": int(n_full),
        "n_lcc": int(n_lcc),
        "n_used": int(n_used),
        "note": note,
        "kernel_recipe": "PRD-01 §2.5: row-normalized adjacency; μ = stationary; LCC then optional degree-subgraph.",
        "replication": "A8.5: ≥2 organizational datasets (email_eu_core, enron_snap, apache).",
    }
    manifest_path = out_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        f.write("# Apache (organizational replication) manifest\n")
        for k, v in manifest.items():
            f.write(f"{k}: {repr(v)}\n")
    print(f"Wrote {out_dir / 'kernel.npz'} and {manifest_path}")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-01/PRD-23: Download and normalize public data (Enron SNAP, email-Eu-core).")
    ap.add_argument("--source", default="enron_snap", help="Data source: enron_snap, email_eu_core, or apache (A8.5 replication)")
    ap.add_argument("--max-nodes", type=int, default=400, help="Max nodes for kernel (LCC subgraph by degree). Default 400 for feasible Test D / PRD-23.")
    ap.add_argument("--full", action="store_true", help="Use full LCC (no max-nodes cap)")
    args = ap.parse_args()
    max_nodes = None if args.full else args.max_nodes
    if args.source == "enron_snap":
        out_dir = DATA_PROCESSED / ENRON_SNAP_SOURCE_ID
        run_enron_snap(max_nodes, out_dir)
    elif args.source == "email_eu_core":
        out_dir = DATA_PROCESSED / EMAIL_EUCORE_SOURCE_ID
        run_email_eu_core(max_nodes, out_dir)
    elif args.source == "apache":
        out_dir = DATA_PROCESSED / APACHE_SOURCE_ID
        run_apache(max_nodes, out_dir)
    else:
        print("--source must be enron_snap, email_eu_core, or apache.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
