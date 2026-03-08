"""
PRD III (thoughts3): Outlier and Leverage Stability Test.

S(q) = sup_{A in A_eps} |Perf(q) - Perf^{(-A)}(q)|. Results must remain stable under
small adversarial removals (node-drop, edge-drop, window-drop). Pass: S below threshold.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .greedy import greedy_coarse_graining
from .harness import score_J


def _kernel_subgraph_nodes(K: np.ndarray, mu: np.ndarray, keep_idx: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Restrict K and mu to keep_idx; renormalize."""
    K_sub = K[np.ix_(keep_idx, keep_idx)]
    mu_sub = mu[keep_idx].copy()
    mu_sub /= mu_sub.sum()
    row_sums = K_sub.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    K_sub = K_sub / row_sums
    return K_sub, mu_sub


def _extend_partition_to_full(partition: List[List[int]], keep_idx: np.ndarray, n_full: int) -> List[List[int]]:
    """Map partition on subgraph (indices 0..len(keep_idx)-1) to full: node sub_i -> keep_idx[sub_i]; dropped nodes -> last block."""
    keep_set = set(keep_idx)
    full_assign: Dict[int, List[int]] = {b: [] for b in range(len(partition) + 1)}
    for b, bl in enumerate(partition):
        for sub_i in bl:
            full_assign[b].append(int(keep_idx[sub_i]))
    for j in range(n_full):
        if j not in keep_set:
            full_assign[len(partition)].append(j)
    return [full_assign[b] for b in range(len(partition) + 1) if full_assign[b]]


def node_drop_perturbation(
    K: np.ndarray,
    mu: np.ndarray,
    drop_frac: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Indices to keep (drop drop_frac of nodes randomly)."""
    n = K.shape[0]
    n_drop = max(1, int(n * drop_frac))
    keep = rng.choice(n, size=n - n_drop, replace=False)
    return np.sort(keep)


def top_degree_node_drop_perturbation(
    K: np.ndarray,
    drop_frac: float,
) -> np.ndarray:
    """
    Stronger leverage test: drop the top (drop_frac * n) nodes by out-degree (row sum of K).
    Returns indices to keep (low-degree nodes retained).
    """
    n = K.shape[0]
    degree = np.asarray(K).sum(axis=1)
    n_drop = max(1, int(n * drop_frac))
    # highest degree first -> drop those
    order = np.argsort(-degree)
    drop_idx = set(order[:n_drop])
    keep = np.array([i for i in range(n) if i not in drop_idx], dtype=np.int64)
    return keep


def edge_drop_perturbation(
    K: np.ndarray,
    drop_frac: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """New kernel with drop_frac of non-diagonal mass zeroed (then renormalize)."""
    K = np.asarray(K).copy()
    n = K.shape[0]
    triu = np.triu_indices(n, 1)
    n_edges = triu[0].size
    n_drop = max(1, int(n_edges * drop_frac))
    idx = rng.choice(n_edges, size=n_drop, replace=False)
    i, j = triu[0][idx], triu[1][idx]
    K[i, j] = 0
    K[j, i] = 0
    row_sums = K.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return (K / row_sums).astype(np.float64)


def run_leverage_stability(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    epsilon_list: Tuple[float, ...] = (0.05, 0.1),
    n_trials_per_epsilon: int = 3,
    stability_threshold: float = 1.0,
    rng: Optional[np.random.Generator] = None,
    use_node_drop: bool = True,
    use_edge_drop: bool = True,
    use_top_degree_drop: bool = True,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD III: S = max over (epsilon, trial) of |Perf(q_full) - Perf(q_{-A})|.
    Perf = -J(q). Node-drop: remove epsilon fraction of nodes; edge-drop: remove epsilon fraction of edges.
    Pass: S < stability_threshold.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = K.shape[0]
    q_full, _, _ = greedy_coarse_graining(K, mu)
    perf_full = -score_J(K, mu, q_full)[2]  # -J

    deltas: List[float] = []
    details: List[Dict[str, Any]] = []

    if use_node_drop:
        for eps in epsilon_list:
            for t in range(n_trials_per_epsilon):
                keep_idx = node_drop_perturbation(K, mu, eps, rng)
                if len(keep_idx) < 2:
                    continue
                K_sub, mu_sub = _kernel_subgraph_nodes(K, mu, keep_idx)
                q_sub, _, _ = greedy_coarse_graining(K_sub, mu_sub)
                q_ext = _extend_partition_to_full(q_sub, keep_idx, n)
                perf_sub = -score_J(K, mu, q_ext)[2]
                delta = abs(perf_full - perf_sub)
                deltas.append(delta)
                details.append({"type": "node_drop", "epsilon": eps, "trial": t, "delta": delta})

    if use_edge_drop:
        for eps in epsilon_list:
            for t in range(n_trials_per_epsilon):
                K_ed = edge_drop_perturbation(K, eps, rng)
                mu_ed = mu  # same mu
                q_ed, _, _ = greedy_coarse_graining(K_ed, mu_ed)
                perf_ed = -score_J(K, mu, q_ed)[2]
                delta = abs(perf_full - perf_ed)
                deltas.append(delta)
                details.append({"type": "edge_drop", "epsilon": eps, "trial": t, "delta": delta})

    if use_top_degree_drop:
        for eps in epsilon_list:
            keep_idx = top_degree_node_drop_perturbation(K, eps)
            if len(keep_idx) < 2:
                continue
            K_sub, mu_sub = _kernel_subgraph_nodes(K, mu, keep_idx)
            q_sub, _, _ = greedy_coarse_graining(K_sub, mu_sub)
            q_ext = _extend_partition_to_full(q_sub, keep_idx, n)
            perf_sub = -score_J(K, mu, q_ext)[2]
            delta = abs(perf_full - perf_sub)
            deltas.append(delta)
            details.append({"type": "top_degree_drop", "epsilon": eps, "delta": delta})

    S = float(max(deltas)) if deltas else 0.0
    pass_ = S < stability_threshold
    return {
        "perf_full": perf_full,
        "S_max": S,
        "n_perturbations": len(deltas),
        "stability_threshold": stability_threshold,
        "details": details,
    }, pass_
