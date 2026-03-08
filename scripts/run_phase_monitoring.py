#!/usr/bin/env python3
"""
Phase Monitoring (PRD-22). Empirical Test Family F.

Generates a sequence of kernels (synthetic trajectory) or accepts list; computes q* and E_cl
per step, NMI between consecutive q*; reports rising E_cl and abrupt boundary change.
Writes phase_monitoring_report.txt to outputs/runs/<run_id>/ (or --out-dir).
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

from boundary_org.phase_monitoring import run_phase_monitoring
from boundary_org.synthetic import make_lumpable_block_diagonal


def make_trajectory(n: int = 10, n_steps: int = 5, seed: int = 42) -> list[tuple[np.ndarray, np.ndarray]]:
    """Sequence of (K, mu): start lumpable, add increasing perturbation over steps (PRD-22 intervention)."""
    rng = np.random.default_rng(seed)
    base = make_lumpable_block_diagonal(n, rng=rng)
    out = []
    for step in range(n_steps):
        eps = 0.02 * (step + 1)  # increasing perturbation
        K = base.K + rng.uniform(-eps, eps, (n, n))
        K = np.maximum(K, 1e-10)
        row_sums = K.sum(axis=1, keepdims=True)
        K = K / row_sums
        mu = np.ones(n) / n  # simplified; in full would recompute stationary
        out.append((K, mu))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-22: Phase monitoring — E_cl trajectory, NMI, rising/abrupt flags.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory (default: outputs/runs/<ISO timestamp>)")
    ap.add_argument("--n", type=int, default=10, help="State space size")
    ap.add_argument("--n-steps", type=int, default=5, help="Number of time/parameter steps")
    ap.add_argument("--abrupt-threshold", type=float, default=0.8, help="NMI below this flags abrupt_switch")
    ap.add_argument("--rising-window", type=int, default=2, help="Window for rising E_cl detection")
    args = ap.parse_args()

    kernels = make_trajectory(n=args.n, n_steps=args.n_steps)

    out_dir = args.out_dir
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out_dir = ROOT / "outputs" / "runs" / ts
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    trajectory, flags = run_phase_monitoring(
        kernels,
        abrupt_nmi_threshold=args.abrupt_threshold,
        rising_window=args.rising_window,
    )

    lines = [
        "# Phase Monitoring (PRD-22) — Empirical Test Family F",
        f"# n={args.n}, n_steps={args.n_steps}, abrupt_threshold={args.abrupt_threshold}, rising_window={args.rising_window}",
        "",
        "## Trajectory (step, n_blocks, E_cl, nmi_prev)",
        "",
    ]
    for row in trajectory:
        nmi_str = f"{row['nmi_prev']:.4f}" if row.get("nmi_prev") is not None else "—"
        lines.append(f"  step={row['step']} n_blocks={row['n_blocks']} E_cl={row['E_cl']:.6f} nmi_prev={nmi_str}")
    lines.append("")
    lines.append("## Flags (rising_closure, abrupt_switch)")
    for f in flags:
        lines.append(f"  {f}")
    if not flags:
        lines.append("  (none)")
    report_path = out_dir / "phase_monitoring_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
