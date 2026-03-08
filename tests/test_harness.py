"""
Tests for Boundary Benchmark Harness (PRD-17). Empirical Test Family A.
"""

import numpy as np
import pytest

from boundary_org.harness import (
    cost_triviality,
    random_partition_matched,
    run_harness,
    score_J,
)
from boundary_org.projection import identity_partition, single_block_partition


def test_cost_triviality():
    """Cost(q) = 1/|q|: one-block = 1, singleton = 1/n."""
    n = 6
    one = single_block_partition(n)
    sing = identity_partition(n)
    assert cost_triviality(one) == 1.0
    assert cost_triviality(sing) == pytest.approx(1.0 / n)
    assert cost_triviality([[0, 1], [2, 3], [4, 5]]) == pytest.approx(1.0 / 3)


def test_random_partition_matched():
    """Random partition has exactly n_blocks non-empty blocks."""
    rng = np.random.default_rng(42)
    for n in (5, 10):
        for k in (1, 2, min(5, n)):
            q = random_partition_matched(n, k, rng)
            assert len(q) == k
            flat = [i for bl in q for i in bl]
            assert sorted(flat) == list(range(n))


def test_score_J_shape():
    """score_J returns (E_cl, cost, J, Q) with consistent J formula."""
    from boundary_org.synthetic import make_lumpable_block_diagonal
    rng = np.random.default_rng(1)
    syn = make_lumpable_block_diagonal(6, rng=rng)
    E_cl, cost, J, Q = score_J(syn.K, syn.mu, syn.partition, alpha=1.0, eta=0.5)
    assert E_cl >= 0
    assert 0 < cost <= 1
    assert J == pytest.approx(1.0 * E_cl + 0.5 * cost)
    assert -1 <= Q <= 1


def test_run_harness_returns_leaderboard_and_success():
    """Harness returns leaderboard (sorted by J), q_star, success."""
    from boundary_org.synthetic import make_lumpable_block_diagonal
    rng = np.random.default_rng(2)
    syn = make_lumpable_block_diagonal(8, rng=rng)
    leaderboard, q_star, success = run_harness(syn.K, syn.mu, n_random=2, rng=rng)
    assert len(leaderboard) >= 4  # one_block, singleton, q_star, random_0, random_1
    names = [r["name"] for r in leaderboard]
    assert "one_block" in names
    assert "singleton" in names
    assert "q_star" in names
    Js = [r["J"] for r in leaderboard]
    assert Js == sorted(Js)
    assert all(isinstance(b, list) for b in q_star)
    assert isinstance(success, bool)


def test_run_harness_success_false_when_greedy_collapses_to_one_block():
    """When greedy yields one block only, success is False (non-triviality fails)."""
    # Use a kernel that is nearly uniform/rank-1 so greedy may merge to one block
    n = 6
    K = np.ones((n, n)) / n
    mu = np.ones(n) / n
    leaderboard, q_star, success = run_harness(K, mu, n_random=1, rng=np.random.default_rng(3))
    # With uniform K, greedy typically ends at one block
    if len(q_star) < 2:
        assert success is False
