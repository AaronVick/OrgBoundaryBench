"""
Unit tests for PRD-28: Cross-Construction Invariance and Artifact Audit.
"""

from __future__ import annotations

import numpy as np
import pytest

from relational_closure.cross_construction_invariance import (
    construction_raw,
    construction_threshold,
    construction_symmetrized,
    run_constructions,
    run_cross_construction_invariance,
    run_cross_construction_invariance_simple,
)


def test_construction_raw() -> None:
    W = np.array([[0, 1], [1, 0]], dtype=float)
    assert np.allclose(construction_raw(W), W)


def test_construction_symmetrized() -> None:
    W = np.array([[0, 2], [1, 0]], dtype=float)
    S = construction_symmetrized(W)
    assert np.allclose(S, [[0, 1.5], [1.5, 0]])


def test_run_constructions_three_ways() -> None:
    W = np.array([[0, 1, 0.5], [0.5, 0, 1], [1, 0.5, 0]], dtype=float)
    fns = [
        ("raw", construction_raw),
        ("thresh", lambda W: construction_threshold(W, 0.5)),
        ("sym", construction_symmetrized),
    ]
    results = run_constructions(W, fns, use_gudhi=False)
    assert len(results) == 3
    for r in results:
        assert "construction" in r and "PE" in r and "baselines" in r


def test_run_cross_construction_invariance_simple() -> None:
    W = np.array([[0, 1, 0.5], [0.5, 0, 1], [1, 0.5, 0]], dtype=float)
    results, pass_ = run_cross_construction_invariance_simple(W, use_gudhi=False)
    assert len(results) == 3
    assert isinstance(pass_, bool)


def test_run_cross_construction_invariance_multiple_samples() -> None:
    rng = np.random.default_rng(123)
    samples = [rng.uniform(0, 1, (4, 4)) for _ in range(5)]
    fns = [
        ("raw", construction_raw),
        ("sym", construction_symmetrized),
    ]
    result, pass_ = run_cross_construction_invariance(samples, fns, use_gudhi=False, rank_correlation_min=0.0)
    assert result["n_constructions"] == 2
    assert result["n_samples"] == 5
    assert "rank_correlation_pe" in result
    assert "conclusions_agree" in result
    assert isinstance(pass_, bool)
