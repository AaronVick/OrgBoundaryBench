"""
Tests for RCTI Comparative Pipeline (PRD-21) and graph baselines.
"""

import numpy as np
import pytest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from relational_closure.graph_baselines import (
    graph_density,
    graph_clustering_directed,
    graph_reciprocity,
    graph_entropy_degrees,
    compute_all_baselines,
)
from relational_closure.pipeline import run_pipeline


def test_graph_density():
    W = np.zeros((4, 4))
    assert graph_density(W) == 0.0
    W[0, 1] = 1
    W[1, 2] = 1
    assert graph_density(W) == pytest.approx(2 / 16)


def test_graph_reciprocity():
    W = np.zeros((3, 3))
    W[0, 1] = 1
    W[1, 0] = 1
    W[0, 2] = 1
    # Pairs (i,j) with i<j and at least one of (i,j)/(j,i) present: (0,1), (0,2). (0,1) reciprocated -> 1/2
    assert graph_reciprocity(W) == pytest.approx(0.5)


def test_graph_entropy_degrees():
    W = np.ones((4, 4)) / 4
    out = W.sum(axis=1)
    assert out.shape == (4,)
    H = graph_entropy_degrees(W)
    assert H >= 0


def test_compute_all_baselines():
    W = np.eye(4) * 0.5
    W[0, 1] = 0.5
    W[1, 2] = 0.5
    b = compute_all_baselines(W)
    assert "density" in b
    assert "clustering" in b
    assert "reciprocity" in b
    assert "modularity" in b
    assert "spectral_gap" in b
    assert "entropy_degrees" in b


def test_rcti_comparative_two_constructions():
    """Run pipeline on two constructions and ensure baselines and topology are computed."""
    W = np.zeros((5, 5))
    for i in range(5):
        W[i, (i + 1) % 5] = 1.0
    res = run_pipeline(W, tau=0.1, use_gudhi=False)
    assert "C1" in res
    assert "C4b" in res
    assert "persistence_entropy" in res
    b = compute_all_baselines(W)
    assert len(b) == 6
