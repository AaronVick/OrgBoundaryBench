#!/usr/bin/env python3
"""
PRD-26: Misalignment Outcome Validation.

Per-unit m_n and outcomes; correlation in expected direction; out-of-sample and vs null/controls.
Pass: m_n predicts outcomes and is not dominated by controls. Falsification: m_n does not correlate
or controls outperform.
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

from boundary_org.misalignment_outcome_validation import run_misalignment_outcome_validation


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-26: Misalignment outcome validation — m_n vs outcomes, null, controls.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n-units", type=int, default=12, help="Number of units (synthetic)")
    ap.add_argument("--n-nodes", type=int, default=6, help="Nodes per kernel")
    ap.add_argument("--train-frac", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    units = []
    for _ in range(args.n_units):
        K = rng.uniform(0.1, 1.0, (args.n_nodes, args.n_nodes))
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(args.n_nodes) / args.n_nodes
        # Outcomes will be filled by run_misalignment_engine stubs when we call validation (it recomputes m_n and stubs)
        units.append((K, mu, {}))

    result, pass_ = run_misalignment_outcome_validation(
        units, rng=rng, train_frac=args.train_frac
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# PRD-26: Misalignment Outcome Validation",
        f"# n_units={result['n_units']}, n_nodes={args.n_nodes}",
        "",
        "## Correlations (m_n vs outcomes)",
        f"  corr(m_n, override_success): {result['corr_m_n_override_success']:.4f} (expected <= 0)",
        f"  corr(m_n, recovery_time):    {result['corr_m_n_recovery_time']:.4f} (expected >= 0)",
        f"  corr(m_n, confusion):         {result['corr_m_n_confusion']:.4f} (expected >= 0)",
        "",
        "## p-values",
        f"  p_override: {result['p_override']:.4f}, p_recovery: {result['p_recovery']:.4f}, p_confusion: {result['p_confusion']:.4f}",
        "",
        "## Checks",
        f"  direction_ok (expected sign): {result['direction_ok']}",
        f"  m_n_beats_null: {result['m_n_beats_null']}",
        f"  m_n_adds_value_vs_controls: {result['m_n_adds_value_vs_controls']}",
        f"  oos_consistent: {result['oos_consistent']}",
        "",
        f"## Pass: {pass_}",
        "## Falsification: m_n does not correlate in expected direction, or effect not significant, or controls dominate (PRD-26 §4).",
        "",
    ]
    report_path = out_dir / "misalignment_outcome_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
