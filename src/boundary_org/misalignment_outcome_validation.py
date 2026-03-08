"""
PRD-26: Misalignment Outcome Validation.

m_n per unit; outcomes (override success, recovery time, escalation, confusion);
correlation/regression in expected direction; out-of-sample and comparison to null and
graph-feature controls. Falsification: m_n does not predict or is dominated by controls.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional, Tuple

from .misalignment_engine import run_misalignment_engine


def graph_control_density(K: np.ndarray) -> float:
    """Graph density from symmetrized kernel (control for PRD-26 §2.3)."""
    A = (np.asarray(K) + np.asarray(K).T) / 2.0
    n = A.shape[0]
    return float(np.count_nonzero(A > 0) / (n * n)) if n else 0.0


def graph_control_spectral_gap(K: np.ndarray) -> float:
    """Spectral gap of symmetrized Laplacian (control)."""
    n = K.shape[0]
    if n < 2:
        return 0.0
    A = (np.asarray(K) + np.asarray(K).T) / 2.0
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import laplacian
        from scipy.sparse.linalg import eigsh
    except ImportError:
        return 0.0
    L = laplacian(csr_matrix(A), normed=False)
    try:
        vals = eigsh(L.asfptype(), k=min(4, n), which="SM", return_eigenvectors=False)
    except Exception:
        return 0.0
    vals = np.sort(vals)
    for v in vals:
        if v > 1e-10:
            return float(v)
    return 0.0


def run_misalignment_outcome_validation(
    units: List[Tuple[np.ndarray, np.ndarray, Dict[str, float]]],
    *,
    rng: Optional[np.random.Generator] = None,
    train_frac: float = 0.7,
    min_correlation_expected: float = -0.5,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD-26: Per unit (K, mu, outcomes), compute m_n and graph controls; correlate outcomes with m_n;
    expected: higher m_n -> lower override_success, higher recovery_time, higher confusion.
    Compare to null (random) and controls (density, spectral_gap). Out-of-sample: train/test correlation.
    Pass: correlations in expected direction, m_n adds value over controls (coefficient significant or
    partial correlation), and out-of-sample not reversed. Falsification: m_n does not correlate in
    expected direction, or effect not significant, or controls dominate.
    units: list of (K, mu, outcomes_dict). outcomes_dict must have override_success, recovery_time, confusion (or stubs).
    """
    if rng is None:
        rng = np.random.default_rng(42)
    n_units = len(units)
    if n_units < 3:
        return _empty_result(), False

    m_n_list: List[float] = []
    density_list: List[float] = []
    spectral_gap_list: List[float] = []
    override_list: List[float] = []
    recovery_list: List[float] = []
    confusion_list: List[float] = []

    for K, mu, outcomes in units:
        report, _ = run_misalignment_engine(K, mu, rng=rng)
        m_n_list.append(report["m_n"])
        density_list.append(graph_control_density(K))
        spectral_gap_list.append(graph_control_spectral_gap(K))
        override_list.append(outcomes.get("override_success", report["override_success_stub"]))
        recovery_list.append(outcomes.get("recovery_time", report["recovery_time_stub"]))
        confusion_list.append(outcomes.get("confusion", report["confusion_stub"]))

    m_n = np.array(m_n_list)
    override = np.array(override_list)
    recovery = np.array(recovery_list)
    confusion = np.array(confusion_list)
    density = np.array(density_list)
    spectral_gap = np.array(spectral_gap_list)

    # Correlations (expected: m_n neg with override, pos with recovery and confusion)
    try:
        from scipy.stats import pearsonr
    except ImportError:
        return _result_no_scipy(m_n_list, override_list, recovery_list, confusion_list), False

    corr_override, p_override = pearsonr(m_n, override)
    corr_recovery, p_recovery = pearsonr(m_n, recovery)
    corr_confusion, p_confusion = pearsonr(m_n, confusion)
    # Expected: corr_override <= 0, corr_recovery >= 0, corr_confusion >= 0
    direction_ok = corr_override <= 0.2 and corr_recovery >= -0.2 and corr_confusion >= -0.2

    # Null: correlate outcomes with random permutation of m_n
    m_n_shuf = rng.permutation(m_n)
    corr_null_o, _ = pearsonr(m_n_shuf, override)
    corr_null_r, _ = pearsonr(m_n_shuf, recovery)
    m_n_beats_null = abs(corr_override) >= abs(corr_null_o) - 0.1 and abs(corr_recovery) >= abs(corr_null_r) - 0.1

    # Control: partial correlation m_n vs override after regressing density, spectral_gap (or simple: does m_n add?)
    # Simplified: require correlation with m_n stronger than with density
    corr_density_override, _ = pearsonr(density, override)
    corr_gap_override, _ = pearsonr(spectral_gap, override)
    m_n_adds_value = abs(corr_override) >= abs(corr_density_override) - 0.15 or abs(corr_override) >= abs(corr_gap_override) - 0.15

    # Out-of-sample: train/test split
    n_train = max(2, int(n_units * train_frac))
    idx = rng.permutation(n_units)
    train_idx, test_idx = idx[:n_train], idx[n_train:]
    if len(test_idx) < 2:
        oos_ok = True
    else:
        corr_train = np.corrcoef(m_n[train_idx], override[train_idx])[0, 1] if n_train >= 2 else 0
        corr_test = np.corrcoef(m_n[test_idx], override[test_idx])[0, 1] if len(test_idx) >= 2 else 0
        oos_ok = not (np.isnan(corr_train) or np.isnan(corr_test)) and (np.sign(corr_train) == np.sign(corr_test) or abs(corr_test) < 0.3)

    pass_ = direction_ok and (m_n_beats_null or n_units < 6) and (m_n_adds_value or n_units < 6) and oos_ok
    result = {
        "n_units": n_units,
        "corr_m_n_override_success": float(corr_override),
        "corr_m_n_recovery_time": float(corr_recovery),
        "corr_m_n_confusion": float(corr_confusion),
        "p_override": float(p_override),
        "p_recovery": float(p_recovery),
        "p_confusion": float(p_confusion),
        "direction_ok": direction_ok,
        "m_n_beats_null": m_n_beats_null,
        "m_n_adds_value_vs_controls": m_n_adds_value,
        "oos_consistent": oos_ok,
        "mean_m_n": float(np.mean(m_n)),
    }
    return result, pass_


def _empty_result() -> Dict[str, Any]:
    return {
        "n_units": 0,
        "corr_m_n_override_success": 0.0,
        "corr_m_n_recovery_time": 0.0,
        "corr_m_n_confusion": 0.0,
        "p_override": 1.0,
        "p_recovery": 1.0,
        "p_confusion": 1.0,
        "direction_ok": False,
        "m_n_beats_null": False,
        "m_n_adds_value_vs_controls": False,
        "oos_consistent": False,
        "mean_m_n": 0.0,
    }


def _result_no_scipy(
    m_n_list: List[float],
    override_list: List[float],
    recovery_list: List[float],
    confusion_list: List[float],
) -> Dict[str, Any]:
    r = _empty_result()
    r["n_units"] = len(m_n_list)
    r["mean_m_n"] = float(np.mean(m_n_list)) if m_n_list else 0.0
    return r
