"""
Directed flag complex dFlag(G) from directed weighted graph.

A k-simplex is a directed (k+1)-clique: vertices v0 < v1 < ... < vk with
directed edge (vi, vj) for all i < j. Filtration value = min edge weight in simplex.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def _is_directed_clique(W: np.ndarray, vertices: Tuple[int, ...]) -> bool:
    """True iff vertices form a directed clique (all forward edges present)."""
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            if W[vertices[i], vertices[j]] <= 0:
                return False
    return True


def _min_edge_weight(W: np.ndarray, vertices: Tuple[int, ...]) -> float:
    """Min weight over forward edges in the clique."""
    if len(vertices) < 2:
        return 1.0
    return float(min(W[vertices[i], vertices[j]] for i in range(len(vertices)) for j in range(i + 1, len(vertices))))


def enumerate_directed_cliques(
    W: np.ndarray,
    max_dim: int = 4,
) -> List[Tuple[Tuple[int, ...], float]]:
    """
    Enumerate all directed cliques (simplices) and their birth times.

    W: n x n directed weight matrix (nonnegative). Edge (i,j) present if W[i,j] > 0.
    max_dim: max simplex dimension (max_dim+1 vertices).
    Returns: list of ((v0, v1, ...), birth) with vertices sorted and birth = min edge weight.
    """
    n = W.shape[0]
    if W.shape != (n, n):
        raise ValueError("W must be square")
    out: List[Tuple[Tuple[int, ...], float]] = []

    def recurse(vertices: Tuple[int, ...], next_start: int) -> None:
        if not _is_directed_clique(W, vertices):
            return
        birth = _min_edge_weight(W, vertices)
        out.append((vertices, birth))
        if len(vertices) <= max_dim:
            for i in range(next_start, n):
                recurse(vertices + (i,), i + 1)

    for i in range(n):
        recurse((i,), i + 1)
    return out


def directed_flag_complex(
    W: np.ndarray,
    threshold: float | None = None,
    max_dim: int = 4,
) -> List[Tuple[Tuple[int, ...], float]]:
    """
    Build directed flag complex: include only simplices whose edges all have weight >= threshold.

    If threshold is None, use all simplices (threshold = 0). Each simplex has
    filtration value = min edge weight (so it appears at that threshold).
    """
    all_simplices = enumerate_directed_cliques(W, max_dim=max_dim)
    if threshold is not None:
        all_simplices = [(s, b) for s, b in all_simplices if b >= threshold]
    return all_simplices
