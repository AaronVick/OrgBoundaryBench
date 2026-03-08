"""
Baseline methods for comparison (PRD-02, PRD-04, PRD-06).

Graph modularity Q [5] Newman (2006) PNAS — baseline for Domain 6.1 (E6.1).
Q = sum_c (e_cc - a_c^2); higher Q = more modular (within-block density).
Falsification: consistent underperformance of closure energy vs Q on synthetics.
"""

from __future__ import annotations

import numpy as np
from typing import Sequence


def _adjacency_from_kernel(K: np.ndarray) -> np.ndarray:
    """
    Symmetric weighted adjacency from Markov kernel for modularity.
    A = (K + K.T) / 2 so 2m = sum_ij A_ij. PRD-04 §4.1.
    """
    return (np.asarray(K) + np.asarray(K).T) / 2.0


def graph_modularity_q(
    K: np.ndarray,
    partition: Sequence[Sequence[int]],
) -> float:
    """
    Newman (2006) modularity Q for partition on graph with weight matrix from K.

    Q = (1/(2m)) sum_ij [ A_ij - (k_i k_j)/(2m) ] δ(c_i, c_j)
      = sum_c ( e_cc - a_c^2 ),  e_cc = (1/2m) sum_{i,j in c} A_ij,  a_c = (1/2m) sum_{i in c} k_i.

    Baseline [5] for PRD-04 §4.1. Higher Q => more within-community density.
    """
    A = _adjacency_from_kernel(K)
    n = A.shape[0]
    two_m = float(A.sum())
    if two_m <= 0:
        return 0.0
    k = A.sum(axis=1)  # degree
    Q = 0.0
    for Bk in partition:
        Bk = np.asarray(Bk)
        e_cc = A[np.ix_(Bk, Bk)].sum() / two_m
        a_c = k[Bk].sum() / two_m
        Q += e_cc - a_c * a_c
    return float(Q)


def discrimination_auc(
    labels: np.ndarray,
    scores_lumpable_high: np.ndarray,
) -> float:
    """
    AUC for binary classification: label 1 = lumpable, 0 = non-lumpable.
    scores_lumpable_high: higher value => predict lumpable (e.g. -E_cl or Q).
    E6.1 (Section 6.1): closure energy must achieve AUC >= AUC(Q) - 0.05. PRD-04 §4.1.
    """
    from sklearn.metrics import roc_auc_score
    labels = np.asarray(labels).ravel()
    scores = np.asarray(scores_lumpable_high).ravel()
    if np.unique(labels).size < 2:
        return 0.5
    return float(roc_auc_score(labels, scores))


def louvain_partition(K: np.ndarray) -> list[list[int]] | None:
    """
    Louvain community detection [6] on graph from kernel K. PRD-05 Test D baseline.

    A = (K + K')/2; run Louvain; return partition as list of blocks (node indices).
    Returns None if networkx is not installed or Louvain fails.
    """
    try:
        import networkx as nx
        from networkx.algorithms.community import louvain_communities
    except ImportError:
        return None
    A = _adjacency_from_kernel(K)
    n = A.shape[0]
    G = nx.Graph()
    for i in range(n):
        for j in range(i + 1, n):
            if A[i, j] > 0:
                G.add_edge(i, j, weight=float(A[i, j]))
    try:
        communities = louvain_communities(G, seed=42)
    except Exception:
        return None
    # Convert set-of-nodes to list-of-blocks (sorted for determinism)
    partition = [sorted(c) for c in communities]
    return partition


def spectral_partition(K: np.ndarray) -> list[list[int]]:
    """
    Spectral clustering baseline (Fiedler cut): 2-way partition from second eigenvector of Laplacian.
    PRD-23 §2.1. A = (K + K')/2; L = D - A; split at median of Fiedler vector.
    """
    A = _adjacency_from_kernel(K)
    n = A.shape[0]
    deg = A.sum(axis=1)
    D = np.diag(deg)
    L = D - A
    # Small regularization for numerical stability
    L = L + 1e-10 * np.eye(n)
    try:
        eigvals, eigvecs = np.linalg.eigh(L)
        # Fiedler = eigenvector for second smallest eigenvalue (first is ~0)
        idx = np.argsort(eigvals)[1]
        fiedler = np.real(eigvecs[:, idx]).ravel()
        med = np.median(fiedler)
        left = [i for i in range(n) if fiedler[i] <= med]
        right = [i for i in range(n) if fiedler[i] > med]
        if not left:
            left = [np.argmin(fiedler)]
            right = [i for i in range(n) if i != left[0]]
        elif not right:
            right = [np.argmax(fiedler)]
            left = [i for i in range(n) if i != right[0]]
        return [sorted(left), sorted(right)]
    except Exception:
        return [list(range(n))]
