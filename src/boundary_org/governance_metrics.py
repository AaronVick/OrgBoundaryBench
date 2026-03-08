"""
PRD-25: Governance Metrics on Real Appeals / Overrides / Reversals.

Contestability capacity χ(d) decomposition (reachability, visibility, alternatives, reversibility);
override latency, reversal success, unattributed residue, unresolved challenge rate.
Pass only if challenge paths can actually alter outcomes (reversal above threshold, unresolved below).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ChallengeEvent:
    """Single challenge/appeal event. PRD-25 §2.2."""
    challenge_id: str
    timestamp_challenge: float  # e.g. seconds since epoch or step index
    timestamp_resolution: float
    outcome: str  # "reversed" | "denied"
    attributable_agent: Optional[str] = None  # None = unattributed


def compute_override_latency(events: List[ChallengeEvent]) -> Dict[str, Any]:
    """Time from challenge to resolution. Returns mean, median, min, max, count."""
    if not events:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    latencies = [e.timestamp_resolution - e.timestamp_challenge for e in events]
    latencies = [max(0, L) for L in latencies]
    latencies.sort()
    n = len(latencies)
    return {
        "mean": sum(latencies) / n,
        "median": latencies[n // 2] if n else 0.0,
        "min": min(latencies),
        "max": max(latencies),
        "count": n,
    }


def compute_reversal_success(events: List[ChallengeEvent]) -> float:
    """Fraction of challenges that resulted in reversal/correction. PRD-25 §2.2."""
    if not events:
        return 0.0
    reversed_count = sum(1 for e in events if (e.outcome or "").lower() == "reversed")
    return reversed_count / len(events)


def compute_unattributed_residue(events: List[ChallengeEvent]) -> float:
    """Fraction of decisions not attributable to an identifiable agent. PRD-25 §2.2."""
    if not events:
        return 0.0
    unattributed = sum(1 for e in events if e.attributable_agent is None or (e.attributable_agent or "").strip() == "")
    return unattributed / len(events)


def compute_unresolved_challenge_rate(events: List[ChallengeEvent]) -> float:
    """Fraction of challenges that did not result in outcome change (denied). PRD-25 §2.2."""
    if not events:
        return 0.0
    denied = sum(1 for e in events if (e.outcome or "").lower() == "denied")
    return denied / len(events)


def chi_decomposition_proxy(events: List[ChallengeEvent]) -> Dict[str, Any]:
    """
    PRD-25 §2.1: χ(d) proxy. We operationalize:
    - Reversibility: reversal_success (direct).
    - Reachability/visibility/alternatives: stub or from event fields if extended.
    """
    return {
        "reversibility": compute_reversal_success(events),
        "reachability": None,  # Would require per-decision data
        "visibility": None,
        "alternatives": None,
    }


def run_governance_metrics(
    events: List[ChallengeEvent],
    *,
    reversal_success_min: float = 0.2,
    unresolved_rate_max: float = 0.9,
    unattributed_max: float = 0.9,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD-25: Compute all metrics; pass iff challenge paths alter outcomes and responsibility is attributable.

    Pass: reversal_success >= reversal_success_min, unresolved_rate <= unresolved_rate_max,
    unattributed <= unattributed_max. Falsification: any threshold violated.
    """
    if not events:
        metrics = {
            "override_latency": compute_override_latency(events),
            "reversal_success": 0.0,
            "unattributed_residue": 0.0,
            "unresolved_challenge_rate": 0.0,
            "chi_proxy": chi_decomposition_proxy(events),
        }
        return metrics, False

    override_latency = compute_override_latency(events)
    reversal_success = compute_reversal_success(events)
    unattributed_residue = compute_unattributed_residue(events)
    unresolved_rate = compute_unresolved_challenge_rate(events)
    chi_proxy = chi_decomposition_proxy(events)

    metrics = {
        "override_latency": override_latency,
        "reversal_success": reversal_success,
        "unattributed_residue": unattributed_residue,
        "unresolved_challenge_rate": unresolved_rate,
        "chi_proxy": chi_proxy,
        "n_events": len(events),
    }

    pass_ = (
        reversal_success >= reversal_success_min
        and unresolved_rate <= unresolved_rate_max
        and unattributed_residue <= unattributed_max
    )
    return metrics, pass_
