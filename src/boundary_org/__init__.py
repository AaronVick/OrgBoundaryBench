"""
Boundary-Preserving Organization: core estimators and synthetic generators.

Paper: Vick, Boundary-Preserving Organization in Dynamical Systems (2025).
PRD-00 (notation), PRD-02 (estimators), PRD-04 (synthetic). See docs/DESIGN.md.
"""

from .operators import closure_energy, closure_operator_matrix, kernel_l2_norm_squared
from .projection import (
    projection_matrix,
    identity_partition,
    single_block_partition,
    partition_from_blocks,
)
from .estimators import (
    spectral_gap_abs,
    SpectralGapResult,
    binding_index,
    misalignment,
    m_star_single,
)
from .greedy import greedy_coarse_graining, greedy_fixed_point
from .baselines import graph_modularity_q, discrimination_auc
from .synthetic import (
    SyntheticKernel,
    make_lumpable_block_diagonal,
    make_lumpable_quotient,
    make_non_lumpable_perturbed,
    make_non_lumpable_random,
)

__all__ = [
    "closure_energy",
    "closure_operator_matrix",
    "kernel_l2_norm_squared",
    "projection_matrix",
    "identity_partition",
    "single_block_partition",
    "partition_from_blocks",
    "spectral_gap_abs",
    "SpectralGapResult",
    "binding_index",
    "misalignment",
    "m_star_single",
    "greedy_coarse_graining",
    "greedy_fixed_point",
    "SyntheticKernel",
    "make_lumpable_block_diagonal",
    "make_lumpable_quotient",
    "make_non_lumpable_perturbed",
    "make_non_lumpable_random",
    "graph_modularity_q",
    "discrimination_auc",
]
