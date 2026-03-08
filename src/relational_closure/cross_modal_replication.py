"""
PRD VIII (thoughts3): Cross-Modal Sedation Replication.

Replicate RCTI discrimination on a second modality; test sign(ΔT_A) = sign(ΔT_B).
Directionally consistent condition effects across modalities. Falsification: direction
reverses across modalities (modality-specific artifact).
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple

from .pipeline import run_pipeline
from .sedation_discrimination import topology_scalar_summary


def mean_pe_by_condition(
    samples: List[Tuple[np.ndarray, int]],
    *,
    tau: float = 0.1,
    use_gudhi: bool = True,
) -> Dict[int, float]:
    """Mean persistence entropy per condition (label). Returns {label: mean_PE}."""
    by_label: Dict[int, List[float]] = {}
    for W, label in samples:
        res = run_pipeline(W, threshold=None, max_dim=4, tau=tau, use_gudhi=use_gudhi)
        pe = topology_scalar_summary(res)
        by_label.setdefault(label, []).append(pe)
    return {k: float(np.mean(v)) for k, v in by_label.items()}


def condition_effect_direction(
    samples: List[Tuple[np.ndarray, int]],
    *,
    tau: float = 0.1,
    use_gudhi: bool = True,
    condition_compare: Tuple[int, int] = (0, 1),
) -> float:
    """
    ΔT = mean(PE | condition B) - mean(PE | condition A). Returns ΔT (positive => B has higher PE).
    For binary labels, condition_compare = (0, 1) gives ΔT = mean_PE_1 - mean_PE_0.
    """
    means = mean_pe_by_condition(samples, tau=tau, use_gudhi=use_gudhi)
    a, b = condition_compare
    mean_a = means.get(a, 0.0)
    mean_b = means.get(b, 0.0)
    return mean_b - mean_a


def run_cross_modal_replication(
    samples_modality_a: List[Tuple[np.ndarray, int]],
    samples_modality_b: List[Tuple[np.ndarray, int]],
    *,
    tau: float = 0.1,
    use_gudhi: bool = True,
    condition_compare: Tuple[int, int] = (0, 1),
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD VIII: Compute ΔT_A and ΔT_B; pass iff sign(ΔT_A) == sign(ΔT_B) (directionally consistent).
    Falsification: sign(ΔT_A) != sign(ΔT_B) => modality-specific artifact, no robust claim.
    """
    delta_a = condition_effect_direction(
        samples_modality_a, tau=tau, use_gudhi=use_gudhi, condition_compare=condition_compare
    )
    delta_b = condition_effect_direction(
        samples_modality_b, tau=tau, use_gudhi=use_gudhi, condition_compare=condition_compare
    )
    sign_a = 1 if delta_a > 0 else (-1 if delta_a < 0 else 0)
    sign_b = 1 if delta_b > 0 else (-1 if delta_b < 0 else 0)
    direction_consistent = sign_a == sign_b and (sign_a != 0 or sign_b != 0)
    # If both zero, treat as consistent (no effect in either)
    if sign_a == 0 and sign_b == 0:
        direction_consistent = True
    pass_ = direction_consistent
    result = {
        "delta_T_modality_a": float(delta_a),
        "delta_T_modality_b": float(delta_b),
        "sign_a": sign_a,
        "sign_b": sign_b,
        "direction_consistent": direction_consistent,
        "n_a": len(samples_modality_a),
        "n_b": len(samples_modality_b),
    }
    return result, pass_

