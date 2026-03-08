#!/usr/bin/env python3
"""
PRD-24: Public Incident-Coupled Phase Monitoring.

Rolling (m_cl, boundary switch), lead time to incident, false positive burden;
comparison to density/entropy/spectral-gap drift. Pass: phase adds value or is not worse.
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

from boundary_org.incident_phase_monitoring import run_incident_phase_monitoring


def make_synthetic_kernels_and_incident(n_steps: int = 6, incident_at: int = 4, n_nodes: int = 6, seed: int = 42) -> tuple:
    """Synthetic kernels; E_cl rises before incident_at so phase can alert early."""
    rng = np.random.default_rng(seed)
    kernels = []
    for t in range(n_steps):
        K = rng.uniform(0.1, 1.0, (n_nodes, n_nodes))
        if t >= 2:
            K = K * 0.7  # perturb so closure/partition may change
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(n_nodes) / n_nodes
        kernels.append((K, mu))
    return kernels, [incident_at]


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-24: Incident-coupled phase monitoring — lead time, FP, baselines.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory")
    ap.add_argument("--n-steps", type=int, default=6, help="Number of time steps")
    ap.add_argument("--incident-at", type=int, default=4, help="Step index where incident occurs")
    ap.add_argument("--n-nodes", type=int, default=6, help="Nodes per kernel")
    ap.add_argument("--abrupt-threshold", type=float, default=0.8, help="NMI threshold for abrupt_switch")
    ap.add_argument("--fp-window", type=int, default=2, help="Window for false positive (steps)")
    args = ap.parse_args()

    kernels, incident_steps = make_synthetic_kernels_and_incident(
        n_steps=args.n_steps, incident_at=args.incident_at, n_nodes=args.n_nodes
    )
    result, pass_ = run_incident_phase_monitoring(
        kernels,
        incident_steps,
        abrupt_nmi_threshold=args.abrupt_threshold,
        fp_window=args.fp_window,
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# PRD-24: Public Incident-Coupled Phase Monitoring",
        f"# n_steps={args.n_steps}, incident_steps={incident_steps}, n_nodes={args.n_nodes}",
        "",
        "## Phase monitoring",
        f"  Phase alert steps: {result['phase_alert_steps']}",
        f"  Median lead time (phase): {result['median_lead_time_phase']:.4f}",
        f"  False positive rate (phase): {result['fp_rate_phase']:.4f} (n_fp={result['n_fp_phase']})",
        "",
        "## Baseline drift alerts",
    ]
    for name in ["density_drift", "entropy_drift", "spectral_gap_drift"]:
        lines.append(f"  {name}: {result['baseline_alerts'].get(name, [])}")
    lines.append("")
    lines.append("## Baseline median lead time: " + str(result["baseline_median_lead"]))
    lines.append("## Baseline FP rate: " + str(result["baseline_fp_rate"]))
    lines.extend([
        "",
        f"## Pass (phase adds value or is not worse than baselines): {pass_}",
        "## Falsification: Phase does not precede incidents, or FP too high, or baselines outperform (PRD-24 §4).",
        "",
    ])
    report_path = out_dir / "incident_phase_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
