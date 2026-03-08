#!/usr/bin/env python3
"""PRD-16: Adversarial and Domain-Grounded Falsification — adversarial checklist Q1–Q4."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.adversarial_audit import run_adversarial_audit


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-16: Adversarial checklist (Q1–Q4) for run reports.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    result, pass_ = run_adversarial_audit(K, mu, n_random=2, rng=rng)

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    chk = result["checklist"]
    lines = [
        "# PRD-16: Adversarial and Domain-Grounded Falsification",
        "",
        "## Adversarial checklist",
        f"Q1 (reject trivial partition): {chk['Q1']}",
        f"Q2 (survive intervention/construction): {chk['Q2']}",
        f"Q3 (beat baselines on real task): {chk['Q3']}",
        f"Q4 (governance properties): {chk['Q4']}",
        "",
        f"n_blocks(q*): {result['n_blocks_q_star']}",
        f"Pass: {pass_}",
        "",
        "Falsification: Q1 Fail (trivial q*) or any assessed Q2–Q4 Fail (PRD-16 §3).",
    ]
    report_path = out_dir / "adversarial_audit_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
