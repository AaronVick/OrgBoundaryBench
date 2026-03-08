"""
Tests for Predictive-Control Misalignment Engine (PRD-20). Empirical Test Family D.
"""

import numpy as np
import pytest

from boundary_org.misalignment_engine import (
    predictive_boundary,
    control_boundary_proxy,
    run_misalignment_engine,
)


def test_predictive_boundary():
    # Use uniform mu to avoid near-zero block mass in greedy (PRD-20)
    n = 6
    rng = np.random.default_rng(5)
    K = rng.uniform(0.1, 1.0, (n, n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(n) / n
    q = predictive_boundary(K, mu)
    assert len(q) >= 1
    flat = [i for bl in q for i in bl]
    assert sorted(flat) == list(range(6))


def test_control_boundary_proxy():
    n = 6
    rng = np.random.default_rng(6)
    K = rng.uniform(0.1, 1.0, (n, n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(n) / n
    q = control_boundary_proxy(K, mu, use_perturbed=True, rng=rng)
    assert len(q) >= 1
    flat = [i for bl in q for i in bl]
    assert sorted(flat) == list(range(6))


def test_run_misalignment_engine():
    n = 8
    rng = np.random.default_rng(7)
    K = rng.uniform(0.1, 1.0, (n, n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(n) / n
    report, success = run_misalignment_engine(K, mu, rng=rng)
    assert "m_n" in report
    assert "n_blocks_pred" in report
    assert "n_blocks_ctrl" in report
    assert report["m_n"] >= 0.0
    assert isinstance(success, bool)
