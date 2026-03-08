"""
Unit tests for PRD-24: Incident-Coupled Phase Monitoring.
"""

from __future__ import annotations

import numpy as np
import pytest

from boundary_org.incident_phase_monitoring import (
    _parse_alert_steps_from_flags,
    lead_time_and_fp,
    run_incident_phase_monitoring,
    compute_baseline_drift_alerts,
)


def test_parse_alert_steps_from_flags() -> None:
    """Parse step indices from flag strings."""
    flags = ["step_0: rising_closure", "step_2: abrupt_switch (NMI=0.5 < 0.8)", "step_2: duplicate"]
    assert _parse_alert_steps_from_flags(flags) == [0, 2]
    assert _parse_alert_steps_from_flags([]) == []


def test_lead_time_and_fp() -> None:
    """Lead time = incident - last alert before; FP = alert with no incident in window."""
    alert_steps = [1, 2]
    incident_steps = [4]
    median_lead, fp_rate, n_fp = lead_time_and_fp(alert_steps, incident_steps, fp_window=2)
    assert median_lead == 2  # incident 4 - last alert 2
    assert n_fp >= 0
    assert 0 <= fp_rate <= 1


def test_lead_time_and_fp_no_incidents() -> None:
    """When no incidents, all alerts are FP."""
    median_lead, fp_rate, n_fp = lead_time_and_fp([1, 2], [], fp_window=2)
    assert n_fp == 2
    assert fp_rate == 1.0


def test_run_incident_phase_monitoring_returns_result_and_pass() -> None:
    """Full run returns trajectory, phase alerts, baselines, lead/FP, pass."""
    rng = np.random.default_rng(42)
    kernels = []
    for _ in range(5):
        K = rng.uniform(0.1, 1.0, (4, 4))
        K = K / K.sum(axis=1, keepdims=True)
        kernels.append((K, np.ones(4) / 4))
    result, pass_ = run_incident_phase_monitoring(kernels, incident_steps=[3], fp_window=2)
    assert "trajectory" in result
    assert "phase_alert_steps" in result
    assert "median_lead_time_phase" in result
    assert "fp_rate_phase" in result
    assert "baseline_alerts" in result
    assert "baseline_median_lead" in result
    assert isinstance(pass_, bool)


def test_compute_baseline_drift_alerts() -> None:
    """Baseline drift alerts return list of step indices per baseline."""
    rng = np.random.default_rng(123)
    kernels = [(rng.uniform(0.1, 1.0, (4, 4)) / 4, np.ones(4) / 4) for _ in range(4)]
    for i, (K, mu) in enumerate(kernels):
        K = K / K.sum(axis=1, keepdims=True)
        kernels[i] = (K, mu)
    out = compute_baseline_drift_alerts(kernels, drift_quantile_threshold=0.9)
    assert "density_drift" in out
    assert "entropy_drift" in out
    assert "spectral_gap_drift" in out
    assert all(isinstance(v, list) for v in out.values())
