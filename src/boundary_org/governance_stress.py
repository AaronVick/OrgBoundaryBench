"""
Governance Stress Test Suite (PRD-18). Empirical Test Family B.

Perturbation families on (K, μ); recompute closure and block stability (NMI) under each.
Success: boundary remains near-optimal / stable under pre-registered perturbations.
Falsification: boundary degrades arbitrarily under small perturbations.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Sequence, Tuple

from .operators import closure_energy
from .greedy import greedy_coarse_graining
from .phase_monitoring import nmi_between_partitions


def perturb_kernel_noise(K: np.ndarray, strength: float, rng: np.random.Generator) -> np.ndarray:
    """PRD-18 §2.1: workload/input mix — add noise to kernel entries."""
    K = np.asarray(K, dtype=float).copy()
    n = K.shape[0]
    noise = rng.uniform(-strength, strength, (n, n))
    K = K + noise
    K = np.maximum(K, 1e-12)
    row_sums = K.sum(axis=1, keepdims=True)
    K = K / row_sums
    return K


def perturb_kernel_missingness(K: np.ndarray, frac_drop: float, rng: np.random.Generator) -> np.ndarray:
    """PRD-18 §2.1: missingness — zero out a fraction of (i,j) then renormalize."""
    K = np.asarray(K, dtype=float).copy()
    n = K.shape[0]
    mask = rng.random((n, n)) > frac_drop
    K = K * mask
    K = np.maximum(K, 1e-12)
    row_sums = K.sum(axis=1, keepdims=True)
    K = K / np.where(row_sums > 0, row_sums, 1.0)
    return K


def perturb_kernel_scale_rows(K: np.ndarray, scale_range: Tuple[float, float], rng: np.random.Generator) -> np.ndarray:
    """PRD-18 §2.1: workload intensity — scale rows (transition rates) then renormalize."""
    K = np.asarray(K, dtype=float).copy()
    n = K.shape[0]
    scales = rng.uniform(scale_range[0], scale_range[1], n)
    K = K * scales[:, np.newaxis]
    row_sums = K.sum(axis=1, keepdims=True)
    K = K / np.where(row_sums > 0, row_sums, 1.0)
    return K


def run_stress_test(
    K: np.ndarray,
    mu: np.ndarray,
    q_baseline: Sequence[Sequence[int]] | None = None,
    *,
    noise_strength: float = 0.05,
    missingness_frac: float = 0.1,
    scale_range: Tuple[float, float] = (0.8, 1.2),
    n_trials_per_family: int = 2,
    stability_nmi_min: float = 0.5,
    rng: np.random.Generator | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool]:
    """
    Run governance stress test (PRD-18): apply perturbation families, recompute E_cl and NMI.

    Returns (per_trial_results, summary, pass).
    pass: True iff in a majority of trials, NMI(q_baseline, q_perturbed) >= stability_nmi_min
    and E_cl on perturbed kernel with q_baseline does not explode (e.g. within 2x baseline E_cl).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = K.shape[0]
    if q_baseline is None:
        q_baseline, _, _ = greedy_coarse_graining(K, mu)
    q_baseline = list(q_baseline)
    E_cl_baseline = float(closure_energy(K, mu, q_baseline))

    trials: List[Dict[str, Any]] = []
    nmis: List[float] = []
    E_cl_ratios: List[float] = []

    def run_one(K_pert: np.ndarray, mu_pert: np.ndarray, family: str, trial_id: int) -> None:
        q_pert, _, _ = greedy_coarse_graining(K_pert, mu_pert)
        E_cl_pert_on_pert = float(closure_energy(K_pert, mu_pert, q_pert))
        E_cl_baseline_on_pert = float(closure_energy(K_pert, mu_pert, q_baseline))
        nmi = nmi_between_partitions(q_baseline, q_pert, n)
        nmis.append(nmi)
        ratio = E_cl_baseline_on_pert / (E_cl_baseline + 1e-20)
        E_cl_ratios.append(ratio)
        trials.append({
            "family": family,
            "trial": trial_id,
            "n_blocks_pert": len(q_pert),
            "E_cl_pert": E_cl_pert_on_pert,
            "E_cl_baseline_on_pert": E_cl_baseline_on_pert,
            "nmi": nmi,
        })

    for t in range(n_trials_per_family):
        K_n = perturb_kernel_noise(K, noise_strength, rng)
        run_one(K_n, mu, "noise", t)
    for t in range(n_trials_per_family):
        K_m = perturb_kernel_missingness(K, missingness_frac, rng)
        run_one(K_m, mu, "missingness", t)
    for t in range(n_trials_per_family):
        K_s = perturb_kernel_scale_rows(K, scale_range, rng)
        run_one(K_s, mu, "workload_scale", t)

    mean_nmi = float(np.mean(nmis)) if nmis else 0.0
    mean_ratio = float(np.mean(E_cl_ratios)) if E_cl_ratios else 0.0
    stable_count = sum(1 for x in nmis if x >= stability_nmi_min)
    pass_stability = stable_count >= (len(nmis) * 0.5)  # majority
    pass_ratio = mean_ratio < 5.0  # E_cl doesn't explode
    success = pass_stability and pass_ratio

    summary = {
        "n_trials": len(trials),
        "mean_nmi": mean_nmi,
        "stability_nmi_min": stability_nmi_min,
        "stable_fraction": stable_count / len(nmis) if nmis else 0.0,
        "mean_E_cl_ratio_baseline_on_pert": mean_ratio,
        "pass": success,
    }
    return trials, summary, success
