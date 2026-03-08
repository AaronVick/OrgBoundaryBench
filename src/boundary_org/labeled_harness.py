"""
PRD-23: Nontrivial boundary on public labeled graphs.

Run harness (J(q), baselines) and compute external agreement (NMI, ARI, macro-F1) vs ground-truth labels.
Determines "meaningful boundary" vs "useless collapse" per PRD-23 §3–§5.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Sequence, Tuple

from .phase_monitoring import partition_to_labels
from .harness import run_harness, score_J, random_partition_matched
from .baselines import spectral_partition, louvain_partition
from .projection import identity_partition, single_block_partition
from .greedy import greedy_coarse_graining


def external_agreement(
    partition: Sequence[Sequence[int]],
    true_labels: np.ndarray,
    n: int,
) -> Dict[str, float]:
    """
    External agreement of partition with ground-truth labels. PRD-23 §2.3.

    true_labels: array of length n (e.g. department id). Use only nodes with true_labels >= 0.
    Returns dict with nmi, ari, macro_f1 in [0,1]; higher = better agreement.
    """
    from sklearn.metrics import (
        normalized_mutual_info_score,
        adjusted_rand_score,
        f1_score,
    )
    pred = partition_to_labels(partition, n)
    true = np.asarray(true_labels, dtype=np.int64).ravel()[:n]
    # Restrict to labeled nodes
    mask = true >= 0
    if not np.any(mask):
        return {"nmi": 0.0, "ari": 0.0, "macro_f1": 0.0}
    pred_m = pred[mask]
    true_m = true[mask]
    if np.unique(true_m).size < 2 and np.unique(pred_m).size < 2:
        nmi = 1.0 if np.all(true_m == pred_m) else 0.0
        ari = 1.0 if np.all(true_m == pred_m) else 0.0
        macro_f1 = 1.0 if np.all(true_m == pred_m) else 0.0
        return {"nmi": nmi, "ari": ari, "macro_f1": macro_f1}
    nmi = float(normalized_mutual_info_score(true_m, pred_m, average_method="arithmetic"))
    ari = float(adjusted_rand_score(true_m, pred_m))
    try:
        macro_f1 = float(f1_score(true_m, pred_m, average="macro", zero_division=0))
    except Exception:
        macro_f1 = 0.0
    return {"nmi": nmi, "ari": ari, "macro_f1": macro_f1}


def run_nontrivial_boundary_labeled(
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    *,
    alpha: float = 1.0,
    eta: float = 0.5,
    n_random: int = 5,
    rng: np.random.Generator | None = None,
) -> Tuple[List[Dict[str, Any]], List[List[int]], bool, bool]:
    """
    PRD-23: Run harness plus spectral baseline; attach external agreement (NMI, ARI, macro-F1) to each candidate.

    Returns (leaderboard_with_agreement, q_star, success, meaningful).
    success: harness success (nontrivial q* beats baselines on J(q)).
    meaningful: q* is nontrivial and its external agreement is no worse than best baseline (PRD-23 §3).
    """
    n = K.shape[0]
    if rng is None:
        rng = np.random.default_rng(42)
    leaderboard: List[Dict[str, Any]] = []

    def add(name: str, q: List[List[int]]) -> None:
        E_cl, cost, J, Q = score_J(K, mu, q, alpha=alpha, eta=eta)
        entry: Dict[str, Any] = {
            "name": name,
            "n_blocks": len(q),
            "E_cl": E_cl,
            "cost": cost,
            "J": J,
            "Q": Q,
        }
        entry["agreement"] = external_agreement(q, labels, n)
        leaderboard.append(entry)

    add("one_block", single_block_partition(n))
    add("singleton", identity_partition(n))
    q_star, _, _ = greedy_coarse_graining(K, mu)
    add("q_star", q_star)
    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        add("Louvain", q_louvain)
    add("spectral", spectral_partition(K))
    k_star = len(q_star)
    for i in range(n_random):
        q_rand = random_partition_matched(n, max(1, min(k_star, n)), rng)
        add(f"random_{i}", q_rand)

    leaderboard.sort(key=lambda x: x["J"])

    J_star = next(x["J"] for x in leaderboard if x["name"] == "q_star")
    J_one = next(x["J"] for x in leaderboard if x["name"] == "one_block")
    J_singleton = next(x["J"] for x in leaderboard if x["name"] == "singleton")
    non_trivial = len(q_star) >= 2
    beats_one = J_star < J_one
    beats_singleton = J_star < J_singleton
    if q_louvain is not None:
        J_louvain = next(x["J"] for x in leaderboard if x["name"] == "Louvain")
        beats_louvain = J_star < J_louvain
    else:
        beats_louvain = True
    rand_js = [x["J"] for x in leaderboard if x["name"].startswith("random_")]
    beats_random = J_star < np.mean(rand_js) if rand_js else True
    success = non_trivial and beats_one and beats_singleton and beats_louvain and beats_random

    best_nmi = max((e["agreement"]["nmi"] for e in leaderboard if e["name"] != "q_star"), default=0.0)
    best_ari = max((e["agreement"]["ari"] for e in leaderboard if e["name"] != "q_star"), default=0.0)
    best_f1 = max((e["agreement"]["macro_f1"] for e in leaderboard if e["name"] != "q_star"), default=0.0)
    star_agreement = next(e["agreement"] for e in leaderboard if e["name"] == "q_star")
    meaningful = (
        non_trivial
        and star_agreement["nmi"] >= best_nmi
        and star_agreement["ari"] >= best_ari
        and star_agreement["macro_f1"] >= best_f1
    )
    return leaderboard, q_star, success, meaningful
