# Tests for PRD-11: Extended Testing Framework and Rigor
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.extended_rigor import (
    run_replication_sweep,
    run_sensitivity_n,
    negative_result_checklist,
    run_extended_rigor,
)


def test_run_replication_sweep():
    rng = np.random.default_rng(42)
    out = run_replication_sweep(n=8, n_seeds=3, n_random=1, rng=rng)
    assert out["n_seeds"] == 3
    assert "J_star_mean" in out and "J_star_std" in out
    assert out["success_rate"] >= 0 and out["success_rate"] <= 1
    assert len(out["outcomes"]) == 3


def test_run_sensitivity_n():
    rows = run_sensitivity_n(n_values=[6, 8], base_seed=99, n_random=1)
    assert len(rows) == 2
    assert rows[0]["n"] == 6 and rows[1]["n"] == 8
    assert "J_star" in rows[0] and "success" in rows[0]


def test_negative_result_checklist():
    rep = {"n_seeds": 2, "success_rate": 1.0}
    sens = [{"n": 8, "success": True}, {"n": 10, "success": False}]
    chk = negative_result_checklist(rep, sens)
    assert chk["all_tests_listed"] is True
    assert chk["falsification_cited"] is True
    assert chk["null_stated"] is True  # one sensitivity row failed


def test_run_extended_rigor():
    rng = np.random.default_rng(123)
    result, pass_ = run_extended_rigor(n=8, n_seeds=3, n_values=[6, 8], n_random=1, rng=rng)
    assert "replication" in result and "sensitivity" in result and "checklist" in result
    assert "stable" in result and "checklist_ok" in result
    assert isinstance(pass_, bool)
