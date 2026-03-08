"""
End-to-end RCTI pipeline: directed graph → barcode → C1/C3/C4b/C2F.

Single-window run produces barcode and condition checks; optional second graph for C2F (S').
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from relational_closure.directed_flag import directed_flag_complex
from relational_closure.persistence import barcode_from_complex, betti_from_barcode, persistence_entropy
from relational_closure.conditions import check_C1, check_C3, check_C4b, compute_C2F


def run_pipeline(
    W: np.ndarray,
    threshold: float | None = None,
    max_dim: int = 4,
    tau: float = 0.1,
    use_gudhi: bool = True,
    W_sub: np.ndarray | None = None,
    node_sub: List[int] | None = None,
) -> Dict[str, Any]:
    """
    Run RCTI pipeline on directed weight matrix W.

    W: n x n nonnegative directed weights.
    threshold: if set, only edges with weight >= threshold (else all).
    max_dim: max simplex dimension.
    tau: C1 lifespan threshold.
    use_gudhi: use gudhi for persistence when available.
    W_sub / node_sub: if provided, compute C2F using sub-complex (S').
      Either pass W_sub = induced subgraph matrix, or node_sub = list of vertex indices in S'.
    Returns dict: barcode_dict, betti, PE, C1 (ok, msg), C4b (ok, msg), C2F (float or None).
    """
    simplices = directed_flag_complex(W, threshold=threshold, max_dim=max_dim)
    barcode_dict = barcode_from_complex(simplices, use_gudhi=use_gudhi)
    betti = betti_from_barcode(barcode_dict)
    pe = persistence_entropy(barcode_dict)
    c1_ok, c1_msg = check_C1(barcode_dict, tau=tau)
    c4b_ok, c4b_msg = check_C4b(barcode_dict)

    c2f_val = None
    if W_sub is not None or node_sub is not None:
        if node_sub is not None:
            # Induced subgraph: matrix of size len(node_sub) x len(node_sub)
            idx = sorted(set(node_sub))
            k = len(idx)
            W_sub = np.zeros((k, k))
            for i, vi in enumerate(idx):
                for j, vj in enumerate(idx):
                    if i != j:
                        W_sub[i, j] = W[vi, vj]
            sub_simplices = directed_flag_complex(W_sub, threshold=threshold, max_dim=max_dim)
        else:
            sub_simplices = directed_flag_complex(W_sub, threshold=threshold, max_dim=max_dim)
        barcode_sub = barcode_from_complex(sub_simplices, use_gudhi=use_gudhi)
        betti_sub = betti_from_barcode(barcode_sub)
        c2f_val = compute_C2F(betti, betti_sub, beta_relative=None)

    return {
        "barcode_dict": barcode_dict,
        "betti": betti,
        "persistence_entropy": pe,
        "C1": {"satisfied": c1_ok, "message": c1_msg},
        "C4b": {"satisfied": c4b_ok, "message": c4b_msg},
        "C2F": c2f_val,
        "n_simplices": len(simplices),
        "method": barcode_dict.get("method", "unknown"),
    }


def run_pipeline_sweep(
    W: np.ndarray,
    thresholds: List[float],
    max_dim: int = 4,
    tau: float = 0.1,
) -> List[Dict[str, Any]]:
    """Run pipeline at each threshold; for C3 we need two time windows (two W's)."""
    return [run_pipeline(W, threshold=t, max_dim=max_dim, tau=tau) for t in thresholds]
