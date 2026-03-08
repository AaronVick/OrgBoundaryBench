"""
Tests for Quiet Error Detection Lab (PRD-19). Empirical Test Family C.
"""

import numpy as np
import pytest

from boundary_org.quiet_error_lab import (
    planted_error_row_swap,
    planted_error_threshold_scale,
    run_quiet_error_lab,
)


def test_planted_error_row_swap():
    # Use stochastic K (rows sum to 1)
    K = np.ones((4, 4)) / 4
    K2 = planted_error_row_swap(K, 0, 1)
    assert np.allclose(K2[0], K[1])
    assert np.allclose(K2[1], K[0])
    assert np.allclose(K2.sum(axis=1), 1.0)


def test_planted_error_threshold_scale():
    K = np.ones((3, 3)) / 3
    K2 = planted_error_threshold_scale(K, 0, 2.0)
    assert np.allclose(K2.sum(axis=1), 1.0)


def test_run_quiet_error_lab_returns_cases_summary_pass():
    from boundary_org.synthetic import make_lumpable_block_diagonal
    rng = np.random.default_rng(4)
    syn = make_lumpable_block_diagonal(6, rng=rng)
    cases, summary, success = run_quiet_error_lab(syn.K, syn.mu, n_control=2, n_planted=2, rng=rng)
    assert len(cases) >= 4
    assert "detection_rate" in summary
    assert "false_reassurance_rate" in summary
    assert isinstance(success, bool)
