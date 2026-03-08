"""
Persistence barcode and Betti numbers from directed flag complex.

Uses gudhi when available (SimplexTree + persistence); otherwise cycle-rank proxy for β₁.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

# Optional gudhi for full persistence
try:
    import gudhi
    _GUDHI_AVAILABLE = True
except ImportError:
    _GUDHI_AVAILABLE = False


def _simplices_to_sorted_by_dim_and_birth(
    simplices_with_birth: List[Tuple[Tuple[int, ...], float]],
) -> List[Tuple[Tuple[int, ...], float]]:
    """Sort so faces come before cofaces: (dimension, birth) ascending. Vertices: birth=0."""
    def key(item: Tuple[Tuple[int, ...], float]) -> Tuple[int, float]:
        s, b = item
        dim = len(s) - 1
        birth = b if dim > 0 else 0.0
        return (dim, birth)
    return sorted(simplices_with_birth, key=key)


def barcode_from_complex(
    simplices_with_birth: List[Tuple[Tuple[int, ...], float]],
    use_gudhi: bool = True,
) -> Dict[str, Any]:
    """
    Compute persistence barcode from list of (simplex, birth).

    If use_gudhi and gudhi available: use SimplexTree and persistence().
    Otherwise: return barcode with only β₁ proxy from cycle rank (edges - vertices + 1 for 1-component graph).
    """
    sorted_simplices = _simplices_to_sorted_by_dim_and_birth(simplices_with_birth)
    if use_gudhi and _GUDHI_AVAILABLE and sorted_simplices:
        st = gudhi.SimplexTree()
        for vertices, birth in sorted_simplices:
            dim = len(vertices) - 1
            filt = birth if dim > 0 else 0.0
            st.insert(list(vertices), filtration=filt)
        st.compute_persistence()
        # Build barcode dict: dim -> list of (birth, death)
        barcode: Dict[int, List[Tuple[float, float]]] = {}
        for dim in range(st.dimension() + 1):
            barcode[dim] = []
        for (dim, (birth, death)) in st.persistence():
            if death == float("inf"):
                death = birth + 1.0  # cap for JSON
            barcode[dim].append((float(birth), float(death)))
        return {
            "barcode": barcode,
            "method": "gudhi",
            "dimension": st.dimension() if hasattr(st, "dimension") else max(barcode.keys()) if barcode else 0,
        }
    # Fallback: no gudhi or empty - compute cycle-rank proxy from 1-skeleton
    edges = [(s, b) for s, b in sorted_simplices if len(s) == 2]
    vertices = set()
    for (a, b), _ in edges:
        vertices.add(a)
        vertices.add(b)
    n_v = len(vertices)
    n_e = len(edges)
    # Single component proxy: β₁ ≈ n_e - n_v + 1 (cycle rank)
    beta1_proxy = max(0, n_e - n_v + 1)
    barcode_fallback = {
        0: [(0.0, 0.0)],  # one component
        1: [(0.0, 0.5)] * beta1_proxy if beta1_proxy else [],
    }
    return {
        "barcode": barcode_fallback,
        "method": "cycle_rank_proxy",
        "dimension": 1,
        "beta1_proxy": beta1_proxy,
    }


def betti_from_barcode(barcode_dict: Dict[str, Any]) -> Dict[int, int]:
    """Extract Betti numbers from barcode: β_k = number of bars in dimension k."""
    barcode = barcode_dict.get("barcode", {})
    betti = {}
    for dim, bars in barcode.items():
        betti[int(dim)] = len(bars)
    return betti


def persistence_entropy(barcode_dict: Dict[str, Any]) -> float:
    """PE = -Σ p_i log(p_i), p_i = lifespan_i / Σ lifespan_j. C1/C3/C4 imply PE > 0."""
    barcode = barcode_dict.get("barcode", {})
    lifespans: List[float] = []
    for bars in barcode.values():
        for (birth, death) in bars:
            lifespans.append(max(0.0, death - birth))
    total = sum(lifespans)
    if total <= 0:
        return 0.0
    import math
    pe = 0.0
    for L in lifespans:
        if L > 0:
            p = L / total
            pe -= p * math.log(p)
    return float(pe)


def bottleneck_distance(
    barcode1: Dict[int, List[Tuple[float, float]]],
    barcode2: Dict[int, List[Tuple[float, float]]],
) -> float:
    """
    Approximate bottleneck distance between two barcodes (max over dimensions of sup-inf matching distance).
    Simplified: max over dimensions of the max of (birth diff, death diff) for matched bars.
    For full d_B use gudhi.bottleneck_distance if available.
    """
    try:
        import gudhi
        d0 = gudhi.bottleneck_distance(barcode1.get(0, []), barcode2.get(0, []))
        d1 = gudhi.bottleneck_distance(barcode1.get(1, []), barcode2.get(1, []))
        return max(d0, d1)
    except Exception:
        # Fallback: L_inf difference of sorted lifespans (very crude)
        def norms(b: Dict[int, List[Tuple[float, float]]]) -> List[float]:
            out = []
            for bars in b.values():
                for (birth, death) in bars:
                    out.append(death - birth)
            return sorted(out, reverse=True)
        a1, a2 = norms(barcode1), norms(barcode2)
        if not a1 and not a2:
            return 0.0
        if not a1 or not a2:
            return max(a1 + a2)
        return float(max(abs(a1[i] - a2[i]) for i in range(min(len(a1), len(a2)))))
