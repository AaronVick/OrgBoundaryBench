#!/usr/bin/env python3
"""
PRD-31: Full null/rival/leverage audit on email-Eu-core.

Runs null/rival audit (with rewire nulls and bootstrap CI) and leverage stability
on email-Eu-core kernel (or synthetic when data missing). Writes combined report
and run_report.md. Resolves density-confounding threat when rewire-null gate
and leverage gate pass.

Scientific method: hypothesis, method, data provenance, rewire-null gate,
bootstrap CI, leverage gate, falsification. Traceability: PRD-31, thoughts3-II/III.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.null_rival_audit import run_null_rival_audit_bootstrap
from boundary_org.leverage_stability import run_leverage_stability


def load_kernel(npz_path: Path, max_nodes: int) -> tuple:
    """Load K, mu, labels from kernel.npz; optionally cap to max_nodes by degree."""
    data = np.load(npz_path, allow_pickle=False)
    K = np.asarray(data["K"], dtype=np.float64)
    mu = np.asarray(data["mu"], dtype=np.float64)
    mu = np.where(mu > 0, mu, 0.0)
    mu = mu / np.sum(mu) if np.sum(mu) > 0 else np.ones(K.shape[0]) / K.shape[0]
    labels = np.asarray(data["labels"], dtype=np.int64) if "labels" in data else np.full(K.shape[0], -1)
    n0 = K.shape[0]
    if max_nodes > 0 and max_nodes < n0:
        degree = K.sum(axis=1)
        keep = np.argsort(-degree)[:max_nodes]
        keep = np.sort(keep)
        K = K[np.ix_(keep, keep)]
        row_sum = K.sum(axis=1, keepdims=True)
        row_sum = np.where(row_sum > 0, row_sum, 1.0)
        K = K / row_sum
        mu = mu[keep]
        mu = mu / np.sum(mu)
        labels = labels[keep]
    return K, mu, labels, {"n": K.shape[0], "n_original": n0, "path": str(npz_path)}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PRD-31: Full null/rival/leverage audit on email-Eu-core (rewire-null gate + bootstrap CI)."
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--dataset-npz", type=Path, default=ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz")
    ap.add_argument("--max-nodes", type=int, default=0, help="Cap nodes by degree; 0 = use all.")
    ap.add_argument("--bootstrap", type=int, default=50, help="Bootstrap runs for D CI (rewire nulls included).")
    ap.add_argument("--epsilon", type=float, nargs="+", default=[0.05, 0.1], help="Leverage drop fractions.")
    ap.add_argument("--n-trials", type=int, default=3)
    ap.add_argument("--stability-threshold", type=float, default=1.0, help="Leverage pass if S_max < threshold.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    npz_path = args.dataset_npz.resolve()
    if npz_path.exists():
        K, mu, labels, info = load_kernel(npz_path, args.max_nodes)
        data_provenance = f"email-Eu-core (or equivalent): {info['path']}, n={info['n']}, n_original={info.get('n_original', info['n'])}. Labels: present." if np.any(labels >= 0) else f"Kernel: {info['path']}, n={info['n']}. Labels: none."
    else:
        n = args.max_nodes if args.max_nodes > 0 else 24
        K = rng.uniform(0.1, 1.0, (n, n))
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(n) / n
        labels = rng.integers(0, 4, size=n)
        data_provenance = f"Synthetic: n={n}, seed={args.seed}. Dataset not found at {npz_path}; run download_and_normalize for public data."

    n = K.shape[0]
    if np.all(labels < 0):
        labels = None

    print(f"Running full audit: n={n}, bootstrap={args.bootstrap}, n_trials={args.n_trials}...", flush=True)
    # --- Null/Rival (includes rewire nulls in bootstrap) ---
    nr_result, rewire_null_pass = run_null_rival_audit_bootstrap(
        K, mu, labels,
        n_bootstrap=args.bootstrap,
        rng=rng,
        ci_lower_bound_required=0.0,
    )

    # --- Leverage stability ---
    lev_result, leverage_pass = run_leverage_stability(
        K, mu,
        epsilon_list=tuple(args.epsilon),
        n_trials_per_epsilon=args.n_trials,
        stability_threshold=args.stability_threshold,
        rng=rng,
    )

    overall_pass = rewire_null_pass and leverage_pass

    # --- Text report ---
    report_lines = [
        "# PRD-31: Full null/rival/leverage audit",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Rewire-null gate (bootstrap CI for D)",
        f"  mean_D: {nr_result['mean_D']:.6f}",
        f"  CI_lower: {nr_result['ci_lower']:.6f}, CI_upper: {nr_result['ci_upper']:.6f}",
        f"  n_bootstrap: {nr_result['n_bootstrap']} (includes row-sum-preserving rewire nulls)",
        f"  Pass (CI_lower > 0): {rewire_null_pass}",
        "",
        "## Leverage gate",
        f"  S_max: {lev_result['S_max']:.6f}",
        f"  threshold: {args.stability_threshold}",
        f"  Pass (S_max < threshold): {leverage_pass}",
        "",
        f"Overall pass (rewire-null and leverage): {overall_pass}",
    ]
    run_report_md = [
        "# Run report: PRD-31 full null/rival/leverage audit",
        "",
        f"**Run:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}  ",
        "**Framework:** BPO (thoughts3-II null/rival, thoughts3-III leverage).",
        "",
        "---",
        "",
        "## 1. Hypothesis",
        "",
        "BPO partition q* (greedy coarse-graining) beats baselines and nulls including **degree-preserving rewired** graphs (D > 0 with bootstrap CI). Results are not driven by leverage points (S_max < threshold).",
        "",
        "## 2. Method",
        "",
        "Null/rival: Perf = NMI to labels when provided else -J(q). Baselines: one-block, singleton, Louvain. Nulls: random partition (matched k), label-permuted NMI, **row-sum-preserving rewire** (n_rewire in each bootstrap draw). Bootstrap CI for D; rewire-null gate: CI_lower > 0. Leverage: node/edge drop; S_max; pass if S_max < threshold.",
        "",
        "## 3. Data provenance",
        "",
        data_provenance,
        "",
        "## 4. Results",
        "",
        "| Gate | Result |",
        "|------|--------|",
        f"| Rewire-null (bootstrap CI) | mean_D={nr_result['mean_D']:.4f}, CI=[{nr_result['ci_lower']:.4f}, {nr_result['ci_upper']:.4f}], Pass={rewire_null_pass} |",
        f"| Leverage | S_max={lev_result['S_max']:.4f}, threshold={args.stability_threshold}, Pass={leverage_pass} |",
        "",
        "## 5. Falsification",
        "",
        "**PRD-31:** If rewire-null gate fails (CI includes 0 or D ≤ 0), density-confounding threat remains; no organizational relevance claim. If leverage gate fails, results sensitive to few nodes/edges.",
        "",
        "---",
        "",
        "*Traceability: PRD-31, thoughts3-II, thoughts3-III, outputs/METHODOLOGY.md.*",
    ]

    out_dir = args.out_dir or (ROOT / "outputs" / "email_eu_core_full_audit" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "full_audit_report.txt").write_text("\n".join(report_lines))
    (out_dir / "run_report.md").write_text("\n".join(run_report_md))
    print(f"Wrote {out_dir / 'full_audit_report.txt'}, {out_dir / 'run_report.md'}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
