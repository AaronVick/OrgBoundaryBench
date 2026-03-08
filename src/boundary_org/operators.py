"""
L2(μ) operator norm and closure operator K_q.

Paper: Def 2.3 (closure energy E^op_cl(q) = ‖K_q‖^2); PRD-02 §2.3 (matrix recipe).
"""

from __future__ import annotations

import numpy as np
from typing import Sequence

from .projection import projection_matrix


def l2_operator_norm_squared(A: np.ndarray, mu: np.ndarray) -> float:
    """
    ‖A‖^2_{L2(μ)→L2(μ)} = σ_max(D^{1/2} A D^{-1/2})^2.

    PRD-02 §2.3. D = diag(μ). Guard D^{-1/2} for near-zero μ.
    """
    mu = np.asarray(mu, dtype=float)
    mu_safe = np.maximum(mu, 1e-15)
    D_inv_sqrt = np.diag(1.0 / np.sqrt(mu_safe))
    D_sqrt = np.diag(np.sqrt(mu_safe))
    M = D_sqrt @ A @ D_inv_sqrt
    if not np.isfinite(M).all():
        return float("inf")
    # Largest singular value squared
    s = np.linalg.svd(M, compute_uv=False)
    return float(np.max(s) ** 2)


def closure_operator_matrix(
    K: np.ndarray,
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
) -> np.ndarray:
    """
    K_q = (I - Π_q) K Π_q. Def 2.3.
    """
    Pi = projection_matrix(mu, partition)
    return (np.eye(K.shape[0]) - Pi) @ K @ Pi


def closure_energy(
    K: np.ndarray,
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
) -> float:
    """
    E^op_cl(q) = ‖K_q‖^2_{L2(μ)}.  [Paper Eq. (2), Def 2.3; Estimator 5.1]

    PRD-02 §2.3: E = σ_max(D^{1/2} K_q D^{-1/2})^2.
    Returns 0 for single-block and identity partition (by construction).
    """
    n = K.shape[0]
    if len(partition) == 1:
        return 0.0
    if len(partition) == n and all(len(B) == 1 for B in partition):
        return 0.0
    K_q = closure_operator_matrix(K, mu, partition)
    return l2_operator_norm_squared(K_q, mu)


def kernel_l2_norm_squared(K: np.ndarray, mu: np.ndarray) -> float:
    """‖K‖²_{L2(μ)} for T3.2 bound (E_cl ≤ m_*² ‖K‖²). Def 2.3, Theorem 3.2. Same as l2_operator_norm_squared(K, mu)."""
    return l2_operator_norm_squared(K, mu)
