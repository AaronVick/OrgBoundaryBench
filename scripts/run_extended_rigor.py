#!/usr/bin/env python3
"""PRD-11: Extended Testing Framework and Rigor — replication, sensitivity, negative-result checklist."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.extended_rigor import run_extended_rigor


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-11: Extended rigor — replication, sensitivity, checklist.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--n-seeds", type=int, default=3)
    ap.add_argument("--n-values", type=int, nargs="+", default=[8, 12, 16])
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    result, pass_ = run_extended_rigor(
        n=args.n,
        n_seeds=args.n_seeds,
        n_values=args.n_values,
        n_random=2,
        rng=rng,
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rep = result["replication"]
    sens = result["sensitivity"]
    chk = result["checklist"]
    lines = [
        "# PRD-11: Extended Testing Framework and Rigor",
        "",
        "## Replication",
        f"n_seeds: {rep['n_seeds']}",
        f"J_star mean (std): {rep['J_star_mean']:.6f} ({rep['J_star_std']:.6f})",
        f"success_rate: {rep['success_rate']:.4f}",
        f"stable: {result['stable']}",
        "",
        "## Sensitivity (vary n)",
    ]
    for row in sens:
        lines.append(f"  n={row['n']}: success={row['success']}, J_star={row['J_star']:.6f}, n_blocks={row['n_blocks']}")
    lines.extend([
        "",
        "## Negative-result checklist",
        f"all_tests_listed: {chk['all_tests_listed']}",
        f"null_stated: {chk['null_stated']}",
        f"falsification_cited: {chk['falsification_cited']}",
        "",
        f"Pass: {pass_}",
        "Falsification (PRD-11): replication unstable or checklist incomplete.",
    ])
    report_path = out_dir / "extended_rigor_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
