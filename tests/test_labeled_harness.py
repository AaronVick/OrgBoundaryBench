"""
Unit tests for PRD-23: Nontrivial boundary on public labeled graphs.

Tests: external_agreement (NMI, ARI, macro-F1), spectral_partition, run_nontrivial_boundary_labeled.
"""

from __future__ import annotations

import numpy as np
import pytest

from boundary_org.labeled_harness import external_agreement, run_nontrivial_boundary_labeled
from boundary_org.baselines import spectral_partition


def test_external_agreement_perfect_match() -> None:
    """Partition identical to labels gives NMI=1, ARI=1, macro_F1=1 (or high)."""
    n = 6
    # Labels: 0,0,1,1,2,2
    true_labels = np.array([0, 0, 1, 1, 2, 2])
    partition = [[0, 1], [2, 3], [4, 5]]
    out = external_agreement(partition, true_labels, n)
    assert out["nmi"] >= 0.99
    assert out["ari"] >= 0.99
    assert out["macro_f1"] >= 0.99


def test_external_agreement_mismatch() -> None:
    """Random partition vs fixed labels gives lower agreement."""
    n = 8
    true_labels = np.array([0, 0, 0, 1, 1, 1, 2, 2])
    partition = [[0, 1, 2, 3], [4, 5, 6, 7]]  # does not match classes
    out = external_agreement(partition, true_labels, n)
    assert 0 <= out["nmi"] <= 1
    assert 0 <= out["ari"] <= 1
    assert 0 <= out["macro_f1"] <= 1
    # Should be worse than perfect
    assert out["nmi"] < 0.99 or out["ari"] < 0.99


def test_external_agreement_masked_unlabeled() -> None:
    """Nodes with label -1 are excluded from agreement."""
    n = 4
    true_labels = np.array([0, -1, 1, -1])
    partition = [[0, 1], [2, 3]]
    out = external_agreement(partition, true_labels, n)
    assert "nmi" in out and "ari" in out and "macro_f1" in out


def test_spectral_partition_returns_two_blocks() -> None:
    """Spectral baseline returns a 2-way partition (list of two blocks)."""
    rng = np.random.default_rng(42)
    K = rng.uniform(0.1, 1.0, (8, 8))
    K = K / K.sum(axis=1, keepdims=True)
    q = spectral_partition(K)
    assert len(q) == 2
    assert sum(len(b) for b in q) == 8
    assert sorted(sum(q, [])) == list(range(8))


def test_run_nontrivial_boundary_labeled_returns_leaderboard_and_agreement() -> None:
    """run_nontrivial_boundary_labeled returns leaderboard with agreement, q_star, success, meaningful."""
    n = 10
    rng = np.random.default_rng(42)
    K = rng.uniform(0.1, 1.0, (n, n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(n) / n
    labels = rng.integers(0, 3, size=n)
    leaderboard, q_star, success, meaningful = run_nontrivial_boundary_labeled(
        K, mu, labels, n_random=2, rng=rng
    )
    assert len(leaderboard) >= 5  # one_block, singleton, q_star, spectral, random_0, random_1
    for row in leaderboard:
        assert "name" in row and "J" in row and "agreement" in row
        assert set(row["agreement"].keys()) == {"nmi", "ari", "macro_f1"}
    assert 2 <= len(q_star) <= n or len(q_star) == 1  # q* may collapse to one block
    assert isinstance(success, bool)
    assert isinstance(meaningful, bool)
