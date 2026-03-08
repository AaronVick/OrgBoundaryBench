# Tests for PRD III (thoughts3): Outlier and Leverage Stability
from __future__ import annotations

import numpy as np
import pytest
from boundary_org.leverage_stability import (
    node_drop_perturbation,
    run_leverage_stability,
    _kernel_subgraph_nodes,
    _extend_partition_to_full,
)


def test_node_drop_perturbation():
    rng = np.random.default_rng(42)
    K = np.ones((10, 10)) / 10
    mu = np.ones(10) / 10
    keep = node_drop_perturbation(K, mu, 0.2, rng)
    assert len(keep) == 8
    assert len(np.unique(keep)) == 8


def test_run_leverage_stability():
    rng = np.random.default_rng(42)
    K = rng.uniform(0.1, 1.0, (10, 10))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(10) / 10
    result, pass_ = run_leverage_stability(
        K, mu, epsilon_list=(0.1,), n_trials_per_epsilon=2, stability_threshold=2.0, rng=rng
    )
    assert "S_max" in result
    assert "perf_full" in result
    assert result["n_perturbations"] >= 2
    assert isinstance(pass_, bool)


def test_extend_partition_to_full():
    partition = [[0, 1], [2]]
    keep_idx = np.array([1, 2, 5])
    full = _extend_partition_to_full(partition, keep_idx, 6)
    assert len(full) >= 2
    all_nodes = sum(len(b) for b in full)
    assert all_nodes == 6
