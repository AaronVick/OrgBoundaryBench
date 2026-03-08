"""
Synthetic kernel generators for Domain 6.1 (PRD-04).

Def 2.1 (K, μ); Def 2.3 (lumpability). Lumpable: E_cl(q)=0. Non-lumpable: PRD-04 §2.2 (perturbed, random).
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SyntheticKernel:
    """Canonical schema: K, mu, partition, lumpable flag. PRD-01 §4."""
    K: np.ndarray
    mu: np.ndarray
    partition: List[List[int]]
    lumpable: bool


def _normalize_rows(M: np.ndarray) -> np.ndarray:
    """Stochastic: each row sums to 1."""
    row_sums = M.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return M / row_sums


def _stationary_distribution(K: np.ndarray) -> np.ndarray:
    """Invariant measure μ: left eigenvector with eigenvalue 1, normalized. Def 2.1."""
    eigvals, eigvecs = np.linalg.eig(K.T)
    idx = np.argmin(np.abs(eigvals - 1.0))
    mu = np.real(eigvecs[:, idx]).ravel()
    mu = np.maximum(mu, 1e-15)
    total = mu.sum()
    if total <= 0:
        mu = np.ones(K.shape[0]) / K.shape[0]
    else:
        mu = mu / total
    return mu


def make_lumpable_block_diagonal(
    n: int,
    partition: Optional[List[List[int]]] = None,
    *,
    rng: Optional[np.random.Generator] = None,
) -> SyntheticKernel:
    """
    Lumpable K: block-diagonal (no cross-block mass). Def 2.3, PRD-04 §2.1.

    Within each block: random stochastic submatrix. If partition is None, use 2 blocks [0:n//2], [n//2:n].
    """
    rng = rng or np.random.default_rng()
    if partition is None:
        m = 2
        partition = [list(range(0, n // 2)), list(range(n // 2, n))]
    else:
        partition = [list(B) for B in partition]
    K = np.zeros((n, n))
    for Bk in partition:
        Bk = np.asarray(Bk)
        size = len(Bk)
        block = rng.uniform(0.1, 1.0, (size, size))
        block = _normalize_rows(block)
        K[np.ix_(Bk, Bk)] = block
    mu = _stationary_distribution(K)
    return SyntheticKernel(K=K, mu=mu, partition=partition, lumpable=True)


def make_lumpable_quotient(
    n: int,
    m: int,
    *,
    rng: Optional[np.random.Generator] = None,
) -> SyntheticKernel:
    """
    Lumpable by construction: quotient chain on m states; each state in block k has same
    transition distribution to blocks, then uniform within target block. Def 2.3, PRD-04 §2.1.
    """
    rng = rng or np.random.default_rng()
    # Random quotient chain on {0,...,m-1}
    K_bar = rng.uniform(0.1, 1.0, (m, m))
    K_bar = _normalize_rows(K_bar)
    # Assign states to blocks (roughly equal)
    partition = []
    for k in range(m):
        start = (k * n) // m
        end = ((k + 1) * n) // m
        partition.append(list(range(start, end)))
    # K(i,j) = K_bar(k,ell) / |B_ell| for i in B_k, j in B_ell
    K = np.zeros((n, n))
    for k, Bk in enumerate(partition):
        for ell, B_ell in enumerate(partition):
            size_ell = len(B_ell)
            if size_ell == 0:
                continue
            val = K_bar[k, ell] / size_ell
            for i in Bk:
                for j in B_ell:
                    K[i, j] = val
    # Normalize rows (floating point)
    K = _normalize_rows(K)
    mu = _stationary_distribution(K)
    return SyntheticKernel(K=K, mu=mu, partition=partition, lumpable=True)


def make_non_lumpable_perturbed(
    base: SyntheticKernel,
    epsilon: float = 0.05,
    *,
    rng: Optional[np.random.Generator] = None,
) -> SyntheticKernel:
    """
    Non-lumpable: K = (1-ε) K_lumpable + ε K_noise. PRD-04 §2.2.

    K_noise has cross-block support so E_cl > 0.
    """
    rng = rng or np.random.default_rng()
    K_noise = rng.uniform(0, 1, base.K.shape)
    K_noise = _normalize_rows(K_noise)
    K = (1 - epsilon) * base.K + epsilon * K_noise
    K = _normalize_rows(K)
    mu = _stationary_distribution(K)
    return SyntheticKernel(K=K, mu=mu, partition=base.partition, lumpable=False)


def make_non_lumpable_random(
    n: int,
    partition: Optional[List[List[int]]] = None,
    *,
    rng: Optional[np.random.Generator] = None,
) -> SyntheticKernel:
    """
    Random stochastic K; given partition is almost surely not lumpable. PRD-04 §2.2.
    """
    rng = rng or np.random.default_rng()
    K = rng.uniform(0.1, 1.0, (n, n))
    K = _normalize_rows(K)
    mu = _stationary_distribution(K)
    if partition is None:
        partition = [list(range(0, n // 2)), list(range(n // 2, n))]
    return SyntheticKernel(K=K, mu=mu, partition=partition, lumpable=False)
