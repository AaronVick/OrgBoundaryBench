"""
Core estimators: closure energy (5.1), misalignment (5.2), spectral gap (5.3), binding index (5.4).

PRD-02; PRD-00 §4 (Estimators). Closure energy implemented in operators.py; here re-export and add rest.
"""

from __future__ import annotations

import numpy as np
from typing import Sequence, Tuple, Optional
from dataclasses import dataclass

from .operators import closure_energy, kernel_l2_norm_squared, l2_operator_norm_squared
from .projection import projection_matrix, identity_partition
from . import projection
from . import operators

# Re-export for API
__all__ = [
    "closure_energy",
    "spectral_gap_abs",
    "binding_index",
    "misalignment",
    "SpectralGapResult",
]


@dataclass
class SpectralGapResult:
    """Estimator 5.3 output. PRD-02 §4."""
    gap_abs: float
    lambda_2: float
    negative_dominant: bool  # True when |λ_n| > λ_2


def spectral_gap_abs(
    K: np.ndarray,
    mu: np.ndarray,
) -> SpectralGapResult:
    """
    Absolute spectral gap: gap_abs = 1 - max_{i>=2} |λ_i|. Def 2.6, Estimator 5.3.

    K̃ = D^{1/2} K D^{-1/2}; eigenvalues λ_1=1 >= λ_2 >= ... >= λ_n.
    negative_dominant when standard gap 1-λ_2 would overestimate decay (λ_n < 0 dominant).
    """
    mu = np.asarray(mu, dtype=float)
    D_sqrt = np.diag(np.sqrt(np.maximum(mu, 1e-15)))
    D_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(mu, 1e-15)))
    K_tilde = D_sqrt @ K @ D_inv_sqrt
    eigvals = np.linalg.eigvalsh(K_tilde)  # ascending order for real symmetric
    eigvals = np.sort(eigvals)[::-1]  # λ_1 >= λ_2 >= ... >= λ_n
    lambda_2 = float(eigvals[1])
    max_abs_non_perron = float(np.max(np.abs(eigvals[1:])))
    gap_abs = 1.0 - max_abs_non_perron
    negative_dominant = abs(eigvals[-1]) > lambda_2 if len(eigvals) > 1 else False
    return SpectralGapResult(gap_abs=gap_abs, lambda_2=lambda_2, negative_dominant=negative_dominant)


def binding_index(
    K: np.ndarray,
    mu: np.ndarray,
    partition: Sequence[Sequence[int]],
    *,
    min_blocks: int = 3,
) -> float:
    """
    B_ind = 1 - Var(s_i / s̄) from eigenvalue spacings of K restricted to L^2_q(μ). Estimator 5.4.

    PRD-02 §5.2: quotient chain eigenvalues; spacings s_i; normalized variance.
    Returns NaN if number of blocks < min_blocks or s̄ = 0.
    """
    m = len(partition)
    if m < min_blocks:
        return np.nan
    # Quotient chain: K̄_{kℓ} = (1/μ(B_k)) sum_{i in B_k} μ_i sum_{j in B_ℓ} K_{ij}
    mu_arr = np.asarray(mu)
    K_bar = np.zeros((m, m))
    for k, Bk in enumerate(partition):
        Bk = np.asarray(Bk)
        mass_k = mu_arr[Bk].sum()
        for ell, B_ell in enumerate(partition):
            B_ell = np.asarray(B_ell)
            # K̄_{k,ell} = (1/μ(B_k)) sum_{i in B_k} μ_i sum_{j in B_ell} K_{ij}
            K_bar[k, ell] = (1.0 / mass_k) * np.sum(mu_arr[Bk] * K[np.ix_(Bk, B_ell)].sum(axis=1))
    # Eigenvalues of K̄ (excluding Perron 1)
    eigvals = np.linalg.eigvals(K_bar)
    eigvals = np.real(eigvals)
    eigvals = np.sort(eigvals)[::-1]
    if eigvals[0] < 0.99:
        pass  # still use all for spacings
    non_perron = eigvals[1:]  # drop Perron
    if len(non_perron) < 2:
        return np.nan
    spacings = np.diff(non_perron)  # λ_{i+1} - λ_i
    s_bar = np.mean(spacings)
    if s_bar <= 0 or np.isclose(s_bar, 0):
        return np.nan
    var_normalized = np.var(spacings / s_bar)
    return float(1.0 - var_normalized)


def misalignment(
    mu: np.ndarray,
    partition_pred: Sequence[Sequence[int]],
    partition_ctrl: Sequence[Sequence[int]],
) -> float:
    """
    m̂_n = ‖Π_{q_pred} - Π_{q_ctrl}‖_{L2(μ)}. Estimator 5.2.

    PRD-02 §3.1: same L2(μ) operator norm as closure energy.
    """
    Pi_pred = projection_matrix(mu, partition_pred)
    Pi_ctrl = projection_matrix(mu, partition_ctrl)
    diff = Pi_pred - Pi_ctrl
    # ‖diff‖_{L2(μ)} = σ_max(D^{1/2} diff D^{-1/2})
    return float(np.sqrt(l2_operator_norm_squared(diff, mu)))


def m_star_single(mu: np.ndarray, partition: Sequence[Sequence[int]]) -> float:
    """
    m_*(q) = ‖I - Π_q‖_{L2(μ)} when Q_A = {q_n}, Q_B = {q}. Def 2.4 special case.
    Used in T3.2 verification.
    """
    n = len(mu)
    Pi = projection_matrix(mu, partition)
    return float(np.sqrt(l2_operator_norm_squared(np.eye(n) - Pi, mu)))
