#!/usr/bin/env python3
"""
Predictive-Control Misalignment Engine (PRD-20). Empirical Test Family D.

Computes q_pred (greedy on K), q_ctrl proxy (greedy on perturbed K or Louvain), m_n;
writes misalignment_report.txt. Outcomes stubbed when no intervention data.
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

from boundary_org.misalignment_engine import run_misalignment_engine


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-20: Misalignment engine — q_pred vs q_ctrl, m_n, stub outcomes.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--use-louvain", action="store_true", help="Use Louvain as control proxy")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report, success = run_misalignment_engine(K, mu, use_louvain_as_ctrl=args.use_louvain, rng=rng)

    lines = [
        "# Predictive-Control Misalignment Engine (PRD-20) — Empirical Test Family D",
        f"# n={args.n}, control_proxy={report['control_proxy']}",
        "",
        "## Report",
        f"m_n: {report['m_n']:.6f}",
        f"n_blocks_pred: {report['n_blocks_pred']}",
        f"n_blocks_ctrl: {report['n_blocks_ctrl']}",
        f"override_success_stub: {report['override_success_stub']:.4f}",
        f"recovery_time_stub: {report['recovery_time_stub']:.4f}",
        f"confusion_stub: {report['confusion_stub']:.4f}",
        f"pass: {success}",
    ]

    report_path = out_dir / "misalignment_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
