#!/usr/bin/env python3
"""
PRD-30: Organizational Design Mapping Validation.

Runs a boundary+governance mapping audit on public organization-like graph data.
Produces required outputs:
  - organizational_design_map_report.md
  - boundary_leaderboard.csv
  - external_agreement_report.md
  - stress_robustness_report.md
  - null_rival_audit_report.md
  - governance_preservation_report.md
  - temporal_drift_report.md
  - organizational_map_summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.baselines import louvain_partition, spectral_partition
from boundary_org.estimators import binding_index
from boundary_org.governance_metrics import ChallengeEvent, run_governance_metrics
from boundary_org.governance_stress import perturb_kernel_missingness, perturb_kernel_noise, perturb_kernel_scale_rows
from boundary_org.harness import random_partition_matched
from boundary_org.incident_phase_monitoring import run_incident_phase_monitoring
from boundary_org.labeled_harness import external_agreement
from boundary_org.operators import closure_energy
from boundary_org.projection import identity_partition, single_block_partition


@dataclass(frozen=True)
class PartitionEval:
    name: str
    category: str
    n_blocks: int
    block_balance: float
    E_cl: float
    E_rob_proxy: float
    delta_otimes_proxy: Optional[float]
    delta_gov_proxy: float
    E_lg: float
    nmi: float
    ari: float
    macro_f1: float
    contestability_proxy: float
    responsibility_residue: float


def _row_stochastic(K: np.ndarray) -> np.ndarray:
    K = np.asarray(K, dtype=np.float64)
    row_sums = K.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return K / row_sums


def _load_public_kernel(npz_path: Path, max_nodes: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    data = np.load(npz_path, allow_pickle=False)
    K = np.asarray(data["K"], dtype=np.float64)
    labels = np.asarray(data["labels"], dtype=np.int64) if "labels" in data else np.full(K.shape[0], -1, dtype=np.int64)
    if "mu" in data:
        mu = np.asarray(data["mu"], dtype=np.float64)
        mu = np.where(mu > 0, mu, 0.0)
        mu = mu / np.sum(mu) if np.sum(mu) > 0 else np.ones(K.shape[0], dtype=np.float64) / K.shape[0]
    else:
        mu = np.ones(K.shape[0], dtype=np.float64) / K.shape[0]

    n0 = int(K.shape[0])
    if max_nodes > 0 and max_nodes < n0:
        degree = np.asarray(K).sum(axis=1)
        keep = np.argsort(-degree)[:max_nodes]
        keep = np.sort(keep)
        K = K[np.ix_(keep, keep)]
        labels = labels[keep]
        mu = mu[keep]
        mu = mu / np.sum(mu)

    K = _row_stochastic(K)
    info = {
        "dataset_npz": str(npz_path.resolve()),
        "n": int(K.shape[0]),
        "n_original": n0,
        "n_labels": int(np.unique(labels[labels >= 0]).size),
    }
    return K, mu, labels, info


def _block_balance(partition: Sequence[Sequence[int]], n: int) -> float:
    """Normalized entropy of block sizes in [0,1], higher = more balanced."""
    k = len(partition)
    if k <= 1 or n <= 1:
        return 0.0
    sizes = np.array([len(b) for b in partition], dtype=np.float64)
    p = sizes / np.sum(sizes)
    ent = -float(np.sum(p * np.log(p + 1e-20)))
    denom = float(np.log(k))
    return ent / denom if denom > 0 else 0.0


def _partition_map(partition: Sequence[Sequence[int]], n: int) -> np.ndarray:
    block = np.full(n, -1, dtype=np.int64)
    for b, nodes in enumerate(partition):
        for i in nodes:
            block[int(i)] = b
    return block


def _restrict_partition(partition: Sequence[Sequence[int]], keep_idx: np.ndarray) -> List[List[int]]:
    """Restrict partition to kept original nodes and remap to 0..len(keep_idx)-1."""
    idx_map = {int(orig): i for i, orig in enumerate(keep_idx.tolist())}
    out: List[List[int]] = []
    for block in partition:
        mapped = [idx_map[int(node)] for node in block if int(node) in idx_map]
        if mapped:
            out.append(mapped)
    if not out:
        return [list(range(len(keep_idx)))]
    return out


def _block_transition_matrix(K: np.ndarray, mu: np.ndarray, partition: Sequence[Sequence[int]]) -> np.ndarray:
    """Quotient transition matrix on blocks."""
    n_blocks = len(partition)
    block_id = _partition_map(partition, K.shape[0])
    B = np.zeros((n_blocks, n_blocks), dtype=np.float64)
    for a in range(n_blocks):
        idx_a = np.where(block_id == a)[0]
        if idx_a.size == 0:
            continue
        mass_a = float(np.sum(mu[idx_a]))
        if mass_a <= 0:
            continue
        mu_a = mu[idx_a]
        for b in range(n_blocks):
            idx_b = np.where(block_id == b)[0]
            if idx_b.size == 0:
                continue
            B[a, b] = float(np.sum(mu_a[:, None] * K[np.ix_(idx_a, idx_b)]) / mass_a)
    B = np.where(B > 0, B, 0.0)
    row = B.sum(axis=1, keepdims=True)
    row = np.where(row > 0, row, 1.0)
    return B / row


def _governance_proxies(
    K: np.ndarray,
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
    *,
    edge_eps: float = 1e-6,
    max_events: int = 5000,
    reverse_ratio_threshold: float = 0.8,
) -> Dict[str, float]:
    """
    Structural governance proxies from block-level transitions.
    Uses run_governance_metrics on synthetic challenge events induced by quotient links.
    """
    B = _block_transition_matrix(K, mu, partition)
    n_blocks = B.shape[0]
    edge_rows: List[Tuple[float, int, int]] = []
    for a in range(n_blocks):
        for b in range(n_blocks):
            if a == b:
                continue
            w_ab = float(B[a, b])
            if w_ab > edge_eps:
                edge_rows.append((w_ab, a, b))
    edge_rows.sort(reverse=True)
    if max_events > 0 and len(edge_rows) > max_events:
        edge_rows = edge_rows[:max_events]

    events: List[ChallengeEvent] = []
    t = 0.0
    for w_ab, a, b in edge_rows:
        reverse_weight = float(B[b, a])
        # Dense graphs can make every pair weakly bidirectional. Require meaningful reverse support.
        reversed_ = reverse_weight >= max(edge_eps, reverse_ratio_threshold * w_ab)
        outcome = "reversed" if reversed_ else "denied"
        latency = float(1.0 / max(w_ab, 1e-6))
        events.append(
            ChallengeEvent(
                challenge_id=f"{a}->{b}",
                timestamp_challenge=t,
                timestamp_resolution=t + latency,
                outcome=outcome,
                attributable_agent=f"block_{a}",
            )
        )
        t += 1.0

    metrics, _ = run_governance_metrics(events)
    reversal = float(metrics.get("reversal_success", 0.0))
    unresolved = float(metrics.get("unresolved_challenge_rate", 1.0))
    unattributed = float(metrics.get("unattributed_residue", 1.0))
    contestability = float(metrics.get("chi_proxy", {}).get("reversibility", 0.0))

    capacity = float(np.clip(np.mean([reversal, 1.0 - unresolved, 1.0 - unattributed]), 0.0, 1.0))
    delta_gov_proxy = 1.0 - capacity
    responsibility_residue = unattributed
    return {
        "contestability_proxy": contestability,
        "reversal_success": reversal,
        "unresolved_rate": unresolved,
        "responsibility_residue": responsibility_residue,
        "governance_capacity": capacity,
        "delta_gov_proxy": delta_gov_proxy,
        "n_challenge_events": float(len(events)),
    }


def _robust_closure_proxy(
    K: np.ndarray,
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
    *,
    n_trials: int,
    rng: np.random.Generator,
) -> float:
    """Proxy for E_rob: max closure energy under mild perturbation families."""
    vals: List[float] = []
    for _ in range(n_trials):
        K_n = perturb_kernel_noise(K, 0.05, rng)
        vals.append(float(closure_energy(K_n, mu, partition)))
        K_m = perturb_kernel_missingness(K, 0.10, rng)
        vals.append(float(closure_energy(K_m, mu, partition)))
        K_s = perturb_kernel_scale_rows(K, (0.8, 1.2), rng)
        vals.append(float(closure_energy(K_s, mu, partition)))
    return float(max(vals)) if vals else float(closure_energy(K, mu, partition))


def _degree_median_partition(K: np.ndarray) -> List[List[int]]:
    deg = np.asarray(K).sum(axis=1)
    med = float(np.median(deg))
    left = [int(i) for i in np.where(deg <= med)[0]]
    right = [int(i) for i in np.where(deg > med)[0]]
    if len(left) == 0 or len(right) == 0:
        n = K.shape[0]
        half = max(1, n // 2)
        left = list(range(half))
        right = list(range(half, n))
    return [left, right]


def _label_frequency_partition(labels: np.ndarray, n: int) -> Optional[List[List[int]]]:
    valid = np.asarray(labels).ravel()[:n]
    mask = valid >= 0
    if not np.any(mask):
        return None
    vals, counts = np.unique(valid[mask], return_counts=True)
    major = int(vals[int(np.argmax(counts))])
    left = [int(i) for i in range(n) if valid[i] == major]
    right = [int(i) for i in range(n) if valid[i] != major]
    if not left or not right:
        return None
    return [left, right]


def _leiden_partition_or_none(K: np.ndarray) -> Optional[List[List[int]]]:
    """
    Optional Leiden baseline. Returns None if dependency unavailable.
    """
    try:
        import igraph as ig
        import leidenalg as la
    except Exception:
        return None
    A = (np.asarray(K) + np.asarray(K).T) / 2.0
    n = A.shape[0]
    g = ig.Graph()
    g.add_vertices(n)
    edges = []
    weights = []
    for i in range(n):
        for j in range(i + 1, n):
            w = float(A[i, j])
            if w > 0:
                edges.append((i, j))
                weights.append(w)
    if not edges:
        return [list(range(n))]
    g.add_edges(edges)
    g.es["weight"] = weights
    part = la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight", seed=42)
    blocks: List[List[int]] = []
    for comm in part:
        blocks.append(sorted(int(x) for x in comm))
    return blocks if blocks else [list(range(n))]


def _rewire_preserve_row_sums(K: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    K = np.asarray(K)
    n = K.shape[0]
    K_out = np.zeros_like(K)
    for i in range(n):
        perm = rng.permutation(n)
        K_out[i, :] = K[i, perm]
    return K_out


def _spectral_split_block(K: np.ndarray, block: Sequence[int], min_block_size: int) -> Optional[Tuple[List[int], List[int]]]:
    idx = np.asarray(block, dtype=np.int64)
    if idx.size < max(2 * min_block_size, 4):
        return None
    K_sub = K[np.ix_(idx, idx)]
    q_sub = spectral_partition(K_sub)
    if len(q_sub) != 2:
        return None
    left = [int(idx[i]) for i in q_sub[0]]
    right = [int(idx[i]) for i in q_sub[1]]
    if len(left) < min_block_size or len(right) < min_block_size:
        return None
    return (left, right)


def _partition_eval(
    *,
    name: str,
    category: str,
    partition: List[List[int]],
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    beta1: float,
    beta2: float,
    rng: np.random.Generator,
    robust_trials: int,
    compute_robust: bool,
    governance_max_events: int,
) -> PartitionEval:
    n = K.shape[0]
    E_cl = float(closure_energy(K, mu, partition))
    E_rob_proxy = (
        _robust_closure_proxy(K, mu, partition, n_trials=robust_trials, rng=rng)
        if compute_robust
        else E_cl
    )
    b_ind = float(binding_index(K, mu, partition)) if len(partition) >= 3 else float("nan")
    delta_otimes_proxy = (1.0 - b_ind) if np.isfinite(b_ind) else None

    gov = _governance_proxies(K, mu, partition, max_events=governance_max_events)
    delta_gov_proxy = float(gov["delta_gov_proxy"])
    E_lg = float(beta1 * E_cl + beta2 * (delta_gov_proxy**2))
    ag = external_agreement(partition, labels, n)
    return PartitionEval(
        name=name,
        category=category,
        n_blocks=len(partition),
        block_balance=_block_balance(partition, n),
        E_cl=E_cl,
        E_rob_proxy=E_rob_proxy,
        delta_otimes_proxy=delta_otimes_proxy,
        delta_gov_proxy=delta_gov_proxy,
        E_lg=E_lg,
        nmi=float(ag.get("nmi", 0.0)),
        ari=float(ag.get("ari", 0.0)),
        macro_f1=float(ag.get("macro_f1", 0.0)),
        contestability_proxy=float(gov["contestability_proxy"]),
        responsibility_residue=float(gov["responsibility_residue"]),
    )


def _framework_partition_search(
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    *,
    beta1: float,
    beta2: float,
    rng: np.random.Generator,
    max_splits: int,
    min_block_size: int,
    min_improvement: float,
    robust_trials: int,
    governance_max_events: int,
) -> Tuple[List[List[int]], PartitionEval, List[Dict[str, Any]]]:
    """
    Greedy split search on E_lg from spectral seed.
    This is bounded and laptop-safe while keeping the same objective surface.
    """
    q = spectral_partition(K)
    current = _partition_eval(
        name="q_star",
        category="framework",
        partition=q,
        K=K,
        mu=mu,
        labels=labels,
        beta1=beta1,
        beta2=beta2,
        rng=rng,
        robust_trials=robust_trials,
        compute_robust=False,
        governance_max_events=governance_max_events,
    )
    trace: List[Dict[str, Any]] = [
        {
            "step": 0,
            "action": "seed_spectral",
            "n_blocks": len(q),
            "E_lg": current.E_lg,
        }
    ]

    for step in range(1, max_splits + 1):
        best_q: Optional[List[List[int]]] = None
        best_eval: Optional[PartitionEval] = None
        best_delta = 0.0
        best_block = -1

        for b_idx, block in enumerate(q):
            split = _spectral_split_block(K, block, min_block_size=min_block_size)
            if split is None:
                continue
            left, right = split
            cand = [list(bl) for i, bl in enumerate(q) if i != b_idx]
            cand.append(left)
            cand.append(right)
            cand_eval = _partition_eval(
                name="q_star",
                category="framework",
                partition=cand,
                K=K,
                mu=mu,
                labels=labels,
                beta1=beta1,
                beta2=beta2,
                rng=rng,
                robust_trials=robust_trials,
                compute_robust=False,
                governance_max_events=governance_max_events,
            )
            delta = current.E_lg - cand_eval.E_lg
            if delta > best_delta:
                best_delta = delta
                best_q = cand
                best_eval = cand_eval
                best_block = b_idx

        if best_q is None or best_eval is None or best_delta < min_improvement:
            trace.append(
                {
                    "step": step,
                    "action": "stop_no_improving_split",
                    "n_blocks": len(q),
                    "E_lg": current.E_lg,
                }
            )
            break

        q = best_q
        current = best_eval
        trace.append(
            {
                "step": step,
                "action": f"split_block_{best_block}",
                "n_blocks": len(q),
                "E_lg": current.E_lg,
                "delta": best_delta,
            }
        )

    return q, current, trace


def _permutation_external_pvals(
    q_star: List[List[int]],
    labels: np.ndarray,
    n: int,
    *,
    n_perm: int,
    rng: np.random.Generator,
) -> Dict[str, float]:
    star = external_agreement(q_star, labels, n)
    nmi_star = float(star.get("nmi", 0.0))
    ari_star = float(star.get("ari", 0.0))
    f1_star = float(star.get("macro_f1", 0.0))
    null_nmi: List[float] = []
    null_ari: List[float] = []
    null_f1: List[float] = []
    labels_flat = np.asarray(labels).ravel()[:n]
    for _ in range(n_perm):
        perm = rng.permutation(len(labels_flat))
        lp = labels_flat[perm]
        ag = external_agreement(q_star, lp, n)
        null_nmi.append(float(ag.get("nmi", 0.0)))
        null_ari.append(float(ag.get("ari", 0.0)))
        null_f1.append(float(ag.get("macro_f1", 0.0)))
    return {
        "nmi_star": nmi_star,
        "ari_star": ari_star,
        "f1_star": f1_star,
        "nmi_p_value": float(np.mean(np.array(null_nmi) >= nmi_star)) if null_nmi else 1.0,
        "ari_p_value": float(np.mean(np.array(null_ari) >= ari_star)) if null_ari else 1.0,
        "f1_p_value": float(np.mean(np.array(null_f1) >= f1_star)) if null_f1 else 1.0,
    }


def _edge_drop_perturbation(K: np.ndarray, drop_frac: float, rng: np.random.Generator) -> np.ndarray:
    K2 = np.asarray(K, dtype=np.float64).copy()
    n = K2.shape[0]
    triu = np.triu_indices(n, 1)
    n_edges = triu[0].size
    n_drop = max(1, int(n_edges * drop_frac))
    idx = rng.choice(n_edges, size=n_drop, replace=False)
    i, j = triu[0][idx], triu[1][idx]
    K2[i, j] = 0.0
    K2[j, i] = 0.0
    K2 = np.maximum(K2, 1e-12)
    return _row_stochastic(K2)


def _kernel_subgraph(K: np.ndarray, mu: np.ndarray, labels: np.ndarray, keep_idx: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    K_sub = K[np.ix_(keep_idx, keep_idx)]
    K_sub = _row_stochastic(K_sub)
    mu_sub = mu[keep_idx].copy()
    mu_sub = mu_sub / np.sum(mu_sub)
    labels_sub = labels[keep_idx]
    return K_sub, mu_sub, labels_sub


def _stress_and_leverage_audit(
    *,
    q_star: List[List[int]],
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    beta1: float,
    beta2: float,
    rng: np.random.Generator,
    robust_trials: int,
    stability_threshold: float,
    leverage_ratio_threshold: float,
    n_random_node_trials: int,
    governance_max_events: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool, bool]:
    base_eval = _partition_eval(
        name="q_star",
        category="framework",
        partition=q_star,
        K=K,
        mu=mu,
        labels=labels,
        beta1=beta1,
        beta2=beta2,
        rng=rng,
        robust_trials=robust_trials,
        compute_robust=False,
        governance_max_events=governance_max_events,
    )

    records: List[Dict[str, Any]] = []

    def add_case(
        family: str,
        severity: float,
        K_case: np.ndarray,
        mu_case: np.ndarray,
        labels_case: np.ndarray,
        q_case: List[List[int]],
    ) -> None:
        ev = _partition_eval(
            name="q_star_case",
            category="stress",
            partition=q_case,
            K=K_case,
            mu=mu_case,
            labels=labels_case,
            beta1=beta1,
            beta2=beta2,
            rng=rng,
            robust_trials=robust_trials,
            compute_robust=False,
            governance_max_events=governance_max_events,
        )
        records.append(
            {
                "family": family,
                "severity": severity,
                "E_lg": ev.E_lg,
                "nmi": ev.nmi,
                "delta_E_lg_abs": abs(ev.E_lg - base_eval.E_lg),
                "delta_nmi_abs": abs(ev.nmi - base_eval.nmi),
                "n_blocks": ev.n_blocks,
            }
        )

    for eps in (0.02, 0.05):
        K_n = perturb_kernel_noise(K, eps, rng)
        add_case("noise", eps, K_n, mu, labels, q_star)

    for eps in (0.05, 0.10):
        K_m = perturb_kernel_missingness(K, eps, rng)
        add_case("missingness", eps, K_m, mu, labels, q_star)

    for hi in (1.1, 1.2):
        K_s = perturb_kernel_scale_rows(K, (2.0 - hi, hi), rng)
        add_case("workload_scale", hi, K_s, mu, labels, q_star)

    n = K.shape[0]
    degrees = np.asarray(K).sum(axis=1)
    for eps in (0.05, 0.10):
        for _ in range(n_random_node_trials):
            n_drop = max(1, int(n * eps))
            keep = np.sort(rng.choice(n, size=n - n_drop, replace=False))
            K_sub, mu_sub, labels_sub = _kernel_subgraph(K, mu, labels, keep)
            q_sub = _restrict_partition(q_star, keep)
            add_case("node_drop_random", eps, K_sub, mu_sub, labels_sub, q_sub)

        n_drop = max(1, int(n * eps))
        order = np.argsort(-degrees)
        keep = np.sort(np.array([i for i in range(n) if i not in set(order[:n_drop])], dtype=np.int64))
        K_sub, mu_sub, labels_sub = _kernel_subgraph(K, mu, labels, keep)
        q_sub = _restrict_partition(q_star, keep)
        add_case("node_drop_top_degree", eps, K_sub, mu_sub, labels_sub, q_sub)

    for eps in (0.05, 0.10):
        K_ed = _edge_drop_perturbation(K, eps, rng)
        add_case("edge_drop", eps, K_ed, mu, labels, q_star)

    deltas = np.array([float(r["delta_E_lg_abs"]) for r in records], dtype=np.float64)
    S_max = float(np.max(deltas)) if deltas.size else 0.0
    stable_fraction = float(np.mean(deltas <= stability_threshold)) if deltas.size else 1.0

    rand = np.array([float(r["delta_E_lg_abs"]) for r in records if r["family"] == "node_drop_random"], dtype=np.float64)
    topd = np.array([float(r["delta_E_lg_abs"]) for r in records if r["family"] == "node_drop_top_degree"], dtype=np.float64)
    rand_mean = float(np.mean(rand)) if rand.size else 0.0
    top_mean = float(np.mean(topd)) if topd.size else 0.0
    leverage_ratio = float(top_mean / (rand_mean + 1e-12)) if topd.size else 0.0

    stress_pass = bool(S_max <= stability_threshold)
    leverage_pass = bool(leverage_ratio <= leverage_ratio_threshold)

    summary = {
        "n_cases": int(len(records)),
        "S_max": S_max,
        "stability_threshold": float(stability_threshold),
        "stable_fraction": stable_fraction,
        "leverage_random_mean_delta": rand_mean,
        "leverage_top_degree_mean_delta": top_mean,
        "leverage_ratio": leverage_ratio,
        "leverage_ratio_threshold": float(leverage_ratio_threshold),
        "stress_pass": stress_pass,
        "leverage_pass": leverage_pass,
    }
    return records, summary, stress_pass, leverage_pass


def _bootstrap_null_dominance(
    *,
    q_star: List[List[int]],
    rival_partitions: Dict[str, List[List[int]]],
    labels: np.ndarray,
    n: int,
    n_bootstrap: int,
    rng: np.random.Generator,
) -> Dict[str, Any]:
    from sklearn.metrics import normalized_mutual_info_score

    labels_full = np.asarray(labels).ravel()[:n]
    labeled_idx = np.where(labels_full >= 0)[0]
    if labeled_idx.size == 0:
        return {
            "mean_D": 0.0,
            "std_D": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "n_bootstrap": n_bootstrap,
            "best_rival_name_full": None,
            "best_rival_nmi_full": 0.0,
            "star_nmi_full": 0.0,
            "pass": False,
        }

    true_lab = labels_full[labeled_idx]
    pred_star_full = _partition_map(q_star, n)[labeled_idx]
    pred_rivals = {name: _partition_map(part, n)[labeled_idx] for name, part in rival_partitions.items()}

    def _safe_nmi(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        if np.unique(y_true).size < 2 and np.unique(y_pred).size < 2:
            return 1.0 if np.array_equal(y_true, y_pred) else 0.0
        return float(normalized_mutual_info_score(y_true, y_pred, average_method="arithmetic"))

    star_full = _safe_nmi(true_lab, pred_star_full)
    rival_full = {name: _safe_nmi(true_lab, pred) for name, pred in pred_rivals.items()}
    if rival_full:
        best_rival_name_full = max(rival_full, key=lambda k: rival_full[k])
        best_rival_full = float(rival_full[best_rival_name_full])
    else:
        best_rival_name_full = None
        best_rival_full = 0.0

    D_samples: List[float] = []
    m = labeled_idx.size
    for _ in range(n_bootstrap):
        draw = rng.integers(0, m, size=m)
        y = true_lab[draw]
        star = _safe_nmi(y, pred_star_full[draw])
        if pred_rivals:
            rivals = [
                _safe_nmi(y, pred_rivals[name][draw])
                for name in pred_rivals
            ]
            max_rival = max(rivals)
        else:
            max_rival = 0.0
        D_samples.append(star - max_rival)

    D_arr = np.asarray(D_samples, dtype=np.float64)
    mean_D = float(np.mean(D_arr)) if D_arr.size else 0.0
    std_D = float(np.std(D_arr)) if D_arr.size else 0.0
    lb = float(np.percentile(D_arr, 2.5)) if D_arr.size else 0.0
    ub = float(np.percentile(D_arr, 97.5)) if D_arr.size else 0.0
    pass_ = bool(lb > 0.0 and (star_full - best_rival_full) > 0.0)

    return {
        "mean_D": mean_D,
        "std_D": std_D,
        "ci_lower": lb,
        "ci_upper": ub,
        "n_bootstrap": n_bootstrap,
        "best_rival_name_full": best_rival_name_full,
        "best_rival_nmi_full": best_rival_full,
        "star_nmi_full": star_full,
        "pass": pass_,
    }


def _write_boundary_leaderboard(path: Path, rows: List[PartitionEval]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "category",
                "n_blocks",
                "block_balance",
                "E_cl",
                "E_rob_proxy",
                "delta_otimes_proxy",
                "delta_gov_proxy",
                "E_lg",
                "nmi",
                "ari",
                "macro_f1",
                "contestability_proxy",
                "responsibility_residue",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "name": r.name,
                    "category": r.category,
                    "n_blocks": r.n_blocks,
                    "block_balance": f"{r.block_balance:.6f}",
                    "E_cl": f"{r.E_cl:.10f}",
                    "E_rob_proxy": f"{r.E_rob_proxy:.10f}",
                    "delta_otimes_proxy": "" if r.delta_otimes_proxy is None else f"{r.delta_otimes_proxy:.10f}",
                    "delta_gov_proxy": f"{r.delta_gov_proxy:.10f}",
                    "E_lg": f"{r.E_lg:.10f}",
                    "nmi": f"{r.nmi:.6f}",
                    "ari": f"{r.ari:.6f}",
                    "macro_f1": f"{r.macro_f1:.6f}",
                    "contestability_proxy": f"{r.contestability_proxy:.6f}",
                    "responsibility_residue": f"{r.responsibility_residue:.6f}",
                }
            )


def _write_md(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-30: organizational design mapping validation on public graph data.")
    ap.add_argument(
        "--dataset-npz",
        type=Path,
        default=ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz",
    )
    ap.add_argument(
        "--temporal-dataset-dir",
        type=Path,
        default=ROOT / "data" / "processed" / "email_eu_core_temporal",
        help="Optional directory containing temporal window npz files.",
    )
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs")
    ap.add_argument("--max-nodes", type=int, default=200)
    ap.add_argument("--n-random", type=int, default=24, help="Random matched partitions (null world).")
    ap.add_argument("--n-rewire", type=int, default=12, help="Degree-preserving rewired null worlds.")
    ap.add_argument("--n-permutations", type=int, default=200)
    ap.add_argument("--n-bootstrap", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--beta1", type=float, default=1.0, help="Weight for E_cl in E_lg objective.")
    ap.add_argument("--beta2", type=float, default=1.0, help="Weight for delta_gov^2 in E_lg objective.")
    ap.add_argument("--robust-trials", type=int, default=2)
    ap.add_argument("--framework-max-splits", type=int, default=6)
    ap.add_argument("--framework-min-block-size", type=int, default=6)
    ap.add_argument("--framework-min-improvement", type=float, default=1e-4)
    ap.add_argument("--governance-max-events", type=int, default=5000)
    ap.add_argument("--stability-threshold", type=float, default=0.20)
    ap.add_argument("--leverage-ratio-threshold", type=float, default=2.0)
    args = ap.parse_args()

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    K, mu, labels, info = _load_public_kernel(args.dataset_npz.resolve(), max_nodes=args.max_nodes)
    n = K.shape[0]

    # Framework partition search (bounded, objective-aligned).
    q_star, q_star_eval_seed, framework_trace = _framework_partition_search(
        K,
        mu,
        labels,
        beta1=args.beta1,
        beta2=args.beta2,
        rng=rng,
        max_splits=args.framework_max_splits,
        min_block_size=args.framework_min_block_size,
        min_improvement=args.framework_min_improvement,
        robust_trials=args.robust_trials,
        governance_max_events=args.governance_max_events,
    )

    parts: List[Tuple[str, str, List[List[int]]]] = [
        ("q_star", "framework", q_star),
        ("one_block", "trivial", single_block_partition(n)),
        ("singleton", "trivial", identity_partition(n)),
        ("spectral", "graph_baseline", spectral_partition(K)),
        ("degree_median", "stat_baseline", _degree_median_partition(K)),
    ]

    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        parts.append(("louvain", "graph_baseline", q_louvain))

    q_leiden = _leiden_partition_or_none(K)
    if q_leiden is not None:
        parts.append(("leiden", "graph_baseline", q_leiden))

    q_label_freq = _label_frequency_partition(labels, n)
    if q_label_freq is not None:
        parts.append(("label_frequency", "stat_baseline", q_label_freq))

    k_star = max(2, len(q_star))
    for i in range(args.n_random):
        q_rand = random_partition_matched(n, min(k_star, n), rng)
        parts.append((f"random_{i}", "random_null", q_rand))

    for i in range(args.n_rewire):
        K_rw = _rewire_preserve_row_sums(K, rng)
        q_rw = spectral_partition(K_rw)
        parts.append((f"rewire_spectral_{i}", "null_world_rewire", q_rw))

    rows: List[PartitionEval] = []
    for name, category, q in parts:
        rows.append(
            _partition_eval(
                name=name,
                category=category,
                partition=q,
                K=K,
                mu=mu,
                labels=labels,
                beta1=args.beta1,
                beta2=args.beta2,
                rng=rng,
                robust_trials=args.robust_trials,
                compute_robust=(name == "q_star"),
                governance_max_events=args.governance_max_events,
            )
        )
    rows_sorted = sorted(rows, key=lambda r: r.E_lg)

    by_name = {r.name: r for r in rows}
    q_row = by_name["q_star"]
    baseline_rows = [r for r in rows if r.name != "q_star" and r.category in {"trivial", "graph_baseline", "stat_baseline"}]
    random_rows = [r for r in rows if r.category == "random_null"]

    best_baseline_by_E_lg = min(baseline_rows, key=lambda r: r.E_lg) if baseline_rows else None
    best_baseline_by_nmi = max(baseline_rows, key=lambda r: r.nmi) if baseline_rows else None

    perm = _permutation_external_pvals(q_star, labels, n, n_perm=args.n_permutations, rng=rng)

    stress_records, stress_summary, stress_pass, leverage_pass = _stress_and_leverage_audit(
        q_star=q_star,
        K=K,
        mu=mu,
        labels=labels,
        beta1=args.beta1,
        beta2=args.beta2,
        rng=rng,
        robust_trials=args.robust_trials,
        stability_threshold=args.stability_threshold,
        leverage_ratio_threshold=args.leverage_ratio_threshold,
        n_random_node_trials=2,
        governance_max_events=args.governance_max_events,
    )

    rival_partitions = {
        name: q
        for name, category, q in parts
        if name != "q_star" and category in {"trivial", "graph_baseline", "stat_baseline", "random_null", "null_world_rewire"}
    }
    null_result = _bootstrap_null_dominance(
        q_star=q_star,
        rival_partitions=rival_partitions,
        labels=labels,
        n=n,
        n_bootstrap=args.n_bootstrap,
        rng=rng,
    )
    null_pass = bool(null_result["pass"] and perm["nmi_p_value"] <= 0.05)

    gov_q = _governance_proxies(K, mu, q_star, max_events=args.governance_max_events)
    gov_one = _governance_proxies(K, mu, single_block_partition(n), max_events=args.governance_max_events)
    if random_rows:
        rand_cap = []
        for rr in random_rows:
            q = next(q for nm, _cat, q in parts if nm == rr.name)
            rand_cap.append(_governance_proxies(K, mu, q, max_events=args.governance_max_events)["governance_capacity"])
        gov_random_capacity_mean = float(np.mean(rand_cap))
    else:
        gov_random_capacity_mean = 0.0
    governance_preservation_pass = bool(
        gov_q["governance_capacity"] > gov_one["governance_capacity"]
        and gov_q["governance_capacity"] >= gov_random_capacity_mean
    )

    temporal_dir = args.temporal_dataset_dir.resolve()
    temporal_status = "not_run_missing_dataset"
    temporal_pass: Optional[bool] = None
    temporal_payload: Dict[str, Any] = {}
    if temporal_dir.exists() and temporal_dir.is_dir():
        npz_files = sorted(temporal_dir.glob("*.npz"))
        kernels: List[Tuple[np.ndarray, np.ndarray]] = []
        for p in npz_files:
            d = np.load(p, allow_pickle=False)
            if "K" not in d:
                continue
            Kt = _row_stochastic(np.asarray(d["K"], dtype=np.float64))
            if "mu" in d:
                mut = np.asarray(d["mu"], dtype=np.float64)
                mut = np.where(mut > 0, mut, 0.0)
                mut = mut / np.sum(mut) if np.sum(mut) > 0 else np.ones(Kt.shape[0]) / Kt.shape[0]
            else:
                mut = np.ones(Kt.shape[0]) / Kt.shape[0]
            kernels.append((Kt, mut))
        if len(kernels) >= 3:
            incident_steps = [max(1, len(kernels) // 2), len(kernels) - 1]
            temporal_payload, temporal_pass_flag = run_incident_phase_monitoring(
                kernels,
                incident_steps,
                abrupt_nmi_threshold=0.8,
                rising_window=2,
                fp_window=2,
                drift_quantile_threshold=0.9,
            )
            temporal_pass = bool(temporal_pass_flag)
            temporal_status = "run"
        else:
            temporal_status = "missing_windows"

    nontrivial = bool(
        q_row.n_blocks >= 2
        and q_row.n_blocks <= max(2, int(0.8 * n))
        and q_row.block_balance >= 0.05
    )
    beats_trivial_random = bool(
        q_row.E_lg < by_name["one_block"].E_lg
        and q_row.E_lg < by_name["singleton"].E_lg
        and (q_row.E_lg < float(np.mean([r.E_lg for r in random_rows])) if random_rows else True)
    )
    external_alignment_pass = bool(
        best_baseline_by_nmi is not None
        and q_row.nmi > best_baseline_by_nmi.nmi
        and perm["nmi_p_value"] <= 0.05
    )
    stress_pass_total = bool(stress_pass and leverage_pass)
    null_pass_total = bool(null_pass)
    governance_pass = governance_preservation_pass
    temporal_ok = bool(temporal_pass) if temporal_pass is not None else False

    all_acceptance = bool(
        nontrivial
        and beats_trivial_random
        and external_alignment_pass
        and stress_pass_total
        and null_pass_total
        and governance_pass
        and temporal_ok
    )

    claim_unlocked = all_acceptance
    decision = "PASS" if all_acceptance else "FAIL"

    leaderboard_csv = out_dir / "boundary_leaderboard.csv"
    _write_boundary_leaderboard(leaderboard_csv, rows_sorted)

    _write_md(
        out_dir / "external_agreement_report.md",
        [
            "# External Agreement Report",
            "",
            f"- Dataset: `{info['dataset_npz']}`",
            f"- n: `{n}`",
            "",
            "| Candidate | NMI | ARI | macro-F1 |",
            "|---|---:|---:|---:|",
            *[
                f"| {r.name} | {r.nmi:.4f} | {r.ari:.4f} | {r.macro_f1:.4f} |"
                for r in sorted(rows, key=lambda x: x.nmi, reverse=True)
            ],
            "",
            "## Chance-comparison (q_star vs permuted labels)",
            f"- NMI p-value: `{perm['nmi_p_value']:.4f}`",
            f"- ARI p-value: `{perm['ari_p_value']:.4f}`",
            f"- macro-F1 p-value: `{perm['f1_p_value']:.4f}`",
            "",
            f"Pass criterion status: `{external_alignment_pass}`",
            "Fail condition: no better than baseline or null-equivalent.",
        ],
    )

    _write_md(
        out_dir / "stress_robustness_report.md",
        [
            "# Stress Robustness Report",
            "",
            f"- S_max (|delta E_lg|): `{stress_summary['S_max']:.6f}`",
            f"- stability threshold: `{stress_summary['stability_threshold']:.6f}`",
            f"- stable_fraction: `{stress_summary['stable_fraction']:.4f}`",
            f"- stress pass: `{stress_pass}`",
            "",
            "## Leverage sensitivity",
            f"- random drop mean delta: `{stress_summary['leverage_random_mean_delta']:.6f}`",
            f"- top-degree drop mean delta: `{stress_summary['leverage_top_degree_mean_delta']:.6f}`",
            f"- leverage ratio: `{stress_summary['leverage_ratio']:.4f}`",
            f"- leverage ratio threshold: `{stress_summary['leverage_ratio_threshold']:.4f}`",
            f"- leverage pass: `{leverage_pass}`",
            "",
            f"Combined stress pass: `{stress_pass_total}`",
            "",
            "Fail condition: high leverage sensitivity or unstable boundary under mild perturbation.",
        ],
    )

    _write_md(
        out_dir / "null_rival_audit_report.md",
        [
            "# Null/Rival Audit Report",
            "",
            f"- star_nmi_full: `{null_result['star_nmi_full']:.6f}`",
            f"- best_rival_name_full: `{null_result['best_rival_name_full']}`",
            f"- best_rival_nmi_full: `{null_result['best_rival_nmi_full']:.6f}`",
            f"- mean_D: `{null_result['mean_D']:.6f}`",
            f"- std_D: `{null_result['std_D']:.6f}`",
            f"- ci_lower: `{null_result['ci_lower']:.6f}`",
            f"- ci_upper: `{null_result['ci_upper']:.6f}`",
            f"- n_bootstrap: `{null_result['n_bootstrap']}`",
            f"- permutation null p(NMI): `{perm['nmi_p_value']:.6f}`",
            f"- pass (ci_lower > 0 and perm p<=0.05): `{null_pass}`",
            "",
            f"Pass criterion status: `{null_pass_total}`",
            "Fail condition: D <= 0 or CI lower bound <= 0 or permutation null not rejected.",
        ],
    )

    _write_md(
        out_dir / "governance_preservation_report.md",
        [
            "# Governance Preservation Report",
            "",
            "## q_star structural governance proxies",
            f"- contestability_proxy: `{gov_q['contestability_proxy']:.4f}`",
            f"- reversal_success: `{gov_q['reversal_success']:.4f}`",
            f"- unresolved_rate: `{gov_q['unresolved_rate']:.4f}`",
            f"- responsibility_residue: `{gov_q['responsibility_residue']:.4f}`",
            f"- governance_capacity: `{gov_q['governance_capacity']:.4f}`",
            f"- delta_gov_proxy: `{gov_q['delta_gov_proxy']:.4f}`",
            "",
            "## Comparators",
            f"- one_block governance_capacity: `{gov_one['governance_capacity']:.4f}`",
            f"- random_matched mean governance_capacity: `{gov_random_capacity_mean:.4f}`",
            "",
            f"Governance preservation pass: `{governance_pass}`",
            "",
            "Note: these are structural proxies for governance observables, not final institutional metrics.",
        ],
    )

    if temporal_status == "run":
        _write_md(
            out_dir / "temporal_drift_report.md",
            [
                "# Temporal Drift Report",
                "",
                f"- status: `{temporal_status}`",
                f"- pass: `{temporal_pass}`",
                f"- phase_alert_steps: `{temporal_payload.get('phase_alert_steps', [])}`",
                f"- baseline_alerts: `{temporal_payload.get('baseline_alerts', {})}`",
                f"- median_lead_time_phase: `{temporal_payload.get('median_lead_time_phase', 0.0)}`",
                f"- fp_rate_phase: `{temporal_payload.get('fp_rate_phase', 0.0)}`",
            ],
        )
    else:
        _write_md(
            out_dir / "temporal_drift_report.md",
            [
                "# Temporal Drift Report",
                "",
                f"- status: `{temporal_status}`",
                "- temporal public dataset is not available in this workspace run.",
                "- result classification: incomplete (cannot satisfy temporal acceptance criterion).",
            ],
        )

    _write_md(
        out_dir / "organizational_design_map_report.md",
        [
            "# Organizational Design Mapping Report",
            "",
            "## Boundary map",
            f"- q_star blocks: `{q_row.n_blocks}`",
            f"- q_star block_balance: `{q_row.block_balance:.4f}`",
            "",
            "## Boundary report R(q*)",
            f"- E_cl(q*): `{q_row.E_cl:.8f}`",
            f"- E_rob(q*) proxy: `{q_row.E_rob_proxy:.8f}`",
            f"- delta_otimes(q*) proxy: `{'NA' if q_row.delta_otimes_proxy is None else f'{q_row.delta_otimes_proxy:.8f}'}`",
            f"- delta_gov(q*) proxy: `{q_row.delta_gov_proxy:.8f}`",
            "",
            "## Test outcomes",
            f"- Test A nontrivial boundary: `{nontrivial}`",
            f"- Test B external agreement: `{external_alignment_pass}`",
            f"- Test C stress robustness: `{stress_pass_total}`",
            f"- Test D null/rival dominance: `{null_pass_total}`",
            f"- Test E temporal drift: `{temporal_ok}`",
            f"- Test F governance preservation: `{governance_pass}`",
            "",
            "## Acceptance",
            f"- all criteria satisfied: `{all_acceptance}`",
            f"- decision: `{decision}`",
            "",
            (
                "Claim status: mapping claim supported."
                if claim_unlocked
                else "Claim status: mapping claim NOT supported on current live public artifacts."
            ),
        ],
    )

    summary = {
        "dataset": info,
        "framework_search": {
            "trace": framework_trace,
            "seed_eval": {
                "n_blocks": q_star_eval_seed.n_blocks,
                "E_lg": q_star_eval_seed.E_lg,
            },
        },
        "q_star": {
            "name": q_row.name,
            "n_blocks": q_row.n_blocks,
            "block_balance": q_row.block_balance,
            "E_cl": q_row.E_cl,
            "E_rob_proxy": q_row.E_rob_proxy,
            "delta_otimes_proxy": q_row.delta_otimes_proxy,
            "delta_gov_proxy": q_row.delta_gov_proxy,
            "E_lg": q_row.E_lg,
            "nmi": q_row.nmi,
            "ari": q_row.ari,
            "macro_f1": q_row.macro_f1,
            "contestability_proxy": q_row.contestability_proxy,
            "responsibility_residue": q_row.responsibility_residue,
        },
        "best_baseline_E_lg": (
            None
            if best_baseline_by_E_lg is None
            else {
                "name": best_baseline_by_E_lg.name,
                "E_lg": best_baseline_by_E_lg.E_lg,
                "nmi": best_baseline_by_E_lg.nmi,
            }
        ),
        "tests": {
            "A_nontrivial_boundary": nontrivial,
            "B_external_agreement": external_alignment_pass,
            "C_stress_robustness": stress_pass_total,
            "D_null_rival_dominance": null_pass_total,
            "E_temporal_drift": temporal_ok,
            "F_governance_preservation": governance_pass,
        },
        "null_rival": null_result,
        "stress": {
            "summary": stress_summary,
            "records": stress_records,
        },
        "external_perm_p_values": perm,
        "temporal_status": temporal_status,
        "claim_unlocked": claim_unlocked,
        "decision": decision,
        "required_outputs": [
            "organizational_design_map_report.md",
            "boundary_leaderboard.csv",
            "external_agreement_report.md",
            "stress_robustness_report.md",
            "null_rival_audit_report.md",
            "governance_preservation_report.md",
            "temporal_drift_report.md",
            "organizational_map_summary.json",
        ],
    }
    (out_dir / "organizational_map_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))

    print(
        json.dumps(
            {
                "ok": True,
                "out_dir": str(out_dir),
                "decision": decision,
                "claim_unlocked": claim_unlocked,
                "q_star_n_blocks": q_row.n_blocks,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if claim_unlocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
