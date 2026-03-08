"""
Numerical tolerances and constants for Boundary-Preserving Organization.

Paper symbols: τ_cl (TOL_LUMPABLE), μ_min (MU_MIN), τ_{3.2} (TOL_T32_VIOLATION), δ (DELTA_T33).
Reference: docs/DESIGN.md §5 (Numerical Tolerances); PRD-02 (edge cases, validation).
"""

# τ_cl: lumpability; E_cl(q) < TOL_LUMPABLE treated as zero (Def 2.3, T3.1)
TOL_LUMPABLE = 1e-10

# μ_min: minimum μ(i); below this flag numerical instability (Def 2.2, PRD-02 §2.4)
MU_MIN = 1e-15

# τ_{3.2}: T3.2 bound; allow rounding in E_cl <= m_*^2 * ||K||^2
TOL_T32_VIOLATION = 1e-8

# δ: T3.3 decay slack; allow ratio up to (1 + DELTA_T33) above theoretical decay
DELTA_T33 = 0.01

# Binding index: require at least this many blocks for non-NaN (Estimator 5.4, PRD-02 §5.3)
MIN_BLOCKS_FOR_BINDING_INDEX = 3
