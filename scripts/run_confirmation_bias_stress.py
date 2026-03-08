#!/usr/bin/env python3
"""PRD X (thoughts3): Human Confirmation-Bias Stress Test. Challenge rate, false reassurance, pass."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.confirmation_bias_stress import run_confirmation_bias_stress


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD X: Confirmation-bias stress — challenge rate, false reassurance.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--n-visible", type=int, default=3)
    ap.add_argument("--n-quiet", type=int, default=3)
    ap.add_argument("--n-control", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    result, pass_ = run_confirmation_bias_stress(
        K, mu,
        n_visible=args.n_visible,
        n_quiet=args.n_quiet,
        n_control=args.n_control,
        rng=rng,
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PRD X: Human Confirmation-Bias Stress Test",
        f"challenge_rate_visible: {result['challenge_rate_visible']:.4f}",
        f"challenge_rate_quiet: {result['challenge_rate_quiet']:.4f}",
        f"false_reassurance_rate: {result['false_reassurance_rate']:.4f}",
        f"successful_override_rate: {result['successful_override_rate']:.4f}",
        f"challenge_rises_when_should: {result['challenge_rises_when_should']}",
        f"rubber_stamping_falls: {result['rubber_stamping_falls']}",
        f"Pass: {pass_}",
        "Falsification: challenge does not rise when it should, or rubber-stamping dominates (thoughts3 X).",
    ]
    report_path = out_dir / "confirmation_bias_stress_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
