# Unit tests for PRD-26: Misalignment Outcome Validation
from __future__ import annotations

import numpy as np
import pytest
from boundary_org.misalignment_outcome_validation import (
    graph_control_density,
    graph_control_spectral_gap,
    run_misalignment_outcome_validation,
)


def test_graph_control_density():
    K = np.ones((4, 4)) / 4
    d = graph_control_density(K)
    assert 0 <= d <= 1
    assert d == 1.0


def test_graph_control_spectral_gap():
    K = np.eye(4) * 0.5 + 0.5 / 4
    g = graph_control_spectral_gap(K)
    assert g >= 0


def test_run_misalignment_outcome_validation_too_few_units():
    units = [(np.eye(3) / 3 + 0.01, np.ones(3) / 3, {})]
    result, pass_ = run_misalignment_outcome_validation(units)
    assert pass_ is False


def test_run_misalignment_outcome_validation_multiple_units():
    rng = np.random.default_rng(42)
    units = []
    for _ in range(6):
        K = rng.uniform(0.1, 1.0, (4, 4))
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(4) / 4
        units.append((K, mu, {}))
    result, pass_ = run_misalignment_outcome_validation(units, rng=rng)
    assert result["n_units"] == 6
    assert "corr_m_n_override_success" in result
    assert "direction_ok" in result
    assert isinstance(pass_, bool)
