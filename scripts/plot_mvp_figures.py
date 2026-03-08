#!/usr/bin/env python3
"""
MVP figures (PRD-03): closure energy arch (Fig 5), T3.2 scatter.
Saves to docs/figures/ if matplotlib is available.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

def _run() -> None:
    import numpy as np
    from boundary_org import (
        closure_energy,
        m_star_single,
        kernel_l2_norm_squared,
        greedy_coarse_graining,
    )
    from boundary_org.synthetic import make_lumpable_block_diagonal, make_non_lumpable_perturbed

    rng = np.random.default_rng(42)
    fig_dir = ROOT / "docs" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Closure arch (Fig 5): E_cl vs coarseness m (number of blocks)
    # Use greedy trajectory: start identity (m=n), end one block (m=1); E at each step
    n = 8
    syn = make_non_lumpable_perturbed(
        make_lumpable_block_diagonal(n, rng=rng), 0.1, rng=rng
    )
    q_star, trajectory, _ = greedy_coarse_graining(syn.K, syn.mu)
    m_vals = list(range(n, 0, -1))  # n, n-1, ..., 1
    E_vals = trajectory

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping figures. Install with: pip install matplotlib")
        return

    # Figure 5 style: E_cl(q) vs partition coarseness (blocks m)
    fig, ax = plt.subplots()
    ax.plot(m_vals, E_vals, "o-", color="C0")
    ax.set_xlabel("Partition coarseness (blocks m)")
    ax.set_ylabel("$E^{\\mathrm{op}}_{\\mathrm{cl}}(q)$")
    ax.set_title("Closure energy along greedy path (Fig 5 style)")
    ax.axhline(0, color="gray", ls="--", alpha=0.7)
    fig.tight_layout()
    fig.savefig(fig_dir / "closure_arch.png", dpi=150)
    plt.close(fig)
    print(f"Saved {fig_dir / 'closure_arch.png'}")

    # T3.2 scatter: E_cl vs m_*^2 ||K||^2 (points should lie below line y=x)
    N = 100
    E_list = []
    bound_list = []
    for _ in range(N):
        n = rng.integers(4, 8)
        syn = make_lumpable_block_diagonal(n, rng=rng)
        E = closure_energy(syn.K, syn.mu, syn.partition)
        m_star = m_star_single(syn.mu, syn.partition)
        K_sq = kernel_l2_norm_squared(syn.K, syn.mu)
        E_list.append(E)
        bound_list.append(m_star**2 * K_sq)
    E_arr = np.array(E_list)
    B_arr = np.array(bound_list)

    fig, ax = plt.subplots()
    ax.scatter(B_arr, E_arr, alpha=0.6, label="trials")
    lim = max(E_arr.max(), B_arr.max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", label="$E = m_*^2 \\|K\\|^2$")
    ax.set_xlabel("$m_*^2 \\|K\\|^2_{L^2(\\mu)}$")
    ax.set_ylabel("$E^{\\mathrm{op}}_{\\mathrm{cl}}(q)$")
    ax.set_title("T3.2: closure energy vs bound (points below line)")
    ax.legend()
    ax.set_aspect("equal")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    fig.tight_layout()
    fig.savefig(fig_dir / "t32_scatter.png", dpi=150)
    plt.close(fig)
    print(f"Saved {fig_dir / 't32_scatter.png'}")


if __name__ == "__main__":
    _run()
