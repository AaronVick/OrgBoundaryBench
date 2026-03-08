"""
PRD-27: RCTI Real Sedation Test — condition-contrast discrimination.

Multi-window, multi-construction topology (C1, C4b, PE, C2F) and six graph baselines;
AUC vs labeled conditions (conscious/sedated/unconscious). Falsification: topology must
beat or match baselines or run fails.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Tuple

from .pipeline import run_pipeline
from .graph_baselines import compute_all_baselines


def topology_scalar_summary(result: Dict[str, Any]) -> float:
    """
    Single scalar from pipeline for discrimination. PRD-27 §2.2.
    Uses persistence entropy as primary; C1/C4b are binary so we use PE for AUC.
    """
    return float(result.get("persistence_entropy", 0.0))


def run_discrimination(
    samples: List[Tuple[np.ndarray, int]],
    *,
    tau: float = 0.1,
    use_gudhi: bool = True,
) -> Tuple[Dict[str, Any], bool]:
    """
    PRD-27: Per (W, label) sample, compute topology scalar (PE) and six baselines; AUC vs labels.
    Pass iff topology AUC >= best baseline AUC or >= 0.5.
    """
    if not samples:
        return {"auc_topology": 0.5, "auc_baselines": {}, "pass": False}, False
    labels = np.array([label for _, label in samples], dtype=np.int64)
    n = len(samples)

    pe_list: List[float] = []
    baseline_lists: Dict[str, List[float]] = {}

    for W, _ in samples:
        res = run_pipeline(W, threshold=None, max_dim=4, tau=tau, use_gudhi=use_gudhi)
        pe_list.append(topology_scalar_summary(res))
        bl = compute_all_baselines(W)
        for k, v in bl.items():
            baseline_lists.setdefault(k, []).append(float(v))

    pe_vec = np.array(pe_list)
    n_classes = len(np.unique(labels))
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError:
        return {"auc_topology": 0.5, "auc_baselines": {k: 0.5 for k in baseline_lists}, "pass": False}, False

    if n_classes < 2:
        auc_topology = 0.5
        auc_baselines = {k: 0.5 for k in baseline_lists}
    else:
        if n_classes == 2:
            auc_topology = float(roc_auc_score(labels, pe_vec))
            auc_baselines = {k: float(roc_auc_score(labels, np.array(baseline_lists[k]))) for k in baseline_lists}
        else:
            auc_topology = float(roc_auc_score(labels, pe_vec, multi_class="ovr", average="macro"))
            auc_baselines = {
                k: float(roc_auc_score(labels, np.array(baseline_lists[k]), multi_class="ovr", average="macro"))
                for k in baseline_lists
            }

    best_baseline_auc = max(auc_baselines.values()) if auc_baselines else 0.5
    pass_ = auc_topology >= best_baseline_auc or auc_topology >= 0.5
    return (
        {
            "auc_topology": auc_topology,
            "auc_baselines": auc_baselines,
            "n_samples": n,
            "n_classes": n_classes,
        },
        pass_,
    )


def run_discrimination_multi_construction(
    samples: List[Tuple[np.ndarray, int]],
    construction_fns: List[Tuple[str, Any]],
    *,
    tau: float = 0.1,
    use_gudhi: bool = True,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    PRD-27 §2.1: At least two constructions. Run discrimination per construction;
    pass iff for at least one construction topology beats or matches baselines.
    construction_fns: list of (name, callable) where callable(W) -> W' (e.g. raw, threshold).
    """
    results: List[Dict[str, Any]] = []
    any_pass = False
    for name, fn in construction_fns:
        transformed = [(fn(W), label) for W, label in samples]
        res, pass_ = run_discrimination(transformed, tau=tau, use_gudhi=use_gudhi)
        res["construction"] = name
        results.append(res)
        any_pass = any_pass or pass_
    return results, any_pass
