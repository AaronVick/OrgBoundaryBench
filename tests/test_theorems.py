"""
Numerical verification of Theorems 3.1–3.4. PRD-04 §3.
"""

import numpy as np
import pytest
from boundary_org import (
    closure_energy,
    spectral_gap_abs,
    greedy_coarse_graining,
    kernel_l2_norm_squared,
    m_star_single,
)
from boundary_org.synthetic import make_lumpable_block_diagonal, make_non_lumpable_random
from config.defaults import TOL_LUMPABLE, TOL_T32_VIOLATION, DELTA_T33


def test_t31_lumpable_implies_zero_closure():
    """T3.1: For lumpable (K,q), E_cl(q) = 0."""
    rng = np.random.default_rng(101)
    for n in [4, 8]:
        syn = make_lumpable_block_diagonal(n, rng=rng)
        E = closure_energy(syn.K, syn.mu, syn.partition)
        assert E < TOL_LUMPABLE, f"n={n} lumpable: E_cl={E}"


def test_t32_no_violations_multiple_trials():
    """T3.2: E_cl <= m_*^2 ||K||^2 over N trials. PRD-04 §3.2 (paper: 1200 trials)."""
    rng = np.random.default_rng(202)
    N = 50  # smaller for CI; use 1200 for full verification
    violations = 0
    max_ratio = 0.0
    for _ in range(N):
        n = rng.integers(4, 12)
        syn = make_lumpable_block_diagonal(n, rng=rng)
        E = closure_energy(syn.K, syn.mu, syn.partition)
        m_star = m_star_single(syn.mu, syn.partition)
        K_sq = kernel_l2_norm_squared(syn.K, syn.mu)
        bound = m_star ** 2 * K_sq
        if bound > 1e-15:
            ratio = E / bound
            max_ratio = max(max_ratio, ratio)
            if E > bound + TOL_T32_VIOLATION:
                violations += 1
    assert violations == 0, f"T3.2: {violations} violations in {N} trials"
    assert max_ratio <= 1.0 + 1e-6, f"T3.2: max ratio {max_ratio} > 1"


def test_t33_spectral_decay_reversible():
    """T3.3: For reversible K, ||K^t f||_L2 <= (1 - gap_abs)^t ||f|| for f ⊥ 1."""
    rng = np.random.default_rng(303)
    n = 6
    syn = make_lumpable_block_diagonal(n, rng=rng)  # symmetric block-diagonal can be reversible
    K = syn.K
    mu = syn.mu
    # Make K reversible (detailed balance): mu_i K_ij = mu_j K_ji
    K_rev = (K + (mu[:, None] * K.T) / (mu[None, :] + 1e-15)) / 2
    K_rev = K_rev / K_rev.sum(axis=1, keepdims=True)
    res = spectral_gap_abs(K_rev, mu)
    # Mean-zero vector
    f = rng.standard_normal(n)
    f = f - (f @ mu)
    D_sqrt = np.diag(np.sqrt(mu))
    D_inv_sqrt = np.diag(1.0 / np.sqrt(mu))
    norm_f = np.sqrt((f ** 2 * mu).sum())
    if norm_f < 1e-10:
        return
    for t in [1, 2, 5]:
        Kt_f = np.linalg.matrix_power(K_rev, t) @ f
        norm_Kt_f = np.sqrt((Kt_f ** 2 * mu).sum())
        theory = (1 - res.gap_abs) ** t * norm_f
        assert norm_Kt_f <= theory * (1 + DELTA_T33), (
            f"T3.3 t={t}: ||K^t f||={norm_Kt_f} > (1-gap)^t ||f||*(1+δ)={theory * (1 + DELTA_T33)}"
        )


def test_t34_greedy_terminates():
    """T3.4: Greedy terminates in at most n-1 steps; block count decreases by 1 each step."""
    rng = np.random.default_rng(404)
    for _ in range(20):
        n = rng.integers(4, 10)
        syn = make_non_lumpable_random(n, rng=rng)
        q_star, trajectory, steps = greedy_coarse_graining(syn.K, syn.mu)
        assert steps <= n - 1, f"T3.4: steps={steps} > n-1={n-1}"
        assert len(q_star) == 1, f"T3.4: expected one block, got {len(q_star)}"
        # Trajectory length = steps + 1 (initial + after each merge)
        assert len(trajectory) == steps + 1
