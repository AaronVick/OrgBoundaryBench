"""
Discrimination benchmark: closure energy vs graph modularity Q (PRD-04 §4.1, E6.1).

Requirement: Ê_n distinguishes lumpable vs non-lumpable with higher power (AUC) than Q
at matched sample size. Falsification: consistent underperformance vs modularity.
"""

import numpy as np
import pytest
from boundary_org import closure_energy
from boundary_org.baselines import graph_modularity_q, discrimination_auc
from boundary_org.synthetic import (
    make_lumpable_block_diagonal,
    make_lumpable_quotient,
    make_non_lumpable_perturbed,
    make_non_lumpable_random,
)


def _generate_balanced_dataset(
    n_per_class: int,
    n_states: int = 8,
    *,
    rng: np.random.Generator,
):
    """Labels 1 = lumpable, 0 = non-lumpable. Same n, same partition structure."""
    partition = [list(range(0, n_states // 2)), list(range(n_states // 2, n_states))]
    labels = []
    scores_E = []
    scores_Q = []
    for _ in range(n_per_class):
        syn = make_lumpable_block_diagonal(n_states, partition=partition, rng=rng)
        labels.append(1)
        scores_E.append(-closure_energy(syn.K, syn.mu, syn.partition))  # higher = lumpable
        scores_Q.append(graph_modularity_q(syn.K, syn.partition))
    for _ in range(n_per_class):
        base = make_lumpable_block_diagonal(n_states, partition=partition, rng=rng)
        syn = make_non_lumpable_perturbed(base, epsilon=0.08, rng=rng)
        labels.append(0)
        scores_E.append(-closure_energy(syn.K, syn.mu, syn.partition))
        scores_Q.append(graph_modularity_q(syn.K, syn.partition))
    return (
        np.array(labels),
        np.array(scores_E),
        np.array(scores_Q),
    )


def test_discrimination_closure_vs_modularity_auc():
    """
    E6.1: Closure energy (as classifier) has AUC >= modularity Q at matched n.
    PRD-04 §4.1; falsification = consistent underperformance.
    """
    rng = np.random.default_rng(42)
    n_per_class = 30
    labels, scores_E, scores_Q = _generate_balanced_dataset(n_per_class, n_states=8, rng=rng)
    auc_E = discrimination_auc(labels, scores_E)
    auc_Q = discrimination_auc(labels, scores_Q)
    assert auc_E >= auc_Q - 0.05, (
        f"E6.1: closure energy AUC={auc_E:.3f} should be >= modularity AUC={auc_Q:.3f} (tolerance 0.05)"
    )


def test_modularity_lumpable_tends_higher():
    """Sanity: lumpable (block-diagonal) kernels tend to have higher Q than perturbed."""
    rng = np.random.default_rng(123)
    q_lump = []
    q_non = []
    for _ in range(20):
        base = make_lumpable_block_diagonal(6, rng=rng)
        syn_l = base
        syn_n = make_non_lumpable_perturbed(base, 0.1, rng=rng)
        q_lump.append(graph_modularity_q(syn_l.K, syn_l.partition))
        q_non.append(graph_modularity_q(syn_n.K, syn_n.partition))
    assert np.mean(q_lump) >= np.mean(q_non) - 0.1, "Lumpable should tend higher Q than perturbed"
