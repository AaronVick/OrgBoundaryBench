"""
Unit tests for PRD-25: Governance Metrics on Real Appeals / Overrides.
"""

from __future__ import annotations

import pytest

from boundary_org.governance_metrics import (
    ChallengeEvent,
    compute_override_latency,
    compute_reversal_success,
    compute_unattributed_residue,
    compute_unresolved_challenge_rate,
    run_governance_metrics,
)


def test_compute_reversal_success() -> None:
    """Reversal success = fraction reversed."""
    events = [
        ChallengeEvent("1", 0, 1, "reversed", "a"),
        ChallengeEvent("2", 0, 1, "denied", "b"),
        ChallengeEvent("3", 0, 1, "reversed", "c"),
    ]
    assert compute_reversal_success(events) == pytest.approx(2 / 3)
    assert compute_reversal_success([]) == 0.0


def test_compute_unresolved_challenge_rate() -> None:
    """Unresolved = fraction denied."""
    events = [
        ChallengeEvent("1", 0, 1, "reversed", "a"),
        ChallengeEvent("2", 0, 1, "denied", "b"),
    ]
    assert compute_unresolved_challenge_rate(events) == 0.5
    assert compute_unresolved_challenge_rate([]) == 0.0


def test_compute_unattributed_residue() -> None:
    """Unattributed = fraction with no attributable_agent."""
    events = [
        ChallengeEvent("1", 0, 1, "reversed", "a"),
        ChallengeEvent("2", 0, 1, "denied", None),
    ]
    assert compute_unattributed_residue(events) == 0.5
    assert compute_unattributed_residue([]) == 0.0


def test_compute_override_latency() -> None:
    """Override latency = resolution - challenge time."""
    events = [
        ChallengeEvent("1", 100, 105, "reversed", "a"),
        ChallengeEvent("2", 200, 208, "denied", "b"),
    ]
    lat = compute_override_latency(events)
    assert lat["count"] == 2
    assert lat["mean"] == 6.5
    assert lat["min"] == 5
    assert lat["max"] == 8


def test_run_governance_metrics_pass() -> None:
    """Pass when reversal high, unresolved and unattributed low."""
    events = [
        ChallengeEvent("1", 0, 1, "reversed", "a"),
        ChallengeEvent("2", 0, 1, "reversed", "b"),
        ChallengeEvent("3", 0, 1, "denied", "c"),
    ]
    metrics, pass_ = run_governance_metrics(
        events, reversal_success_min=0.5, unresolved_rate_max=0.5, unattributed_max=1.0
    )
    assert metrics["reversal_success"] == pytest.approx(2 / 3)
    assert pass_ is True


def test_run_governance_metrics_fail_ceremonial() -> None:
    """Fail when reversal too low (ceremonial review)."""
    events = [
        ChallengeEvent("1", 0, 1, "denied", "a"),
        ChallengeEvent("2", 0, 1, "denied", "b"),
    ]
    metrics, pass_ = run_governance_metrics(events, reversal_success_min=0.5)
    assert metrics["reversal_success"] == 0.0
    assert pass_ is False
