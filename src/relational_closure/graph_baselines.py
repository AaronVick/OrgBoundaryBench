"""
Graph baselines for RCTI comparative pipeline (PRD-21 §3).

Plain graph statistics on the directed weight matrix W used by RCTI:
density, clustering, reciprocity, modularity, spectral gap, entropy.
Used to test whether topological summaries (C1, C2F, barcode) add value.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Any


def graph_density(W: np.ndarray) -> float:
    """Edge density: (number of positive edges) / n^2 or sum(W)/n^2. PRD-21 baseline."""
    n = W.shape[0]
    if n == 0:
        return 0.0
    return float(np.count_nonzero(W > 0) / (n * n))


def graph_clustering_directed(W: np.ndarray) -> float:
    """
    Directed clustering: fraction of directed triangles (i→j, j→k, i→k) among possible.
    Uses triplets (i,j,k) with i<j<k; count where all three forward edges present; normalize by number of triplets.
    PRD-21 baseline.
    """
    n = W.shape[0]
    if n < 3:
        return 0.0
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if W[i, j] > 0 and W[j, k] > 0 and W[i, k] > 0:
                    count += 1
                total += 1
    return count / total if total > 0 else 0.0


def graph_reciprocity(W: np.ndarray) -> float:
    """Fraction of edges that are reciprocated: (i,j) and (j,i) both > 0. PRD-21 baseline."""
    n = W.shape[0]
    if n < 2:
        return 0.0
    reciprocated = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            if W[i, j] > 0 or W[j, i] > 0:
                total += 1
                if W[i, j] > 0 and W[j, i] > 0:
                    reciprocated += 1
    return reciprocated / total if total > 0 else 0.0


def graph_modularity_symmetrized(W: np.ndarray) -> float:
    """
    Modularity Q on symmetrized adjacency A = (W + W.T)/2, single community = 0.
    For baseline we use Q of best 2-block split by sign of Fiedler vector (spectral bisection).
    PRD-21 baseline. Returns 0 if scipy/nx not available or graph too small.
    """
    n = W.shape[0]
    if n < 2:
        return 0.0
    A = (np.asarray(W) + np.asarray(W).T) / 2.0
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import laplacian
        from scipy.sparse.linalg import eigsh
    except ImportError:
        return 0.0
    two_m = float(A.sum())
    if two_m <= 0:
        return 0.0
    L = laplacian(csr_matrix(A), normed=False)
    try:
        vals, vecs = eigsh(L.asfptype(), k=2, which="SM")
    except Exception:
        return 0.0
    fiedler = vecs[:, 1]
    part = [np.where(fiedler >= 0)[0], np.where(fiedler < 0)[0]]
    # Q = sum_c (e_cc - a_c^2)
    e_11 = A[np.ix_(part[0], part[0])].sum() / two_m
    e_22 = A[np.ix_(part[1], part[1])].sum() / two_m
    k = A.sum(axis=1)
    a_1 = k[part[0]].sum() / two_m
    a_2 = k[part[1]].sum() / two_m
    Q = (e_11 - a_1 * a_1) + (e_22 - a_2 * a_2)
    return float(Q)


def graph_spectral_gap(W: np.ndarray) -> float:
    """
    Spectral gap of symmetrized Laplacian L = D - A (unnormalized).
    Gap = smallest non-zero eigenvalue. PRD-21 baseline.
    """
    n = W.shape[0]
    if n < 2:
        return 0.0
    A = (np.asarray(W) + np.asarray(W).T) / 2.0
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import laplacian
        from scipy.sparse.linalg import eigsh
    except ImportError:
        return 0.0
    L = laplacian(csr_matrix(A), normed=False)
    try:
        vals = eigsh(L.asfptype(), k=min(4, n), which="SM", return_eigenvectors=False)
    except Exception:
        return 0.0
    # Smallest eigenvalue is 0; next is spectral gap
    vals = np.sort(vals)
    for v in vals:
        if v > 1e-10:
            return float(v)
    return 0.0


def graph_entropy_degrees(W: np.ndarray) -> float:
    """
    Entropy of out-degree distribution (normalized). PRD-21 baseline.
    degree_i = sum_j W[i,j]; histogram then H = -sum p log p.
    """
    n = W.shape[0]
    if n == 0:
        return 0.0
    out_deg = np.asarray(W).sum(axis=1)
    total = out_deg.sum()
    if total <= 0:
        return 0.0
    p = out_deg / total
    p = p[p > 0]
    return float(-np.sum(p * np.log(p + 1e-20)))


def compute_all_baselines(W: np.ndarray) -> Dict[str, Any]:
    """Compute all six PRD-21 graph baselines. Returns dict of name -> value."""
    return {
        "density": graph_density(W),
        "clustering": graph_clustering_directed(W),
        "reciprocity": graph_reciprocity(W),
        "modularity": graph_modularity_symmetrized(W),
        "spectral_gap": graph_spectral_gap(W),
        "entropy_degrees": graph_entropy_degrees(W),
    }
