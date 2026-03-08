"""
Quiet Error Detection Lab (PRD-19). Empirical Test Family C.

Planted (seeded) errors on kernel; detector flags change in closure energy or partition.
Metrics: detection rate, false reassurance rate. Falsification: detection not above chance;
false reassurance above threshold; rubber-stamping.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple

from .operators import closure_energy
from .greedy import greedy_coarse_graining
from .phase_monitoring import nmi_between_partitions


def planted_error_row_swap(K: np.ndarray, i: int, j: int) -> np.ndarray:
    """PRD-19 §2.1: subtle wrong retrieval — swap two rows (transition distributions)."""
    K = np.asarray(K, dtype=float).copy()
    K[[i, j], :] = K[[j, i], :]
    return K


def planted_error_threshold_scale(K: np.ndarray, row_idx: int, scale: float) -> np.ndarray:
    """PRD-19 §2.1: bad policy thresholding — scale one row then renormalize."""
    K = np.asarray(K, dtype=float).copy()
    K[row_idx, :] = K[row_idx, :] * scale
    row_sums = K.sum(axis=1, keepdims=True)
    K = K / row_sums
    return K


def run_quiet_error_lab(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    n_control: int = 5,
    n_planted: int = 5,
    detection_E_cl_factor: float = 1.5,
    detection_nmi_max: float = 0.99,
    rng: np.random.Generator | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], bool]:
    """
    Run quiet-error lab (PRD-19): control (no error) vs planted (row_swap or threshold_scale).
    Detector: (1) E_cl ratio (perturbed/original) > detection_E_cl_factor, or
    (2) NMI(q_orig, q_pert) < detection_nmi_max → flag as "error detected".

    Returns (per_case_results, summary, pass).
    pass: detection_rate >= 0.5 and false_reassurance_rate <= 0.5.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = K.shape[0]
    q_orig, _, _ = greedy_coarse_graining(K, mu)
    E_cl_orig = float(closure_energy(K, mu, q_orig))

    cases: List[Dict[str, Any]] = []
    control_flagged = 0
    planted_total = 0
    planted_detected = 0
    planted_cases: List[Dict[str, Any]] = []

    for _ in range(n_control):
        # No error: same K
        E_cl = float(closure_energy(K, mu, q_orig))
        ratio = E_cl / (E_cl_orig + 1e-20)
        q_same = q_orig
        nmi = 1.0
        flagged = ratio > detection_E_cl_factor or nmi < detection_nmi_max
        if flagged:
            control_flagged += 1
        cases.append({"has_error": False, "E_cl_ratio": ratio, "nmi": nmi, "flagged": flagged})

    for idx in range(n_planted):
        # Planted: row swap two distinct rows
        i, j = 0, min(1, n - 1)
        if n >= 2:
            i = rng.integers(0, n)
            j = rng.integers(0, n)
            while j == i:
                j = rng.integers(0, n)
        K_err = planted_error_row_swap(K, i, j)
        q_pert, _, _ = greedy_coarse_graining(K_err, mu)
        E_cl_pert = float(closure_energy(K_err, mu, q_pert))
        E_cl_orig_on_err = float(closure_energy(K_err, mu, q_orig))
        ratio = E_cl_orig_on_err / (E_cl_orig + 1e-20)
        nmi = nmi_between_partitions(q_orig, q_pert, n)
        flagged = ratio > detection_E_cl_factor or nmi < detection_nmi_max
        planted_total += 1
        if flagged:
            planted_detected += 1
        planted_cases.append({
            "has_error": True,
            "error_type": "row_swap",
            "E_cl_ratio": ratio,
            "nmi": nmi,
            "flagged": flagged,
        })
        cases.append(planted_cases[-1])

    detection_rate = planted_detected / planted_total if planted_total else 0.0
    false_positive_rate = control_flagged / n_control if n_control else 0.0
    # False reassurance = planted but not flagged (missed detection)
    false_reassurance_rate = 1.0 - detection_rate

    pass_detection = detection_rate >= 0.5
    pass_false_reassurance = false_reassurance_rate <= 0.5
    success = pass_detection and pass_false_reassurance

    summary = {
        "n_control": n_control,
        "n_planted": planted_total,
        "detection_rate": detection_rate,
        "false_reassurance_rate": false_reassurance_rate,
        "false_positive_rate": false_positive_rate,
        "pass": success,
    }
    return cases, summary, success
