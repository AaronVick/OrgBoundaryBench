"""
PRD-24: Public Incident-Coupled Phase Monitoring.

Rolling (m_cl, boundary switch) and alert flags; lead time to incident; false positive burden;
comparison to density/entropy/spectral-gap drift baselines. Pass: phase adds value or is not worse.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple

from .phase_monitoring import run_phase_monitoring


def _kernel_to_adjacency(K: np.ndarray) -> np.ndarray:
    """Symmetrized adjacency from kernel for baseline stats."""
    return (np.asarray(K) + np.asarray(K).T) / 2.0


def _density(A: np.ndarray) -> float:
    """Edge density (nonzero count / n^2)."""
    n = A.shape[0]
    if n == 0:
        return 0.0
    return float(np.count_nonzero(A > 0) / (n * n))


def _entropy_degrees(A: np.ndarray) -> float:
    """Entropy of degree distribution."""
    n = A.shape[0]
    if n == 0:
        return 0.0
    deg = A.sum(axis=1)
    total = deg.sum()
    if total <= 0:
        return 0.0
    p = deg / total
    p = p[p > 0]
    return float(-np.sum(p * np.log(p + 1e-20)))


def _spectral_gap(A: np.ndarray) -> float:
    """Spectral gap of Laplacian (smallest non-zero eigenvalue)."""
    n = A.shape[0]
    if n < 2:
        return 0.0
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


def _parse_alert_steps_from_flags(flags: List[str]) -> List[int]:
    """Extract step indices from phase flags (e.g. 'step_2: abrupt_switch' -> 2)."""
    steps = []
    for f in flags:
        if f.startswith("step_"):
            try:
                step_str = f.split(":")[0].replace("step_", "").strip()
                steps.append(int(step_str))
            except ValueError:
                pass
    return sorted(set(steps))


def compute_baseline_drift_alerts(
    kernels: List[Tuple[np.ndarray, np.ndarray]],
    *,
    drift_quantile_threshold: float = 0.9,
) -> Dict[str, List[int]]:
    """
    PRD-24 §2.4: Density, entropy, spectral-gap per window; drift = |v_t - v_{t-1}|;
    alert when drift exceeds quantile of all drifts. Returns baseline name -> list of alert step indices.
    """
    if len(kernels) < 2:
        return {"density_drift": [], "entropy_drift": [], "spectral_gap_drift": []}
    densities = [_density(_kernel_to_adjacency(K)) for K, _ in kernels]
    entropies = [_entropy_degrees(_kernel_to_adjacency(K)) for K, _ in kernels]
    gaps = [_spectral_gap(_kernel_to_adjacency(K)) for K, _ in kernels]
    d_drift = [abs(densities[i] - densities[i - 1]) for i in range(1, len(densities))]
    e_drift = [abs(entropies[i] - entropies[i - 1]) for i in range(1, len(entropies))]
    g_drift = [abs(gaps[i] - gaps[i - 1]) for i in range(1, len(gaps))]
    thresh_d = np.quantile(d_drift, drift_quantile_threshold) if d_drift else 0
    thresh_e = np.quantile(e_drift, drift_quantile_threshold) if e_drift else 0
    thresh_g = np.quantile(g_drift, drift_quantile_threshold) if g_drift else 0
    alerts_d = [i for i in range(1, len(densities)) if d_drift[i - 1] >= thresh_d - 1e-12]
    alerts_e = [i for i in range(1, len(entropies)) if e_drift[i - 1] >= thresh_e - 1e-12]
    alerts_g = [i for i in range(1, len(gaps)) if g_drift[i - 1] >= thresh_g - 1e-12]
    return {"density_drift": alerts_d, "entropy_drift": alerts_e, "spectral_gap_drift": alerts_g}


def lead_time_and_fp(
    alert_steps: List[int],
    incident_steps: List[int],
    *,
    fp_window: int = 2,
) -> Tuple[float, float, int]:
    """
    Lead time = median(incident_step - last_alert_before_incident). Steps.
    False positive = alert with no incident in [alert, alert+fp_window]. Returns (median_lead, fp_rate, n_fp).
    """
    if not incident_steps:
        n_fp = sum(1 for a in alert_steps if True)  # all alerts are FP if no incidents
        return 0.0, (len(alert_steps) / len(alert_steps)) if alert_steps else 0.0, n_fp
    lead_times = []
    for inc in incident_steps:
        before = [a for a in alert_steps if a < inc]
        if before:
            lead_times.append(inc - max(before))
    median_lead = float(np.median(lead_times)) if lead_times else 0.0
    n_fp = 0
    for a in alert_steps:
        has_incident = any(a <= inc < a + fp_window for inc in incident_steps)
        if not has_incident:
            n_fp += 1
    fp_rate = n_fp / len(alert_steps) if alert_steps else 0.0
    return median_lead, fp_rate, n_fp


def run_incident_phase_monitoring(
    kernels: List[Tuple[np.ndarray, np.ndarray]],
    incident_steps: List[int],
    *,
    abrupt_nmi_threshold: float = 0.8,
    rising_window: int = 2,
    fp_window: int = 2,
    drift_quantile_threshold: float = 0.9,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD-24: Run phase monitoring; compute phase alert steps; lead time and FP;
    same for density/entropy/spectral-gap drift; pass iff phase is not worse than best baseline on lead time or FP.
    """
    trajectory, flags = run_phase_monitoring(
        kernels, abrupt_nmi_threshold=abrupt_nmi_threshold, rising_window=rising_window
    )
    phase_alert_steps = _parse_alert_steps_from_flags(flags)
    baseline_alerts = compute_baseline_drift_alerts(kernels, drift_quantile_threshold=drift_quantile_threshold)

    median_lead_phase, fp_rate_phase, n_fp_phase = lead_time_and_fp(phase_alert_steps, incident_steps, fp_window=fp_window)
    baseline_lead: Dict[str, float] = {}
    baseline_fp: Dict[str, float] = {}
    for name, steps in baseline_alerts.items():
        ml, fr, _ = lead_time_and_fp(steps, incident_steps, fp_window=fp_window)
        baseline_lead[name] = ml
        baseline_fp[name] = fr

    best_baseline_lead = max(baseline_lead.values()) if baseline_lead else 0.0
    best_baseline_fp = min(baseline_fp.values()) if baseline_fp else 1.0  # lower FP is better
    pass_ = median_lead_phase >= best_baseline_lead - 1e-9 or fp_rate_phase <= best_baseline_fp + 1e-9
    return (
        {
            "trajectory": trajectory,
            "phase_alert_steps": phase_alert_steps,
            "median_lead_time_phase": median_lead_phase,
            "fp_rate_phase": fp_rate_phase,
            "n_fp_phase": n_fp_phase,
            "baseline_alerts": baseline_alerts,
            "baseline_median_lead": baseline_lead,
            "baseline_fp_rate": baseline_fp,
            "incident_steps": incident_steps,
        },
        pass_,
    )
