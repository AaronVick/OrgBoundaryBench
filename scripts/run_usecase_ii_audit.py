#!/usr/bin/env python3
"""
Usecase PRD II (useccases.md): Null-Model, Rival-Theory, and Outlier Audit.

Runs null/rival audit (D = Perf(q*) - max(baselines U nulls)) and leverage stability
(S = max |Perf(q) - Perf(q^{-A})|), then writes a single use-case report with:
Hypothesis, Methods, Public data used, Baseline, Outcomes, Falsification,
and "What would make this look good but be wrong".

Scientific method: hypothesis, method, data provenance, baseline, outcomes, falsification.
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

from boundary_org.null_rival_audit import run_null_rival_audit, run_null_rival_audit_bootstrap
from boundary_org.leverage_stability import run_leverage_stability


def load_kernel_optional_labels(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, dict]:
    """Load K, mu, optional labels from kernel.npz (email-Eu-core or enron format). Returns (K, mu, labels, info)."""
    npz_path = processed_dir / "kernel.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Missing {npz_path}. Run download_and_normalize.py for public data.")
    data = np.load(npz_path, allow_pickle=False)
    K = np.asarray(data["K"])
    mu = np.asarray(data["mu"])
    labels = np.asarray(data["labels"], dtype=np.int32) if "labels" in data else None
    info = {"n": int(K.shape[0]), "source": "processed", "path": str(processed_dir)}
    return K, mu, labels, info


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Usecase PRD II: Null-Model, Rival-Theory, and Outlier Audit — scientific-method report."
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--data", type=Path, default=None, help="Processed dir with kernel.npz (e.g. data/processed/email_eu_core)")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--with-labels", action="store_true", help="Synthetic: use random labels for external perf (NMI)")
    ap.add_argument("--bootstrap", type=int, default=50, help="Bootstrap runs for null/rival CI (default: 50)")
    ap.add_argument("--epsilon", type=float, nargs="+", default=[0.05, 0.1])
    ap.add_argument("--n-trials", type=int, default=2)
    ap.add_argument("--threshold", type=float, default=1.0, help="Leverage stability pass if S_max < threshold")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    data_provenance: str
    if args.data is not None:
        processed_dir = Path(args.data).resolve()
        K, mu, labels, info = load_kernel_optional_labels(processed_dir)
        data_provenance = f"Public/processed: {info.get('source', 'processed')} (n={info['n']}), path={info.get('path', processed_dir)}. SNAP email-Eu-core or Enron SNAP if built via download_and_normalize.py."
    else:
        K = rng.uniform(0.1, 1.0, (args.n, args.n))
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(args.n) / args.n
        labels = rng.integers(0, 3, size=args.n) if args.with_labels else None
        data_provenance = f"Synthetic: n={args.n}, seed={args.seed}. No public dataset; for publication use --data with data/processed/email_eu_core (SNAP email-Eu-core) or equivalent."

    n = K.shape[0]

    # --- Null/Rival audit ---
    if args.bootstrap > 0:
        nr_result, nr_pass = run_null_rival_audit_bootstrap(K, mu, labels, n_bootstrap=args.bootstrap, rng=rng)
        nr_lines = [
            "Null/Rival (bootstrap):",
            f"  mean_D: {nr_result['mean_D']:.6f}",
            f"  CI_lower: {nr_result['ci_lower']:.6f}, CI_upper: {nr_result['ci_upper']:.6f}",
            f"  Pass (D > 0 with CI): {nr_pass}",
        ]
    else:
        nr_result, nr_pass = run_null_rival_audit(K, mu, labels, rng=rng)
        nr_lines = [
            "Null/Rival:",
            f"  Perf(q*): {nr_result['perf_star']:.6f}",
            f"  max(baselines U nulls): {nr_result['max_baseline_or_null']:.6f}",
            f"  D: {nr_result['D']:.6f}",
            f"  Pass (D > 0): {nr_pass}",
        ]

    # --- Leverage (outlier) stability ---
    lev_result, lev_pass = run_leverage_stability(
        K, mu,
        epsilon_list=tuple(args.epsilon),
        n_trials_per_epsilon=args.n_trials,
        stability_threshold=args.threshold,
        rng=rng,
    )
    lev_lines = [
        "Outlier/Leverage stability:",
        f"  S_max: {lev_result['S_max']:.6f}",
        f"  threshold: {args.threshold}",
        f"  Pass (S_max < threshold): {lev_pass}",
    ]

    overall_pass = nr_pass and lev_pass

    # --- Build use-case report (scientific method) ---
    report_lines = [
        "# Usecase PRD II: Null-Model, Rival-Theory, and Outlier Audit",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Hypothesis",
        "The boundary/closure framework (q* from greedy coarse-graining) outperforms rival baselines and null",
        "worlds: D(q) = Perf(q*) - max(baselines U nulls) > 0. Results are not driven by leverage points:",
        "S(q) = max |Perf(q) - Perf(q^{-A})| remains below a pre-registered threshold under node/edge removal.",
        "",
        "## 2. Methods",
        "Null/Rival: Perf = -J(q) (internal) or NMI to ground-truth labels when provided. Baselines: one-block,",
        "singleton, Louvain. Nulls: random partitions (matched block count), label-permuted agreement when labels exist,",
        "graph-structure null (row-sum-preserving rewire). Leverage: random node/edge drop, plus top-degree node drop;",
        "recompute q* and Perf; S = max absolute change.",
        "Falsification (useccases.md PRD II): any main result that collapses under mild rewiring/shuffling or is",
        "driven by a tiny set of actors/windows is rejected.",
        "",
        "## 3. Public data used",
        data_provenance,
        "",
        "## 4. Baseline",
        "Rivals: one-block partition, singleton partition, Louvain. Nulls: random partition (matched k),",
        "label-permuted NMI (when labels available), row-sum-preserving rewire. Outlier: node/edge drop and top-degree drop.",
        "",
        "## 5. Outcomes",
        "",
        *nr_lines,
        "",
        *lev_lines,
        "",
        f"Overall pass (null/rival and leverage): {overall_pass}",
        "",
        "## 6. Falsification",
        "If D ≤ 0: framework does not beat baselines/null; no claim. If S_max ≥ threshold: results sensitive to",
        "removal of a small set of nodes/edges (leverage points); claim not robust. Per useccases.md PRD II:",
        "positive dominance over rivals and nulls and low leverage sensitivity required.",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Leakage: labels or structure used in training that appear only in test (ensure strict split).",
        "• Confounding by graph density: wins only on dense subgraphs; nulls should match density where possible.",
        "• Label contamination: department/team labels correlated with degree; use degree-preserving rewires.",
        "• Responsibility-label artifacts: external Perf (NMI) rewards partition-label alignment that may not",
        "  reflect governance; internal Perf (-J) is structure-only.",
        "• Stronger models masquerading as better math: compare same model with vs without boundary module.",
        "• Gains from extra orchestration rather than the math: use sham-complexity control (useccases Arm C).",
        "",
    ]

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "usecase_II_report.txt"
    report_path.write_text("\n".join(report_lines))
    print(f"Wrote {report_path}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
