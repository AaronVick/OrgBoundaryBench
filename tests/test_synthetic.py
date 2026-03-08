"""
Synthetic kernel generators. PRD-04 §2.
"""

import numpy as np
import pytest
from boundary_org import closure_energy
from boundary_org.synthetic import (
    SyntheticKernel,
    make_lumpable_block_diagonal,
    make_lumpable_quotient,
    make_non_lumpable_perturbed,
    make_non_lumpable_random,
)
from config.defaults import TOL_LUMPABLE


def test_lumpable_block_diagonal_stochastic():
    """K rows sum to 1; mu sums to 1."""
    rng = np.random.default_rng(1)
    syn = make_lumpable_block_diagonal(6, rng=rng)
    assert np.allclose(syn.K.sum(axis=1), 1.0)
    assert np.isclose(syn.mu.sum(), 1.0)
    assert syn.lumpable is True


def test_lumpable_quotient_stochastic():
    rng = np.random.default_rng(2)
    syn = make_lumpable_quotient(10, 3, rng=rng)
    assert np.allclose(syn.K.sum(axis=1), 1.0)
    assert np.isclose(syn.mu.sum(), 1.0)
    assert syn.lumpable is True


def test_lumpable_quotient_zero_closure():
    rng = np.random.default_rng(3)
    syn = make_lumpable_quotient(8, 2, rng=rng)
    E = closure_energy(syn.K, syn.mu, syn.partition)
    assert E < TOL_LUMPABLE, f"Quotient lumpable should give E_cl ≈ 0, got {E}"


def test_perturbed_non_lumpable():
    rng = np.random.default_rng(4)
    base = make_lumpable_block_diagonal(6, partition=[[0, 1, 2], [3, 4, 5]], rng=rng)
    syn = make_non_lumpable_perturbed(base, epsilon=0.05, rng=rng)
    assert syn.lumpable is False
    E = closure_energy(syn.K, syn.mu, syn.partition)
    assert E > TOL_LUMPABLE


def test_random_non_lumpable():
    rng = np.random.default_rng(5)
    syn = make_non_lumpable_random(8, partition=[[0, 1, 2, 3], [4, 5, 6, 7]], rng=rng)
    assert syn.lumpable is False
    assert np.allclose(syn.K.sum(axis=1), 1.0)
