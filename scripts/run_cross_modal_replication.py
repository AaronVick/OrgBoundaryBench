#!/usr/bin/env python3
"""PRD VIII (thoughts3): Cross-Modal Sedation Replication. sign(ΔT_A) = sign(ΔT_B)."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from relational_closure.cross_modal_replication import run_cross_modal_replication


def make_samples(n: int, n_per_class: int, seed: int, scale_b: float = 1.0):
    """Synthetic (W, label). scale_b != 1 makes modality B differ in mean PE by condition."""
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n_per_class):
        W = rng.uniform(0.1, 1.0, (n, n))
        samples.append((W, 0))
    for _ in range(n_per_class):
        W = rng.uniform(0.1, 1.0, (n, n)) * scale_b
        samples.append((W, 1))
    return samples


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD VIII: Cross-modal replication — direction consistency.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--n-per-class", type=int, default=3)
    ap.add_argument("--no-gudhi", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    # Modality A: condition 1 slightly higher PE on average (scale 1.2)
    samples_a = make_samples(args.n, args.n_per_class, rng.integers(0, 10000), scale_b=1.2)
    # Modality B: same direction (condition 1 higher)
    samples_b = make_samples(args.n, args.n_per_class, rng.integers(0, 10000), scale_b=1.15)
    result, pass_ = run_cross_modal_replication(samples_a, samples_b, use_gudhi=not args.no_gudhi)

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PRD VIII: Cross-Modal Sedation Replication",
        f"delta_T_modality_a: {result['delta_T_modality_a']:.6f}",
        f"delta_T_modality_b: {result['delta_T_modality_b']:.6f}",
        f"direction_consistent: {result['direction_consistent']}",
        f"Pass: {pass_}",
        "Falsification: sign(ΔT_A) != sign(ΔT_B) => modality-specific artifact (thoughts3 VIII).",
    ]
    report_path = out_dir / "cross_modal_replication_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
