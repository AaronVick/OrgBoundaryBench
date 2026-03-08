#!/usr/bin/env python3
"""
Conjecture 10.1 numerical probe (PRD-07 §5).

For reversible K and non-lumpable q, the conjecture claims
  m_*(q) >= c * E_cl(q) / (gap_abs(K) * ||K||^2)
for some c > 0 depending on |S|. Equivalently, the ratio
  R := m_*(q) * gap_abs(K) * ||K||^2 / E_cl(q)
should be bounded below by some c > 0. This script samples many (K, q), computes R,
and reports min R, distribution, and whether a counterexample (R near 0 or very small) was found.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np
from boundary_org import (
    closure_energy,
    spectral_gap_abs,
    m_star_single,
    kernel_l2_norm_squared,
)
from boundary_org.synthetic import make_lumpable_block_diagonal, make_non_lumpable_perturbed
from config.defaults import TOL_LUMPABLE


def make_reversible(K: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Symmetrize to detailed balance: K_rev with mu_i K_rev_ij = mu_j K_rev_ji."""
    K_rev = (K + (mu[:, None] * K.T) / (mu[None, :] + 1e-15)) / 2
    return K_rev / K_rev.sum(axis=1, keepdims=True)


def main() -> None:
    rng = np.random.default_rng(44)
    N = 500
    ratios = []
    n_vals = []

    for _ in range(N):
        n = rng.integers(4, 12)
        base = make_lumpable_block_diagonal(n, rng=rng)
        syn = make_non_lumpable_perturbed(base, epsilon=rng.uniform(0.03, 0.15), rng=rng)
        K = make_reversible(syn.K, syn.mu)
        mu = syn.mu
        q = syn.partition

        E = closure_energy(K, mu, q)
        if E < TOL_LUMPABLE:
            continue
        m_star = m_star_single(mu, q)
        res = spectral_gap_abs(K, mu)
        K_sq = kernel_l2_norm_squared(K, mu)
        # R = m_* * gap_abs * ||K||^2 / E_cl (conjecture: R >= c > 0)
        if res.gap_abs * K_sq < 1e-15:
            continue
        R = m_star * res.gap_abs * K_sq / E
        if np.isfinite(R) and R > 0:
            ratios.append(R)
            n_vals.append(n)

    ratios = np.array(ratios)
    if len(ratios) == 0:
        print("Conjecture 10.1 probe: no valid (reversible K, non-lumpable q) with E_cl > 0")
        return

    min_R = float(np.min(ratios))
    p25, p50, p75 = np.percentile(ratios, [25, 50, 75])
    print("# Conjecture 10.1 probe (R = m_* * gap_abs * ||K||^2 / E_cl)")
    print(f"N_valid = {len(ratios)}")
    print(f"min(R) = {min_R:.6f}")
    print(f"percentiles: 25%={p25:.4f}, 50%={p50:.4f}, 75%={p75:.4f}")
    counterexample_threshold = 0.01
    if min_R < counterexample_threshold:
        print(f"Counterexample (R < {counterexample_threshold}): YES")
    else:
        print(f"Counterexample (R < {counterexample_threshold}): NO")
    out_path = ROOT / "docs" / "conjecture_10_1_probe.txt"
    out_path.write_text(
        f"# Conjecture 10.1 probe\nN={len(ratios)}, min_R={min_R:.6f}, counterexample={min_R < counterexample_threshold}\n"
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
