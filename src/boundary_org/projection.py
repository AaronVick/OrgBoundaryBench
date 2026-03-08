"""
Projection Π_q onto B_q-measurable functions.  [Paper Eq. (1), Def 2.2]

(Π_q)_{ij} = μ_j / μ(B_k)  if i,j in same block B_k; else 0.
PRD-00 §2.2; PRD-02 §2.3.
"""

from __future__ import annotations

import numpy as np
from typing import List, Sequence, Union


def block_masses(mu: np.ndarray, partition: Sequence[Sequence[int]]) -> np.ndarray:
    """μ(B_k) for each block. Def 2.2 (Π_q weights). partition[k] = list of state indices in block k."""
    return np.array([mu[np.asarray(Bk)].sum() for Bk in partition])


def projection_matrix(
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
    *,
    mu_min: float = 1e-15,
) -> np.ndarray:
    """
    Build Π_q in matrix form: (Π_q)_{ij} = μ_j / μ(B_k) for i,j in same block B_k; 0 else.

    Def 2.2. PRD-02 §2.3. Requires μ(B_k) > 0 for all k; uses mu_min to guard division.
    """
    mu = np.asarray(mu, dtype=float)
    n = mu.size
    Pi = np.zeros((n, n))
    for Bk in partition:
        Bk = np.asarray(Bk)
        mass = mu[Bk].sum()
        if mass < mu_min:
            raise ValueError(f"Block mass {mass} below mu_min={mu_min}; partition invalid for L2(mu)")
        # Submatrix Pi[Bk, Bk] = (1/mass) * 1 * μ^T|_{Bk}
        for i in Bk:
            for j in Bk:
                Pi[i, j] = mu[j] / mass
    return Pi


def partition_from_blocks(n: int, blocks: Sequence[Sequence[int]]) -> List[List[int]]:
    """Normalize partition to list of lists of indices in [0, n-1]. Validates disjoint cover (Def 2.2). PRD-02 partition representation."""
    seen = set()
    out = []
    for Bk in blocks:
        Bk = list(np.asarray(Bk).ravel())
        for i in Bk:
            if i < 0 or i >= n:
                raise ValueError(f"State index {i} out of range [0, {n-1}]")
            if i in seen:
                raise ValueError(f"State {i} appears in more than one block")
            seen.add(i)
        out.append(Bk)
    if seen != set(range(n)):
        raise ValueError("Partition does not cover state space")
    return out


def identity_partition(n: int) -> List[List[int]]:
    """q_n: finest partition, each state its own block. Def 2.2; T3.4 initial condition. PRD-02 §6.1."""
    return [[i] for i in range(n)]


def single_block_partition(n: int) -> List[List[int]]:
    """Trivial partition q = {S}. Def 2.3 (E_cl = 0). PRD-02 §2.4."""
    return [list(range(n))]
