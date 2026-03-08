"""
Phase monitoring (PRD-22). Empirical Test Family F.

Monitored quantities: minimal closure E_cl over time/parameter; boundary q* and NMI between
consecutive q*; flags for rising closure and abrupt boundary switch.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Sequence, Tuple

from .operators import closure_energy
from .greedy import greedy_coarse_graining


def partition_to_labels(partition: Sequence[Sequence[int]], n: int) -> np.ndarray:
    """Map partition (list of blocks) to label vector of length n. label[i] = block index containing i."""
    labels = np.full(n, -1, dtype=int)
    for k, bl in enumerate(partition):
        for i in bl:
            labels[i] = k
    return labels


def nmi_between_partitions(
    q_a: Sequence[Sequence[int]],
    q_b: Sequence[Sequence[int]],
    n: int,
) -> float:
    """Normalized mutual information between two partitions (same n nodes). [0,1]; 1 = identical."""
    from sklearn.metrics import normalized_mutual_info_score
    la = partition_to_labels(q_a, n)
    lb = partition_to_labels(q_b, n)
    if np.any(la < 0) or np.any(lb < 0):
        return 0.0
    return float(normalized_mutual_info_score(la, lb, average_method="arithmetic"))


def run_phase_monitoring(
    kernels: List[Tuple[np.ndarray, np.ndarray]],
    *,
    abrupt_nmi_threshold: float = 0.8,
    rising_window: int = 2,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    PRD-22: Compute E_cl and q* per step; NMI between consecutive q*; flag rising E_cl and abrupt switch.

    kernels: list of (K, mu) for each time/parameter step.
    abrupt_nmi_threshold: if NMI(q_t, q_{t+1}) < this, flag "abrupt_switch".
    rising_window: number of recent steps to check for rising E_cl (rising if E_cl[t] > E_cl[t-1] and ...).

    Returns (trajectory, flags). trajectory[i] = {step, n_blocks, E_cl, nmi_prev}; flags = list of strings.
    """
    trajectory: List[Dict[str, Any]] = []
    flags: List[str] = []
    q_prev = None
    n_prev = None
    for step, (K, mu) in enumerate(kernels):
        n = K.shape[0]
        q_star, energy_traj, _ = greedy_coarse_graining(K, mu)
        E_cl = float(closure_energy(K, mu, q_star))
        nmi_prev = None
        if q_prev is not None and n_prev == n:
            nmi_prev = nmi_between_partitions(q_prev, q_star, n)
            if nmi_prev < abrupt_nmi_threshold:
                flags.append(f"step_{step}: abrupt_switch (NMI={nmi_prev:.4f} < {abrupt_nmi_threshold})")
        trajectory.append({
            "step": step,
            "n_blocks": len(q_star),
            "E_cl": E_cl,
            "nmi_prev": nmi_prev,
        })
        q_prev = q_star
        n_prev = n

    # Rising closure: E_cl increases over the last rising_window steps
    for i in range(rising_window, len(trajectory)):
        recent = [trajectory[j]["E_cl"] for j in range(i - rising_window, i + 1)]
        if all(recent[k] < recent[k + 1] for k in range(len(recent) - 1)):
            flags.append(f"step_{i}: rising_closure (E_cl increasing over {rising_window + 1} steps)")

    return trajectory, flags
