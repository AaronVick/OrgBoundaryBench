"""
Tests for Phase Monitoring (PRD-22). Empirical Test Family F.
"""

import numpy as np
import pytest

from boundary_org.phase_monitoring import (
    partition_to_labels,
    nmi_between_partitions,
    run_phase_monitoring,
)
from boundary_org.projection import identity_partition, single_block_partition


def test_partition_to_labels():
    n = 5
    q = [[0, 1], [2, 3], [4]]
    labels = partition_to_labels(q, n)
    assert labels.shape == (n,)
    assert set(labels) == {0, 1, 2}
    assert list(labels) == [0, 0, 1, 1, 2]


def test_nmi_between_partitions_identical():
    n = 6
    q = [[0, 1, 2], [3, 4, 5]]
    assert nmi_between_partitions(q, q, n) == pytest.approx(1.0)


def test_nmi_between_partitions_permuted():
    n = 4
    qa = [[0, 1], [2, 3]]
    qb = [[2, 3], [0, 1]]  # same partition, block labels swapped
    assert nmi_between_partitions(qa, qb, n) == pytest.approx(1.0)


def test_nmi_between_partitions_different():
    n = 4
    qa = [[0, 1], [2, 3]]
    qb = [[0], [1], [2], [3]]  # singleton
    nmi = nmi_between_partitions(qa, qb, n)
    assert 0 <= nmi <= 1
    assert nmi < 1.0


def test_run_phase_monitoring_returns_trajectory_and_flags():
    # Use uniform mu to avoid near-zero block masses in projection (PRD-22)
    n = 6
    rng = np.random.default_rng(1)
    kernels = []
    for _ in range(3):
        K = rng.uniform(0.1, 1.0, (n, n))
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(n) / n
        kernels.append((K, mu))
    trajectory, flags = run_phase_monitoring(kernels, abrupt_nmi_threshold=0.8, rising_window=2)
    assert len(trajectory) == 3
    assert all("step" in t and "n_blocks" in t and "E_cl" in t for t in trajectory)
    assert isinstance(flags, list)
