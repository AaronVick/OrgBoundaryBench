#!/usr/bin/env python3
"""
Usecase PRD III (useccases.md): Dynamic Drift, Failure Lead, and Recovery Benchmark.

Runs incident-coupled phase monitoring (m_cl, boundary switch, lead time vs baselines).
Report: Hypothesis, Methods, Public data used, Baseline, Outcomes, Falsification,
and "What would make this look good but be wrong". Scientific method, PhD rigor.
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


def make_synthetic_kernels_and_incident(
    n_steps: int = 6, incident_at: int = 4, n_nodes: int = 6, seed: int = 42
) -> tuple[list[tuple[np.ndarray, np.ndarray]], list[int]]:
    """Synthetic kernels; E_cl/partition may change before incident_at so phase can alert early."""
    rng = np.random.default_rng(seed)
    kernels = []
    for t in range(n_steps):
        K = rng.uniform(0.1, 1.0, (n_nodes, n_nodes))
        if t >= 2:
            K = K * 0.7
        K = K / K.sum(axis=1, keepdims=True)
        mu = np.ones(n_nodes) / n_nodes
        kernels.append((K, mu))
    return kernels, [incident_at]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Usecase PRD III: Dynamic drift, failure lead, and recovery benchmark — scientific-method report."
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n-steps", type=int, default=6)
    ap.add_argument("--incident-at", type=int, default=4)
    ap.add_argument("--n-nodes", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    kernels, incident_steps = make_synthetic_kernels_and_incident(
        n_steps=args.n_steps, incident_at=args.incident_at, n_nodes=args.n_nodes, seed=args.seed
    )
    result, pass_ = run_incident_phase_monitoring(kernels, incident_steps)

    data_provenance = (
        f"Synthetic: n_steps={args.n_steps}, n_nodes={args.n_nodes}, incident_at={args.incident_at}, seed={args.seed}. "
        "No public temporal data. For publication use email-Eu-core-temporal, wiki-talk-temporal, or GH Archive slices (useccases.md PRD III)."
    )

    lines = [
        "# Usecase PRD III: Dynamic Drift, Failure Lead, and Recovery Benchmark",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Hypothesis",
        "Math-governed phase monitoring (m_cl, boundary switch) detects coordination drift or likely failure earlier than",
        "event-volume, entropy, modularity, and spectral-gap drift baselines; lead time to incident should be non-inferior,",
        "with acceptable false positive burden (useccases.md PRD III).",
        "",
        "## 2. Methods",
        "Incident-coupled phase monitoring: trajectory of E_cl, q* per step; flags for abrupt_switch (NMI drop).",
        "Phase alert steps vs incident steps → median lead time, false positive rate. Baselines: density drift, entropy drift,",
        "spectral-gap drift (quantile-threshold alerts). Pass: phase adds value or is not worse than baselines on lead time or FP.",
        "",
        "## 3. Public data used",
        data_provenance,
        "",
        "## 4. Baseline",
        "Event-volume / density drift, entropy drift, modularity proxy, spectral-gap drift (per-window; alert when drift exceeds quantile).",
        "",
        "## 5. Outcomes",
        "",
        f"  Phase alert steps: {result['phase_alert_steps']}",
        f"  Median lead time (phase): {result['median_lead_time_phase']:.4f}",
        f"  False positive rate (phase): {result['fp_rate_phase']:.4f} (n_fp={result['n_fp_phase']})",
        f"  Baseline median lead: {result['baseline_median_lead']}",
        f"  Baseline FP rate: {result['baseline_fp_rate']}",
        f"  Incident steps: {result['incident_steps']}",
        "",
        f"Pass (phase not worse than baselines): {pass_}",
        "",
        "## 6. Falsification",
        "If phase does not precede incidents (no lead time), or FP burden too high, or simpler drift baselines outperform,",
        "the early-warning claim is falsified (useccases.md PRD III).",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Lead time from volume/entropy spikes only, not from boundary/closure structure.",
        "• Synthetic incident placement is arbitrary; real rupture/reversal/escalation labels required.",
        "• Window-size sensitivity; report robustness across window sizes.",
    ]

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "usecase_III_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
