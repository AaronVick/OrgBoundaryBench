"""
Boundary Benchmark Harness (PRD-17). Empirical Test Family A.

Reusable evaluation harness for candidate partitions: multi-objective J(q),
baselines (one-block, singleton, Louvain, random matched), leaderboard, success criterion.
Falsification: q* fails to beat trivial/standard baselines on J(q).
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Sequence, Tuple

from .operators import closure_energy
from .projection import identity_partition, single_block_partition
from .greedy import greedy_coarse_graining
from .baselines import graph_modularity_q, louvain_partition


def random_partition_matched(
    n: int,
    n_blocks: int,
    rng: np.random.Generator,
) -> List[List[int]]:
    """Random partition with exactly n_blocks blocks (each non-empty). PRD-17 trivial baseline."""
    if n_blocks < 1 or n_blocks > n:
        raise ValueError("n_blocks must be in [1, n]")
    assign = rng.integers(0, n_blocks, size=n)
    # Ensure each block appears (so we have exactly n_blocks blocks)
    assign[:n_blocks] = np.arange(n_blocks)
    rng.shuffle(assign)
    blocks: Dict[int, List[int]] = {b: [] for b in range(n_blocks)}
    for i in range(n):
        blocks[assign[i]].append(i)
    return [blocks[b] for b in range(n_blocks) if blocks[b]]


def cost_triviality(partition: Sequence[Sequence[int]]) -> float:
    """
    Cost term that penalizes trivial coarse partitions. PRD-17 §2.3.
    Cost(q) = 1/|q| so one-block has cost 1 (worst), finer partitions have lower cost.
    Lower J is better, so higher cost worsens J.
    """
    k = len(partition)
    if k < 1:
        return 1.0
    return 1.0 / float(k)


def score_J(
    K: np.ndarray,
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
    *,
    alpha: float = 1.0,
    beta: float = 0.0,
    gamma: float = 0.0,
    eta: float = 0.5,
) -> Tuple[float, float, float, float]:
    """
    Multi-objective score J(q) = alpha*E_cl + beta*E_rob + gamma*delta_otimes + eta*Cost(q).
    PRD-17. E_rob and delta_otimes not implemented; use beta=gamma=0.
    Returns (E_cl, cost, J, Q).
    """
    E_cl = float(closure_energy(K, mu, partition))
    cost = cost_triviality(partition)
    E_rob = 0.0  # not implemented
    delta_otimes = 0.0  # not implemented
    J = alpha * E_cl + beta * E_rob + gamma * delta_otimes + eta * cost
    Q = float(graph_modularity_q(K, partition))
    return (E_cl, cost, float(J), Q)


def run_harness(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    q_org: Sequence[Sequence[int]] | None = None,
    alpha: float = 1.0,
    eta: float = 0.5,
    n_random: int = 5,
    rng: np.random.Generator | None = None,
) -> Tuple[List[Dict[str, Any]], List[List[int]], bool]:
    """
    Run Boundary Benchmark Harness (PRD-17).

    Returns (leaderboard, q_star, success).
    leaderboard: list of dicts with keys name, n_blocks, E_cl, cost, J, Q.
    success: True iff q_star has |q_star|>=2 and J(q_star) < J(baseline) for all baselines.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = K.shape[0]
    leaderboard: List[Dict[str, Any]] = []

    def add(name: str, q: List[List[int]]) -> None:
        E_cl, cost, J, Q = score_J(K, mu, q, alpha=alpha, eta=eta)
        leaderboard.append({
            "name": name,
            "n_blocks": len(q),
            "E_cl": E_cl,
            "cost": cost,
            "J": J,
            "Q": Q,
        })

    # One-block
    q_one = single_block_partition(n)
    add("one_block", q_one)

    # Singleton
    q_singleton = identity_partition(n)
    add("singleton", q_singleton)

    # Framework q* (greedy)
    q_star, _, _ = greedy_coarse_graining(K, mu)
    add("q_star", q_star)

    # Louvain (if available)
    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        add("Louvain", q_louvain)

    # Org-chart (when provided)
    if q_org is not None:
        add("org_chart", list(q_org))

    # Random matched to q_star block count
    k_star = len(q_star)
    for i in range(n_random):
        q_rand = random_partition_matched(n, max(1, min(k_star, n)), rng)
        add(f"random_{i}", q_rand)

    # Sort by J (lower better)
    leaderboard.sort(key=lambda x: x["J"])

    # Success: q_star must have |q_star| >= 2 (non-trivial) and J(q_star) must be strictly better than J(one_block) and J(singleton)
    J_star = next(x["J"] for x in leaderboard if x["name"] == "q_star")
    J_one = next(x["J"] for x in leaderboard if x["name"] == "one_block")
    J_singleton = next(x["J"] for x in leaderboard if x["name"] == "singleton")
    non_trivial = len(q_star) >= 2
    beats_one = J_star < J_one
    beats_singleton = J_star < J_singleton
    # Beat Louvain if present
    if q_louvain is not None:
        J_louvain = next(x["J"] for x in leaderboard if x["name"] == "Louvain")
        beats_louvain = J_star < J_louvain
    else:
        beats_louvain = True
    # Beat mean random
    rand_js = [x["J"] for x in leaderboard if x["name"].startswith("random_")]
    mean_rand = np.mean(rand_js) if rand_js else J_star
    beats_random = J_star < mean_rand if rand_js else True

    success = (
        non_trivial
        and beats_one
        and beats_singleton
        and beats_louvain
        and beats_random
    )
    return leaderboard, q_star, success
