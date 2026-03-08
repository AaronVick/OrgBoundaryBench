"""
PRD-16: Adversarial and Domain-Grounded Falsification.

Four harsher questions (Q1–Q4) for run reports. Produces an adversarial checklist:
Q1 = reject trivial coarse partition; Q2 = survive intervention/construction; Q3 = beat baselines on real task; Q4 = governance properties.
When multi-construction or real-task data are absent, Q2–Q4 report "Not assessed".
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from .harness import run_harness


def run_adversarial_audit(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    n_random: int = 2,
    rng: np.random.Generator | None = None,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD-16: Compute adversarial checklist Q1–Q4. Q1 from harness (non-trivial q*); Q2–Q4 Not assessed until multi-construction/real data.
    Pass = no assessed item fails (Q1 Pass or Not assessed; Q2–Q4 Not assessed is acceptable).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    _, q_star, success = run_harness(K, mu, n_random=n_random, rng=rng)
    n_blocks = len(q_star)
    # Q1: Does the method reject trivial coarse partitions? (PRD-16 §1)
    q1 = "Pass" if n_blocks >= 2 else "Fail"
    # Q2–Q4: Not assessed without multi-construction, real task, or governance proxy
    q2 = "Not assessed (single kernel construction)"
    q3 = "Not assessed (calibration only)"
    q4 = "Not assessed"
    checklist = {"Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4}
    # Pass iff no assessed item is Fail
    pass_ = q1 != "Fail"
    return (
        {
            "checklist": checklist,
            "n_blocks_q_star": n_blocks,
            "harness_success": success,
        },
        pass_,
    )
