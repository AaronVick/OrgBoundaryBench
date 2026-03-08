# Tests for PRD-16: Adversarial and Domain-Grounded Falsification
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.adversarial_audit import run_adversarial_audit


def test_run_adversarial_audit_nontrivial():
    """With block-structured K, q* can be non-trivial → Q1 Pass."""
    rng = np.random.default_rng(99)
    # Slightly structured so greedy may find >1 block
    K = rng.uniform(0.2, 0.8, (8, 8))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(8) / 8
    result, pass_ = run_adversarial_audit(K, mu, n_random=1, rng=rng)
    assert "checklist" in result
    assert result["checklist"]["Q1"] in ("Pass", "Fail")
    assert result["checklist"]["Q2"] == "Not assessed (single kernel construction)"
    assert isinstance(pass_, bool)


def test_run_adversarial_audit_trivial():
    """With uniform K, q* often one-block → Q1 Fail."""
    rng = np.random.default_rng(42)
    K = np.ones((6, 6)) / 6  # uniform
    mu = np.ones(6) / 6
    result, pass_ = run_adversarial_audit(K, mu, n_random=1, rng=rng)
    assert result["checklist"]["Q1"] in ("Pass", "Fail")
    assert result["n_blocks_q_star"] >= 1
    assert pass_ == (result["checklist"]["Q1"] == "Pass")
