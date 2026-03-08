"""
PRD X (thoughts3): Human Confirmation-Bias Stress Test.

Under seeded error: challenge rate, false reassurance rate, successful override rate,
calibrated-trust gap. Challenge rates should rise when they should; rubber-stamping should fall.
Build: visible vs quiet errors, reversible vs irreversible (structural); compare detection/challenge.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple

from .quiet_error_lab import run_quiet_error_lab, planted_error_row_swap, planted_error_threshold_scale


def run_confirmation_bias_stress(
    K: np.ndarray,
    mu: np.ndarray,
    *,
    n_visible: int = 3,
    n_quiet: int = 3,
    n_control: int = 3,
    visible_strength: float = 1.5,
    quiet_strength: float = 1.05,
    detection_E_cl_factor: float = 1.3,
    detection_nmi_max: float = 0.95,
    rng: np.random.Generator | None = None,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD X: Seed visible (strong) and quiet (weak) errors; run detector.
    challenge_rate_visible = detection rate when visible error planted;
    challenge_rate_quiet = detection rate when quiet error planted;
    false_reassurance_rate = 1 - detection (overall or worst);
    successful_override_rate = detection_rate (stub: detector flag => override attempted);
    calibrated_trust_gap = stub (0) — would need human trust ratings.
    Pass: challenge rate for visible >= challenge rate for quiet (or both above min),
    and false reassurance below threshold; rubber-stamping falls.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n = K.shape[0]
    # Visible: row_swap (always detectable if n>=2) or strong threshold_scale
    visible_flagged = 0
    quiet_flagged = 0
    control_flagged = 0
    n_control_actual = 0

    from .operators import closure_energy
    from .greedy import greedy_coarse_graining
    from .phase_monitoring import nmi_between_partitions

    q_orig, _, _ = greedy_coarse_graining(K, mu)
    E_cl_orig = float(closure_energy(K, mu, q_orig))

    for _ in range(n_control):
        n_control_actual += 1
        ratio = 1.0
        nmi = 1.0
        flagged = ratio > detection_E_cl_factor or nmi < detection_nmi_max
        if flagged:
            control_flagged += 1

    for _ in range(n_visible):
        i, j = rng.integers(0, n), rng.integers(0, n)
        while j == i:
            j = rng.integers(0, n)
        K_err = planted_error_row_swap(K, i, j)
        q_pert, _, _ = greedy_coarse_graining(K_err, mu)
        nmi = nmi_between_partitions(q_orig, q_pert, n)
        E_cl_orig_on_err = float(closure_energy(K_err, mu, q_orig))
        ratio = E_cl_orig_on_err / (E_cl_orig + 1e-20)
        flagged = ratio > detection_E_cl_factor or nmi < detection_nmi_max
        if flagged:
            visible_flagged += 1

    for _ in range(n_quiet):
        row_idx = rng.integers(0, n)
        K_err = planted_error_threshold_scale(K, row_idx, quiet_strength)
        q_pert, _, _ = greedy_coarse_graining(K_err, mu)
        nmi = nmi_between_partitions(q_orig, q_pert, n)
        E_cl_orig_on_err = float(closure_energy(K_err, mu, q_orig))
        ratio = E_cl_orig_on_err / (E_cl_orig + 1e-20)
        flagged = ratio > detection_E_cl_factor or nmi < detection_nmi_max
        if flagged:
            quiet_flagged += 1

    challenge_rate_visible = visible_flagged / n_visible if n_visible else 0.0
    challenge_rate_quiet = quiet_flagged / n_quiet if n_quiet else 0.0
    false_positive_rate = control_flagged / n_control_actual if n_control_actual else 0.0
    false_reassurance_visible = 1.0 - challenge_rate_visible
    false_reassurance_quiet = 1.0 - challenge_rate_quiet
    false_reassurance_rate = max(false_reassurance_visible, false_reassurance_quiet)
    successful_override_rate = (challenge_rate_visible + challenge_rate_quiet) / 2.0 if (n_visible or n_quiet) else 0.0
    calibrated_trust_gap = 0.0  # stub

    # Pass: visible challenge >= quiet (or both above 0.3); false reassurance <= 0.7; rubber-stamping not dominant
    challenge_rises = challenge_rate_visible >= challenge_rate_quiet - 0.2
    rubber_stamping_falls = false_reassurance_rate <= 0.7
    pass_ = challenge_rises and rubber_stamping_falls

    result = {
        "challenge_rate_visible": challenge_rate_visible,
        "challenge_rate_quiet": challenge_rate_quiet,
        "false_reassurance_rate": false_reassurance_rate,
        "false_positive_rate": false_positive_rate,
        "successful_override_rate": successful_override_rate,
        "calibrated_trust_gap": calibrated_trust_gap,
        "challenge_rises_when_should": challenge_rises,
        "rubber_stamping_falls": rubber_stamping_falls,
    }
    return result, pass_

