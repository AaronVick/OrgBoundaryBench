#!/usr/bin/env python3
"""
Verify a remote-compute result by running the same payload locally.

Loads payload and result from a run under outputs/remote_compute_claude/<run_id>/,
runs bootstrap null dominance and permutation external p-values locally with
the same seed (and same n_bootstrap/n_perm as in the payload), and compares
numerically. Writes verification_report.json to the same run directory.

Tolerance: default 1e-2 for mean_D, ci bounds, p-values (to allow for minor
floating-point or resampling order differences when emulating RNG).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np


def _partition_map(partition: list, n: int) -> np.ndarray:
    block = np.full(n, -1, dtype=np.int64)
    for b, nodes in enumerate(partition):
        for i in nodes:
            block[int(i)] = b
    return block


def _bootstrap_null_dominance_local(
    q_star: list,
    rival_partitions: Dict[str, list],
    labels: np.ndarray,
    n: int,
    n_bootstrap: int,
    seed: int,
) -> Dict[str, Any]:
    from sklearn.metrics import normalized_mutual_info_score
    labels_full = np.asarray(labels).ravel()[:n]
    labeled_idx = np.where(labels_full >= 0)[0]
    if labeled_idx.size == 0:
        return {"mean_D": 0.0, "std_D": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "n_bootstrap": n_bootstrap, "best_rival_name_full": None, "best_rival_nmi_full": 0.0, "star_nmi_full": 0.0, "pass": False}
    true_lab = labels_full[labeled_idx]
    pred_star_full = _partition_map(q_star, n)[labeled_idx]
    pred_rivals = {name: _partition_map(part, n)[labeled_idx] for name, part in rival_partitions.items()}

    def _safe_nmi(y_true, y_pred):
        if np.unique(y_true).size < 2 and np.unique(y_pred).size < 2:
            return 1.0 if np.array_equal(y_true, y_pred) else 0.0
        return float(normalized_mutual_info_score(y_true, y_pred, average_method="arithmetic"))

    star_full = _safe_nmi(true_lab, pred_star_full)
    rival_full = {name: _safe_nmi(true_lab, pred) for name, pred in pred_rivals.items()}
    best_rival_name_full = max(rival_full, key=lambda k: rival_full[k]) if rival_full else None
    best_rival_full = float(rival_full[best_rival_name_full]) if best_rival_name_full else 0.0
    rng = np.random.default_rng(seed)
    m = labeled_idx.size
    D_samples = []
    for _ in range(n_bootstrap):
        draw = rng.integers(0, m, size=m)
        y = true_lab[draw]
        star = _safe_nmi(y, pred_star_full[draw])
        rivals = [_safe_nmi(y, pred_rivals[name][draw]) for name in pred_rivals]
        max_rival = max(rivals) if rivals else 0.0
        D_samples.append(star - max_rival)
    D_arr = np.asarray(D_samples, dtype=np.float64)
    mean_D = float(np.mean(D_arr)) if D_arr.size else 0.0
    std_D = float(np.std(D_arr)) if D_arr.size else 0.0
    lb = float(np.percentile(D_arr, 2.5)) if D_arr.size else 0.0
    ub = float(np.percentile(D_arr, 97.5)) if D_arr.size else 0.0
    pass_ = bool(lb > 0.0 and (star_full - best_rival_full) > 0.0)
    return {
        "mean_D": mean_D, "std_D": std_D, "ci_lower": lb, "ci_upper": ub,
        "n_bootstrap": n_bootstrap, "best_rival_name_full": best_rival_name_full,
        "best_rival_nmi_full": best_rival_full, "star_nmi_full": star_full, "pass": pass_,
    }


def _permutation_external_pvals_local(
    q_star: list,
    labels: np.ndarray,
    n: int,
    n_perm: int,
    seed: int,
) -> Dict[str, float]:
    from boundary_org.labeled_harness import external_agreement
    rng = np.random.default_rng(seed)
    labels_flat = np.asarray(labels).ravel()[:n]
    star = external_agreement(q_star, labels_flat, n)
    nmi_star = float(star.get("nmi", 0.0))
    ari_star = float(star.get("ari", 0.0))
    f1_star = float(star.get("macro_f1", 0.0))
    null_nmi, null_ari, null_f1 = [], [], []
    for _ in range(n_perm):
        perm = rng.permutation(len(labels_flat))
        lp = labels_flat[perm]
        ag = external_agreement(q_star, lp, n)
        null_nmi.append(float(ag.get("nmi", 0.0)))
        null_ari.append(float(ag.get("ari", 0.0)))
        null_f1.append(float(ag.get("macro_f1", 0.0)))
    return {
        "nmi_star": nmi_star, "ari_star": ari_star, "f1_star": f1_star,
        "nmi_p_value": float(np.mean(np.array(null_nmi) >= nmi_star)) if null_nmi else 1.0,
        "ari_p_value": float(np.mean(np.array(null_ari) >= ari_star)) if null_ari else 1.0,
        "f1_p_value": float(np.mean(np.array(null_f1) >= f1_star)) if null_f1 else 1.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify remote-compute result with local run.")
    ap.add_argument("--run-dir", type=Path, help="e.g. outputs/remote_compute_claude/2026-03-08T120000Z")
    ap.add_argument("--tolerance", type=float, default=1e-2, help="Absolute tolerance for numeric comparison.")
    args = ap.parse_args()
    run_dir = args.run_dir.resolve()
    if not run_dir.is_dir():
        print(f"Run dir not found: {run_dir}", file=sys.stderr)
        return 1
    payload_path = run_dir / "payload.json"
    result_path = run_dir / "result.json"
    if not payload_path.exists() or not result_path.exists():
        print("Missing payload.json or result.json", file=sys.stderr)
        return 1
    with payload_path.open() as f:
        payload = json.load(f)
    with result_path.open() as f:
        result = json.load(f)
    n = payload["n"]
    labels = np.array(payload["labels"], dtype=np.int64)
    q_star = payload["q_star"]
    rival_partitions = payload.get("rival_partitions", {})
    n_bootstrap = payload.get("n_bootstrap", 50)
    n_perm = payload.get("n_perm", 50)
    seed = payload.get("seed", 42)
    local_bootstrap = None
    local_perm = None
    if payload.get("task") in ("bootstrap_null_dominance", "combined") and rival_partitions:
        local_bootstrap = _bootstrap_null_dominance_local(
            q_star, rival_partitions, labels, n, n_bootstrap, seed
        )
    if payload.get("task") in ("permutation_external_pvals", "combined"):
        local_perm = _permutation_external_pvals_local(q_star, labels, n, n_perm, seed)
    tol = args.tolerance
    report = {"run_id": result.get("run_id"), "payload_hash": result.get("payload_hash"), "tolerance": tol}
    bootstrap_ok = True
    if local_bootstrap and result.get("bootstrap"):
        rb = result["bootstrap"]
        lb = local_bootstrap
        for key in ("mean_D", "std_D", "ci_lower", "ci_upper", "star_nmi_full", "best_rival_nmi_full"):
            if key in rb and key in lb:
                diff = abs(rb[key] - lb[key])
                if diff > tol:
                    bootstrap_ok = False
                    report.setdefault("bootstrap_diffs", {})[key] = {"remote": rb[key], "local": lb[key], "diff": diff}
        if rb.get("pass") != lb.get("pass"):
            bootstrap_ok = False
            report.setdefault("bootstrap_diffs", {})["pass"] = {"remote": rb.get("pass"), "local": lb.get("pass")}
        report["bootstrap_local"] = local_bootstrap
        report["bootstrap_remote"] = rb
    report["bootstrap_verified"] = bootstrap_ok
    perm_ok = True
    if local_perm and result.get("permutation"):
        rp = result["permutation"]
        lp = local_perm
        for key in ("nmi_star", "ari_star", "f1_star", "nmi_p_value", "ari_p_value", "f1_p_value"):
            if key in rp and key in lp:
                diff = abs(rp[key] - lp[key])
                if diff > tol:
                    perm_ok = False
                    report.setdefault("permutation_diffs", {})[key] = {"remote": rp[key], "local": lp[key], "diff": diff}
        report["permutation_local"] = local_perm
        report["permutation_remote"] = rp
    report["permutation_verified"] = perm_ok
    report["overall_verified"] = bootstrap_ok and perm_ok
    out_path = run_dir / "verification_report.json"
    with out_path.open("w") as f:
        json.dump(report, f, indent=2)
    print(f"Verification: overall_verified={report['overall_verified']}. Wrote {out_path}")
    return 0 if report["overall_verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
