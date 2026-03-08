"""
Predictive-Control Misalignment Engine (PRD-20). Empirical Test Family D.

Two boundary learners: q_pred (predictive = greedy on K), q_ctrl (control proxy = greedy on
perturbed K or Louvain). Misalignment m_n = ‖Π_pred - Π_ctrl‖; outcomes: override success,
recovery, confusion (stubbed when no real intervention data).
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple

from .greedy import greedy_coarse_graining
from .estimators import misalignment
from .baselines import louvain_partition


def predictive_boundary(K: np.ndarray, mu: np.ndarray) -> List[List[int]]:
    """PRD-20 §2.1: q_pred from transition distributions (closure-optimal)."""
    q, _, _ = greedy_coarse_graining(K, mu)
    return q


def control_boundary_proxy(K: np.ndarray, mu: np.ndarray, *, use_perturbed: bool = True, perturb_strength: float = 0.08, rng: np.random.Generator | None = None) -> List[List[int]]:
    """PRD-20 §2.2: q_ctrl proxy — Louvain (structure) or greedy on perturbed K (intervention-response proxy)."""
    if use_perturbed:
        if rng is None:
            rng = np.random.default_rng(42)
        K_p = K + rng.uniform(-perturb_strength, perturb_strength, K.shape)
        K_p = np.maximum(K_p, 1e-12)
        K_p = K_p / K_p.sum(axis=1, keepdims=True)
        q, _, _ = greedy_coarse_graining(K_p, mu)
        return q
    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        return q_louvain
    # Fallback: same as predictive (no second view)
    return greedy_coarse_graining(K, mu)[0]


def run_misalignment_engine(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    use_louvain_as_ctrl: bool = False,
    perturb_strength: float = 0.08,
    rng: np.random.Generator | None = None,
) -> Tuple[Dict[str, Any], bool]:
    """
    Compute predictive vs control boundary and misalignment m_n (PRD-20).
    Stub outcomes (override_success, recovery_time, confusion) set from m_n for testing:
    higher m_n → worse override, longer recovery, higher confusion (synthetic).
    pass: True iff m_n is finite and report is produced; real pass/fail requires outcome data.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    q_pred = predictive_boundary(K, mu)
    q_ctrl = control_boundary_proxy(K, mu, use_perturbed=not use_louvain_as_ctrl, perturb_strength=perturb_strength, rng=rng)
    m_n = float(misalignment(mu, q_pred, q_ctrl))

    # Stub outcomes (PRD-20 §3): when real override/recovery data absent, use synthetic relation
    override_success_stub = max(0.0, 1.0 - 0.3 * m_n)  # higher m_n → lower override
    recovery_time_stub = 1.0 + 2.0 * m_n
    confusion_stub = min(1.0, 0.5 * m_n)

    report = {
        "m_n": m_n,
        "n_blocks_pred": len(q_pred),
        "n_blocks_ctrl": len(q_ctrl),
        "override_success_stub": override_success_stub,
        "recovery_time_stub": recovery_time_stub,
        "confusion_stub": confusion_stub,
        "control_proxy": "Louvain" if use_louvain_as_ctrl else "greedy_on_perturbed",
    }
    # Pass: m_n computed and in reasonable range; real falsification needs outcome correlation
    success = np.isfinite(m_n) and m_n >= 0.0
    return report, success
