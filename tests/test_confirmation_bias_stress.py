# Tests for PRD X (thoughts3): Human Confirmation-Bias Stress Test
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.confirmation_bias_stress import run_confirmation_bias_stress


def test_run_confirmation_bias_stress():
    rng = np.random.default_rng(42)
    K = rng.uniform(0.1, 1.0, (6, 6))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(6) / 6
    result, pass_ = run_confirmation_bias_stress(K, mu, n_visible=2, n_quiet=2, n_control=2, rng=rng)
    assert "challenge_rate_visible" in result
    assert "challenge_rate_quiet" in result
    assert "false_reassurance_rate" in result
    assert "successful_override_rate" in result
    assert "challenge_rises_when_should" in result
    assert isinstance(pass_, bool)
