"""
Tests for Relational Closure / Topology of Interiority pipeline.

PRD-13; math → empirical: directed flag, persistence, C1/C4b/C2F.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Allow running without gudhi (cycle-rank proxy used)
pytest.importorskip("relational_closure", reason="relational_closure package")

from relational_closure import (
    directed_flag_complex,
    enumerate_directed_cliques,
    barcode_from_complex,
    betti_from_barcode,
    persistence_entropy,
    check_C1,
    check_C3,
    check_C4b,
    compute_C2F,
    run_pipeline,
)


def test_directed_flag_cycle():
    """Directed 4-cycle: vertices and forward edges (i,j) with i<j; no 2-simplices."""
    W = np.zeros((4, 4))
    for i in range(4):
        W[i, (i + 1) % 4] = 1.0  # edge i -> i+1
    simplices = directed_flag_complex(W, threshold=None, max_dim=2)
    vertices = [s for s, _ in simplices if len(s) == 1]
    edges = [s for s, _ in simplices if len(s) == 2]
    assert len(vertices) == 4
    # Only (0,1), (1,2), (2,3) are (i,j) with i<j; (3,0) is 3->0 so not in (i,j) form
    assert len(edges) == 3
    triangles = [s for s, _ in simplices if len(s) == 3]
    assert len(triangles) == 0


def test_directed_flag_complete_2():
    """Complete directed graph on 3 nodes has one 2-simplex (triangle)."""
    W = np.ones((3, 3)) - np.eye(3)  # all off-diagonal 1
    simplices = directed_flag_complex(W, threshold=None, max_dim=3)
    triangles = [s for s, _ in simplices if len(s) == 3]
    assert len(triangles) == 1
    assert triangles[0] == (0, 1, 2)


def test_barcode_from_complex_returns_dict():
    """barcode_from_complex returns dict with 'barcode' and 'method'."""
    W = np.ones((4, 4)) - np.eye(4)
    W[0, 2] = W[2, 0] = 0  # break some edges so not too dense
    simplices = directed_flag_complex(W, max_dim=3)
    result = barcode_from_complex(simplices, use_gudhi=True)
    assert "barcode" in result
    assert "method" in result
    assert isinstance(result["barcode"], dict)


def test_betti_from_barcode():
    """Betti numbers are nonnegative integers per dimension."""
    barcode_dict = {
        "barcode": {
            0: [(0.0, 0.0)],
            1: [(0.0, 0.3), (0.1, 0.5)],
        },
        "method": "test",
    }
    betti = betti_from_barcode(barcode_dict)
    assert betti.get(0) == 1
    assert betti.get(1) == 2


def test_persistence_entropy_nonnegative():
    """Persistence entropy >= 0."""
    barcode_dict = {"barcode": {0: [(0, 0)], 1: [(0, 0.5)]}, "method": "test"}
    pe = persistence_entropy(barcode_dict)
    assert pe >= 0


def test_check_C1_satisfied():
    """C1 satisfied when at least one β₁ bar has lifespan > τ."""
    barcode_dict = {"barcode": {0: [(0, 0)], 1: [(0.0, 0.5)]}, "method": "test"}
    ok, msg = check_C1(barcode_dict, tau=0.1)
    assert ok is True
    assert "C1" in msg


def test_check_C1_not_satisfied():
    """C1 not satisfied when no β₁ bar with lifespan > τ."""
    barcode_dict = {"barcode": {0: [(0, 0)], 1: [(0.0, 0.05)]}, "method": "test"}
    ok, msg = check_C1(barcode_dict, tau=0.1)
    assert ok is False


def test_check_C4b():
    """C4b checks for β_k, k>=2."""
    barcode_dict = {"barcode": {0: [(0, 0)], 1: [], 2: [(0.1, 0.2)]}, "method": "test"}
    ok, msg = check_C4b(barcode_dict)
    assert ok is True


def test_compute_C2F():
    """C2F in [0,1]; 1 when sub captures all topology."""
    beta_whole = {0: 1, 1: 2}
    beta_sub = {0: 1, 1: 2}
    c2f = compute_C2F(beta_whole, beta_sub)
    assert 0 <= c2f <= 1
    # When sub equals whole, proxy gives high fidelity
    assert c2f >= 0.5


def test_run_pipeline_keys():
    """run_pipeline returns barcode_dict, betti, C1, C4b, persistence_entropy."""
    W = np.ones((5, 5)) - np.eye(5)
    out = run_pipeline(W, max_dim=3, tau=0.01)
    assert "barcode_dict" in out
    assert "betti" in out
    assert "C1" in out and "satisfied" in out["C1"] and "message" in out["C1"]
    assert "C4b" in out
    assert "persistence_entropy" in out
    assert "n_simplices" in out


def test_run_rcti_verification_script():
    """run_rcti_verification.py writes expected files to out-dir."""
    import subprocess
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        r = subprocess.run(
            [sys.executable, str(root / "scripts/run_rcti_verification.py"), "--out-dir", str(out), "--n", "5", "--no-gudhi"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert (out / "rcti_verification_report.txt").exists()
        assert (out / "barcode_summary.json").exists()
        assert (out / "conditions_C1_C4_C2F.yaml").exists()
        assert (out / "falsification_F1_F5.md").exists()
        data = json.loads((out / "barcode_summary.json").read_text())
        assert "betti" in data
        assert "persistence_entropy" in data
