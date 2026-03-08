# Tests for PRD II (thoughts3): Null-Model and Rival-Theory Audit
from __future__ import annotations

import numpy as np
import pytest
from boundary_org.null_rival_audit import run_null_rival_audit, run_null_rival_audit_bootstrap


def test_run_null_rival_audit_returns_D_and_pass():
    rng = np.random.default_rng(42)
    K = rng.uniform(0.1, 1.0, (8, 8))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(8) / 8
    result, pass_ = run_null_rival_audit(K, mu, rng=rng)
    assert "perf_star" in result
    assert "D" in result
    assert "max_baseline_or_null" in result
    assert isinstance(pass_, bool)


def test_run_null_rival_audit_with_labels():
    rng = np.random.default_rng(123)
    K = rng.uniform(0.1, 1.0, (6, 6))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(6) / 6
    labels = np.array([0, 0, 1, 1, 2, 2])
    result, pass_ = run_null_rival_audit(K, mu, labels=labels, rng=rng)
    assert "D" in result
    assert result["n_rivals"] >= 3


def test_run_null_rival_audit_bootstrap():
    rng = np.random.default_rng(42)
    K = rng.uniform(0.1, 1.0, (8, 8))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(8) / 8
    result, pass_ = run_null_rival_audit_bootstrap(K, mu, n_bootstrap=5, rng=rng)
    assert "mean_D" in result
    assert "ci_lower" in result
    assert "ci_upper" in result
