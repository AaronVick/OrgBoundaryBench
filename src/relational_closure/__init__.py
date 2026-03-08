"""
Relational Closure / Topology of Interiority (RCTI).

Empirical pipeline: directed graph → directed flag complex → persistent homology
→ conditions C1–C4, C2F (PRD-13, Vick *Relational Closure and the Topology of Interiority*).
"""

from relational_closure.directed_flag import directed_flag_complex, enumerate_directed_cliques
from relational_closure.persistence import barcode_from_complex, betti_from_barcode, persistence_entropy
from relational_closure.conditions import check_C1, check_C3, check_C4b, compute_C2F
from relational_closure.pipeline import run_pipeline

__all__ = [
    "directed_flag_complex",
    "enumerate_directed_cliques",
    "barcode_from_complex",
    "betti_from_barcode",
    "persistence_entropy",
    "check_C1",
    "check_C3",
    "check_C4b",
    "compute_C2F",
    "run_pipeline",
]
