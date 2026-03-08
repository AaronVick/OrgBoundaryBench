"""
Unit tests for PRD-27: RCTI Real Sedation Test (condition-contrast discrimination).
"""

from __future__ import annotations

import numpy as np
import pytest

from relational_closure.sedation_discrimination import (
    topology_scalar_summary,
    run_discrimination,
    run_discrimination_multi_construction,
)


def test_topology_scalar_summary() -> None:
    """PE is returned from pipeline result."""
    out = topology_scalar_summary({"persistence_entropy": 0.5})
    assert out == 0.5
    assert topology_scalar_summary({}) == 0.0


def test_run_discrimination_empty() -> None:
    """Empty samples returns pass=False."""
    res, pass_ = run_discrimination([])
    assert pass_ is False
    assert res["auc_topology"] == 0.5


def test_run_discrimination_binary_synthetic() -> None:
    """Two-condition synthetic: returns AUC dict and pass flag."""
    rng = np.random.default_rng(42)
    samples = []
    for i in range(4):
        W = rng.uniform(0, 1, (5, 5))
        samples.append((W, 0))
    for i in range(4):
        W = rng.uniform(0, 1, (5, 5)) * 0.3  # different scale
        samples.append((W, 1))
    res, pass_ = run_discrimination(samples, tau=0.1, use_gudhi=False)
    assert "auc_topology" in res
    assert "auc_baselines" in res
    assert res["n_samples"] == 8
    assert res["n_classes"] == 2
    assert 0 <= res["auc_topology"] <= 1
    for k in ["density", "clustering", "reciprocity", "modularity", "spectral_gap", "entropy_degrees"]:
        assert k in res["auc_baselines"]
    assert isinstance(pass_, bool)


def test_run_discrimination_multi_construction_two_constructions() -> None:
    """Multi-construction returns one result per construction; pass if any passes."""
    rng = np.random.default_rng(123)
    samples = [(rng.uniform(0, 1, (4, 4)), i % 2) for i in range(6)]
    raw_fn = lambda W: W
    thresh_fn = lambda W: np.where(W >= 0.5, W, 0.0)
    results, any_pass = run_discrimination_multi_construction(
        samples, [("raw", raw_fn), ("threshold", thresh_fn)], use_gudhi=False
    )
    assert len(results) == 2
    assert results[0]["construction"] == "raw"
    assert results[1]["construction"] == "threshold"
    assert isinstance(any_pass, bool)
