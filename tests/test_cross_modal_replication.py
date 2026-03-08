# Tests for PRD VIII (thoughts3): Cross-Modal Sedation Replication
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from relational_closure.cross_modal_replication import (
    mean_pe_by_condition,
    condition_effect_direction,
    run_cross_modal_replication,
)


def test_mean_pe_by_condition():
    rng = np.random.default_rng(42)
    samples = [(rng.uniform(0, 1, (4, 4)), 0) for _ in range(2)] + [(rng.uniform(0, 1, (4, 4)), 1) for _ in range(2)]
    means = mean_pe_by_condition(samples, use_gudhi=False)
    assert 0 in means and 1 in means
    assert means[0] >= 0 and means[1] >= 0


def test_condition_effect_direction():
    rng = np.random.default_rng(123)
    samples_0 = [(rng.uniform(0.1, 0.5, (4, 4)), 0) for _ in range(2)]
    samples_1 = [(rng.uniform(0.5, 1.0, (4, 4)), 1) for _ in range(2)]
    samples = samples_0 + samples_1
    delta = condition_effect_direction(samples, use_gudhi=False)
    assert isinstance(delta, (float, np.floating))


def test_run_cross_modal_replication():
    rng = np.random.default_rng(42)
    a = [(rng.uniform(0.1, 1.0, (4, 4)), i % 2) for i in range(6)]
    b = [(rng.uniform(0.1, 1.0, (4, 4)), i % 2) for i in range(6)]
    result, pass_ = run_cross_modal_replication(a, b, use_gudhi=False)
    assert "delta_T_modality_a" in result
    assert "delta_T_modality_b" in result
    assert "direction_consistent" in result
    assert isinstance(pass_, bool)
