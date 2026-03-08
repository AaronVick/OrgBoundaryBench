"""
Closure conditions C1–C4 and C2F (PRD-13, paper §3.3–3.5).

C1: Topological non-triviality (persistent H₁, lifespan > τ).
C2: Self-referential inclusion → C2F fidelity metric.
C3: Dynamical persistence (barcode stability d_B < δ across windows).
C4b: Compositional coherence proxy (β_k ≥ 2 for some k ≥ 2).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from relational_closure.persistence import betti_from_barcode, bottleneck_distance


def check_C1(
    barcode_dict: Dict[str, Any],
    tau: float = 0.1,
) -> Tuple[bool, str]:
    """
    C1: At least one 1-dim bar with lifespan > τ at matched density.
    Returns (satisfied, message).
    """
    barcode = barcode_dict.get("barcode", {})
    bars_1 = barcode.get(1, [])
    if not bars_1:
        return False, "C1: no β₁ bars (no persistent 1-cycles)"
    lifespans = [death - birth for (birth, death) in bars_1]
    if max(lifespans) > tau:
        return True, f"C1: satisfied (max β₁ lifespan={max(lifespans):.4f} > τ={tau})"
    return False, f"C1: not satisfied (max β₁ lifespan={max(lifespans):.4f} ≤ τ={tau})"


def check_C3(
    barcode_dict_t1: Dict[str, Any],
    barcode_dict_t2: Dict[str, Any],
    delta: float = 0.5,
) -> Tuple[bool, float, str]:
    """
    C3: Barcode stability across time: d_B(B(t), B(t+1)) < δ.
    Returns (satisfied, d_B, message).
    """
    b1 = barcode_dict_t1.get("barcode", {})
    b2 = barcode_dict_t2.get("barcode", {})
    d_B = bottleneck_distance(b1, b2)
    satisfied = d_B < delta
    msg = f"C3: d_B={d_B:.4f} {'< δ' if satisfied else '≥ δ'} (δ={delta})"
    return satisfied, d_B, msg


def check_C4b(barcode_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """
    C4b: Non-trivial β_k for k ≥ 2 (higher-dimensional cavities).
    """
    betti = betti_from_barcode(barcode_dict)
    higher = sum(betti.get(k, 0) for k in betti if k >= 2)
    if higher > 0:
        return True, f"C4b: satisfied (Σ β_k for k≥2 = {higher})"
    return False, "C4b: no higher-dimensional features (β_k=0 for k≥2)"


def compute_C2F(
    beta_whole: Dict[int, int],
    beta_sub: Dict[int, int],
    beta_relative: Dict[int, int] | None = None,
) -> float:
    """
    Closure fidelity C2F = 1 - Σ_k w_k β_k(S,S') / Σ_k w_k β_k(S).
    If beta_relative not provided, use proxy: 1 - Σ β_k(S')/Σ β_k(S) (approximation).
    When Σ β_k(S)=0, return 0 by convention.
    """
    w = 1.0  # default weight per dimension
    total_s = sum(beta_whole.get(k, 0) * w for k in beta_whole)
    if total_s <= 0:
        return 0.0
    if beta_relative is not None:
        rel = sum(beta_relative.get(k, 0) * w for k in beta_relative)
    else:
        # Proxy: what S' misses = total_s - sum in S' (only if S' ⊆ S; else use total_s - overlap)
        total_sub = sum(beta_sub.get(k, 0) * w for k in beta_sub)
        rel = max(0, total_s - total_sub)
    return float(max(0.0, min(1.0, 1.0 - rel / total_s)))
