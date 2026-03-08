"""
Unit tests for estimators. PRD-02, PRD-04 §5.
"""

import numpy as np
import pytest
from boundary_org import (
    closure_energy,
    projection_matrix,
    identity_partition,
    single_block_partition,
    spectral_gap_abs,
    m_star_single,
    kernel_l2_norm_squared,
)
from boundary_org.synthetic import make_lumpable_block_diagonal, make_non_lumpable_perturbed
from config.defaults import TOL_LUMPABLE, MU_MIN


def test_closure_energy_single_block_zero():
    """Single-block partition => E_cl = 0. PRD-02 §2.4."""
    rng = np.random.default_rng(42)
    syn = make_lumpable_block_diagonal(6, partition=[[0, 1, 2, 3, 4, 5]], rng=rng)
    q = [[0, 1, 2, 3, 4, 5]]
    E = closure_energy(syn.K, syn.mu, q)
    assert E < TOL_LUMPABLE, f"Expected E_cl ≈ 0, got {E}"


def test_closure_energy_identity_partition_zero():
    """Identity partition => E_cl = 0. PRD-02 §2.4."""
    rng = np.random.default_rng(42)
    syn = make_lumpable_block_diagonal(4, rng=rng)
    q = identity_partition(4)
    E = closure_energy(syn.K, syn.mu, q)
    assert E < TOL_LUMPABLE, f"Expected E_cl ≈ 0, got {E}"


def test_closure_energy_lumpable_zero():
    """Lumpable (K,q) => E_cl(q) = 0. T3.1, PRD-04 §3.1."""
    rng = np.random.default_rng(123)
    syn = make_lumpable_block_diagonal(8, partition=[[0, 1, 2, 3], [4, 5, 6, 7]], rng=rng)
    E = closure_energy(syn.K, syn.mu, syn.partition)
    assert E < TOL_LUMPABLE, f"Lumpable kernel should give E_cl < {TOL_LUMPABLE}, got {E}"


def test_closure_energy_non_lumpable_positive():
    """Non-lumpable (K,q) => E_cl(q) > 0. PRD-04 §3.1."""
    rng = np.random.default_rng(456)
    base = make_lumpable_block_diagonal(6, partition=[[0, 1, 2], [3, 4, 5]], rng=rng)
    syn = make_non_lumpable_perturbed(base, epsilon=0.1, rng=rng)
    E = closure_energy(syn.K, syn.mu, syn.partition)
    assert E > TOL_LUMPABLE, f"Non-lumpable should give E_cl > {TOL_LUMPABLE}, got {E}"


def test_spectral_gap_shape():
    """Spectral gap returns gap_abs in [0,1], lambda_2 in [-1,1]. PRD-02 §4."""
    rng = np.random.default_rng(789)
    syn = make_lumpable_block_diagonal(4, rng=rng)
    res = spectral_gap_abs(syn.K, syn.mu)
    assert 0 <= res.gap_abs <= 1
    assert -1 <= res.lambda_2 <= 1


def test_t32_bound_single_trial():
    """T3.2: E_cl(q) <= m_*^2 * ||K||^2. One trial. PRD-04 §3.2."""
    rng = np.random.default_rng(999)
    syn = make_lumpable_block_diagonal(6, partition=[[0, 1, 2], [3, 4, 5]], rng=rng)
    E = closure_energy(syn.K, syn.mu, syn.partition)
    m_star = m_star_single(syn.mu, syn.partition)
    K_norm_sq = kernel_l2_norm_squared(syn.K, syn.mu)
    bound = m_star ** 2 * K_norm_sq
    assert E <= bound + 1e-8, f"T3.2 violation: E_cl={E} > m_*^2||K||^2={bound}"


def test_closure_energy_n2_two_blocks():
    """Edge case n=2, two blocks: E_cl well-defined and >= 0. DESIGN §3 invariants."""
    rng = np.random.default_rng(99)
    syn = make_lumpable_block_diagonal(2, partition=[[0], [1]], rng=rng)
    E = closure_energy(syn.K, syn.mu, [[0], [1]])
    assert E >= 0
    assert E < TOL_LUMPABLE, "Block-diagonal 2x2 is lumpable"
    syn2 = make_non_lumpable_perturbed(syn, 0.1, rng=rng)
    E2 = closure_energy(syn2.K, syn2.mu, [[0], [1]])
    assert E2 >= 0 and np.isfinite(E2)  # n=2 perturbed may still be near-lumpable


def test_closure_energy_singleton_block():
    """Partition with one singleton block: E_cl well-defined (no division by zero)."""
    rng = np.random.default_rng(98)
    syn = make_non_lumpable_perturbed(
        make_lumpable_block_diagonal(4, partition=[[0], [1, 2, 3]], rng=rng), 0.08, rng=rng
    )
    E = closure_energy(syn.K, syn.mu, [[0], [1, 2, 3]])
    assert E >= 0
    assert np.isfinite(E)
