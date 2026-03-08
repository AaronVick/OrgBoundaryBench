"""
Tests for Governance Stress Test Suite (PRD-18). Empirical Test Family B.
"""

import numpy as np
import pytest

from boundary_org.governance_stress import (
    perturb_kernel_noise,
    perturb_kernel_missingness,
    run_stress_test,
)
from boundary_org.synthetic import make_lumpable_block_diagonal


def test_perturb_kernel_noise_stochastic():
    rng = np.random.default_rng(1)
    K = np.ones((4, 4)) / 4
    K2 = perturb_kernel_noise(K, 0.05, rng)
    assert K2.shape == K.shape
    assert np.allclose(K2.sum(axis=1), 1.0)
    assert not np.allclose(K2, K)


def test_perturb_kernel_missingness_stochastic():
    rng = np.random.default_rng(2)
    K = np.ones((4, 4)) / 4
    K2 = perturb_kernel_missingness(K, 0.2, rng)
    assert np.allclose(K2.sum(axis=1), 1.0)


def test_run_stress_test_returns_trials_summary_pass():
    rng = np.random.default_rng(3)
    syn = make_lumpable_block_diagonal(8, rng=rng)
    trials, summary, success = run_stress_test(
        syn.K, syn.mu,
        n_trials_per_family=1,
        stability_nmi_min=0.3,
        rng=rng,
    )
    assert len(trials) >= 3
    assert "mean_nmi" in summary
    assert "pass" in summary
    assert isinstance(success, bool)
