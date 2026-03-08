"""
PRD II (thoughts3): Null-Model and Rival-Theory Audit.

D(q) = Perf(q) - max_{b in baselines U nulls} Perf(b). No claim survives unless D > 0
out of sample with uncertainty bounds. Nulls: label permutations, random partitions,
matched-density random; rivals: ordinary baselines.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .harness import run_harness, score_J, random_partition_matched
from .greedy import greedy_coarse_graining
from .projection import single_block_partition, identity_partition
from .baselines import louvain_partition
from .phase_monitoring import partition_to_labels
from .labeled_harness import external_agreement


def _perf_neg_J(K: np.ndarray, mu: np.ndarray, partition: List[List[int]], alpha: float = 1.0, eta: float = 0.5) -> float:
    """Performance = -J(q) so higher is better."""
    _, _, J, _ = score_J(K, mu, partition, alpha=alpha, eta=eta)
    return -float(J)


def _rewire_preserve_row_sums(K: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Graph-structure null: preserve row sums (out-degree) but destroy structure.
    For each row, permute column indices so K_rewire has same marginals, different topology.
    """
    K = np.asarray(K)
    n = K.shape[0]
    K_out = np.zeros_like(K)
    for i in range(n):
        perm = rng.permutation(n)
        K_out[i, :] = K[i, perm]
    return K_out


def run_null_rival_audit(
    K: np.ndarray,
    mu: np.ndarray,
    labels: Optional[np.ndarray] = None,
    *,
    alpha: float = 1.0,
    eta: float = 0.5,
    n_random_null: int = 5,
    n_label_perm_null: int = 3,
    n_rewire_null: int = 3,
    rng: Optional[np.random.Generator] = None,
    use_external_perf: bool = True,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD II: Compute D = Perf(q*) - max(Perf(baselines), Perf(nulls)).
    Perf = -J(q) for internal; if labels given and use_external_perf, Perf = NMI to labels.
    Nulls: random partition (matched k), and if labels: label-permuted agreement.
    Pass: D > 0 (framework beats all baselines and nulls).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = K.shape[0]
    # Framework partition and baseline partitions
    q_star, _, _ = greedy_coarse_graining(K, mu)
    q_one = single_block_partition(n)
    q_singleton = identity_partition(n)
    q_louvain = louvain_partition(K)
    if q_louvain is None:
        q_louvain = q_singleton

    if use_external_perf and labels is not None:
        def perf(q: List[List[int]]) -> float:
            ag = external_agreement(q, labels, n)
            return ag["nmi"]  # higher better
    else:
        def perf(q: List[List[int]]) -> float:
            return _perf_neg_J(K, mu, q, alpha=alpha, eta=eta)

    perf_star = perf(q_star)
    rival_perfs: List[float] = [
        perf(q_one),
        perf(q_singleton),
        perf(q_louvain),
    ]
    # Null: random partitions matched to q_star block count
    k_star = len(q_star)
    for _ in range(n_random_null):
        q_rand = random_partition_matched(n, max(1, min(k_star, n)), rng)
        rival_perfs.append(perf(q_rand))
    # Null: label permutation (only when using external perf)
    if use_external_perf and labels is not None and n_label_perm_null > 0:
        labels_flat = np.asarray(labels).ravel()[:n]
        for _ in range(n_label_perm_null):
            perm = rng.permutation(len(labels_flat))
            labels_perm = labels_flat[perm]
            # Agreement of q_star with permuted labels is a null (should be ~ chance)
            ag = external_agreement(q_star, labels_perm, n)
            rival_perfs.append(ag["nmi"])
    # Null: graph-structure null — row-sum-preserving rewire (destroy structure, keep marginals)
    if n_rewire_null > 0:
        for _ in range(n_rewire_null):
            K_rewire = _rewire_preserve_row_sums(K, rng)
            q_rewire, _, _ = greedy_coarse_graining(K_rewire, mu)
            rival_perfs.append(perf(q_rewire))

    max_rival = max(rival_perfs)
    D = perf_star - max_rival
    pass_ = D > 0
    result = {
        "perf_star": perf_star,
        "max_baseline_or_null": max_rival,
        "D": D,
        "n_rivals": len(rival_perfs),
        "pass": pass_,
    }
    return result, pass_


def run_null_rival_audit_bootstrap(
    K: np.ndarray,
    mu: np.ndarray,
    labels: Optional[np.ndarray] = None,
    *,
    n_bootstrap: int = 10,
    rng: Optional[np.random.Generator] = None,
    ci_lower_bound_required: float = 0.0,
) -> Tuple[Dict[str, Any], bool]:
    """
    Run null-rival audit with bootstrap: resample units (rows of K/mu) or use same K with different
    null draws; report D and CI. Pass if lower bound of CI(D) > ci_lower_bound_required.
    Simplified: we resample null draws only (same K, multiple audit runs with different rng state).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    D_list: List[float] = []
    for i in range(n_bootstrap):
        rng_i = np.random.default_rng(rng.integers(0, 2**31))
        res, _ = run_null_rival_audit(K, mu, labels, n_random_null=5, n_label_perm_null=2, n_rewire_null=3, rng=rng_i)
        D_list.append(res["D"])
    D_arr = np.array(D_list)
    mean_D = float(np.mean(D_arr))
    std_D = float(np.std(D_arr)) if len(D_arr) > 1 else 0.0
    lb = float(np.percentile(D_arr, 2.5)) if len(D_arr) >= 4 else mean_D - 1.96 * std_D
    ub = float(np.percentile(D_arr, 97.5)) if len(D_arr) >= 4 else mean_D + 1.96 * std_D
    pass_ = lb > ci_lower_bound_required
    return {
        "mean_D": mean_D,
        "std_D": std_D,
        "ci_lower": lb,
        "ci_upper": ub,
        "n_bootstrap": n_bootstrap,
    }, pass_
