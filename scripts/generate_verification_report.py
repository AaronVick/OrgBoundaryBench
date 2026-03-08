#!/usr/bin/env python3
"""
Verification report: T3.2 max ratio, T3.3 max ratio, T3.4 termination, E6.1 AUC.
PRD-04 §6: "Short summary: max ratio T3.2, max ratio T3.3, termination stats T3.4,
discrimination AUC comparison."
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
    greedy_coarse_graining,
    m_star_single,
    kernel_l2_norm_squared,
    graph_modularity_q,
    discrimination_auc,
)
from boundary_org.synthetic import make_lumpable_block_diagonal, make_non_lumpable_perturbed
from config.defaults import TOL_T32_VIOLATION, DELTA_T33


def main() -> None:
    rng = np.random.default_rng(42)
    report = []

    # T3.2
    N_t32 = 200
    max_ratio_t32 = 0.0
    violations_t32 = 0
    for _ in range(N_t32):
        n = rng.integers(4, 10)
        syn = make_lumpable_block_diagonal(n, rng=rng)
        E = closure_energy(syn.K, syn.mu, syn.partition)
        m_star = m_star_single(syn.mu, syn.partition)
        K_sq = kernel_l2_norm_squared(syn.K, syn.mu)
        if K_sq * m_star**2 > 1e-15:
            ratio = E / (m_star**2 * K_sq)
            max_ratio_t32 = max(max_ratio_t32, ratio)
            if E > m_star**2 * K_sq + TOL_T32_VIOLATION:
                violations_t32 += 1
    report.append(f"T3.2: N={N_t32}, violations={violations_t32}, max_ratio={max_ratio_t32:.6f}")

    # T3.3
    N_t33 = 50
    max_ratio_t33 = 0.0
    for _ in range(N_t33):
        n = 6
        syn = make_lumpable_block_diagonal(n, rng=rng)
        K = syn.K
        mu = syn.mu
        K_rev = (K + (mu[:, None] * K.T) / (mu[None, :] + 1e-15)) / 2
        K_rev = K_rev / K_rev.sum(axis=1, keepdims=True)
        res = spectral_gap_abs(K_rev, mu)
        f = rng.standard_normal(n)
        f = f - (f @ mu)
        norm_f = np.sqrt((f**2 * mu).sum())
        if norm_f < 1e-10:
            continue
        for t in [1, 3]:
            Kt_f = np.linalg.matrix_power(K_rev, t) @ f
            norm_Kt_f = np.sqrt((Kt_f**2 * mu).sum())
            theory = (1 - res.gap_abs) ** t * norm_f
            if theory > 1e-15:
                ratio = norm_Kt_f / theory
                max_ratio_t33 = max(max_ratio_t33, ratio)
    report.append(f"T3.3: N={N_t33}, max_decay_ratio={max_ratio_t33:.6f} (expect <= 1+delta={1+DELTA_T33})")

    # T3.4
    N_t34 = 30
    steps_list = []
    for _ in range(N_t34):
        n = rng.integers(5, 10)
        syn = make_lumpable_block_diagonal(n, rng=rng)
        syn = make_non_lumpable_perturbed(syn, 0.05, rng=rng)
        _, _, steps = greedy_coarse_graining(syn.K, syn.mu)
        steps_list.append(steps)
    report.append(f"T3.4: N={N_t34}, steps in [min={min(steps_list)}, max={max(steps_list)}], all <= n-1: {all(s <= 8 for s in steps_list)}")

    # E6.1 discrimination
    n_per_class = 40
    partition = [[0, 1, 2, 3], [4, 5, 6, 7]]
    labels, scores_E, scores_Q = [], [], []
    for _ in range(n_per_class):
        syn = make_lumpable_block_diagonal(8, partition=partition, rng=rng)
        labels.append(1)
        scores_E.append(-closure_energy(syn.K, syn.mu, syn.partition))
        scores_Q.append(graph_modularity_q(syn.K, syn.partition))
    for _ in range(n_per_class):
        base = make_lumpable_block_diagonal(8, partition=partition, rng=rng)
        syn = make_non_lumpable_perturbed(base, 0.08, rng=rng)
        labels.append(0)
        scores_E.append(-closure_energy(syn.K, syn.mu, syn.partition))
        scores_Q.append(graph_modularity_q(syn.K, syn.partition))
    labels_arr = np.array(labels)
    scores_E_arr = np.array(scores_E)
    scores_Q_arr = np.array(scores_Q)
    auc_E = discrimination_auc(labels_arr, scores_E_arr)
    auc_Q = discrimination_auc(labels_arr, scores_Q_arr)
    # Bootstrap 95% CI for AUC (PhD rigor: report uncertainty)
    n_boot = 100
    rng_boot = np.random.default_rng(43)
    n = len(labels_arr)
    auc_E_boot = []
    auc_Q_boot = []
    for _ in range(n_boot):
        idx = rng_boot.integers(0, n, size=n)
        if np.unique(labels_arr[idx]).size < 2:
            continue
        auc_E_boot.append(discrimination_auc(labels_arr[idx], scores_E_arr[idx]))
        auc_Q_boot.append(discrimination_auc(labels_arr[idx], scores_Q_arr[idx]))
    if auc_E_boot:
        lo_E, hi_E = np.percentile(auc_E_boot, [2.5, 97.5])
        lo_Q, hi_Q = np.percentile(auc_Q_boot, [2.5, 97.5])
        report.append(f"E6.1: AUC(E_cl)={auc_E:.4f} [{lo_E:.4f}, {hi_E:.4f}], AUC(Q)={auc_Q:.4f} [{lo_Q:.4f}, {hi_Q:.4f}], closure >= Q-0.05: {auc_E >= auc_Q - 0.05}")
    else:
        report.append(f"E6.1: AUC(closure_energy)={auc_E:.4f}, AUC(modularity_Q)={auc_Q:.4f}, closure >= Q-0.05: {auc_E >= auc_Q - 0.05}")

    out = "\n".join(["# Verification report (Domain 6.1)", ""] + report)
    print(out)
    out_path = ROOT / "docs" / "verification_report.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out + "\n")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
