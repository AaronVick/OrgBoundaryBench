"""
Greedy coarse-graining: merge block pair that minimally increases E_cl. Theorem 3.4.

PRD-02 §6: terminates in at most n-1 steps; block count decreases by 1 per merge.
Tie-break: lexicographically smallest (i, j) among pairs with same Δ.
"""

from __future__ import annotations

import numpy as np
from typing import List, Sequence, Tuple, Callable

from .operators import closure_energy
from .projection import identity_partition


def merge_blocks(partition: List[List[int]], i: int, j: int) -> List[List[int]]:
    """Return new partition with blocks i and j merged. T3.4 merge step. i < j."""
    out = [list(bl) for k, bl in enumerate(partition) if k not in (i, j)]
    merged = list(partition[i]) + list(partition[j])
    # Insert merged block so order is deterministic (e.g. at index min(i,j))
    out.insert(min(i, j), merged)
    return out


def greedy_coarse_graining(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    max_steps: int | None = None,
    energy_fn: Callable[[np.ndarray, np.ndarray, Sequence[Sequence[int]]], float] = closure_energy,
) -> Tuple[List[List[int]], List[float], int]:
    """
    Greedy coarse-graining fixed point q* (T3.4).

    Returns:
        q_star: partition (list of blocks)
        energy_trajectory: E_cl at each step (including initial identity)
        n_steps: number of merges performed (<= n-1)

    PRD-02 §6.1: init q = identity; each step merge (i*, j*) = argmin Δ_ij; stop when one block.
    """
    n = K.shape[0]
    if max_steps is None:
        max_steps = n - 1
    q = identity_partition(n)
    trajectory = [energy_fn(K, mu, q)]
    steps = 0
    while len(q) > 1 and steps < max_steps:
        m = len(q)
        best_delta = np.inf
        best_pair: Tuple[int, int] | None = None
        E_current = trajectory[-1]
        for i in range(m):
            for j in range(i + 1, m):
                q_merge = merge_blocks(q, i, j)
                E_merge = energy_fn(K, mu, q_merge)
                delta = E_merge - E_current
                if delta < best_delta or (delta == best_delta and (best_pair is None or (i, j) < best_pair)):
                    best_delta = delta
                    best_pair = (i, j)
        if best_pair is None:
            break
        i, j = best_pair
        q = merge_blocks(q, i, j)
        trajectory.append(energy_fn(K, mu, q))
        steps += 1
    return q, trajectory, steps


def greedy_fixed_point(
    K: np.ndarray,
    mu: np.ndarray,
) -> List[List[int]]:
    """Convenience: return only q* (first element of greedy_coarse_graining). T3.4."""
    q_star, _, _ = greedy_coarse_graining(K, mu)
    return q_star
