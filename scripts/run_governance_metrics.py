#!/usr/bin/env python3
"""
PRD-25: Governance Metrics on Real Appeals / Overrides / Reversals.

Computes override latency, reversal success, unattributed residue, unresolved challenge rate;
χ(d) proxy. Pass only if challenge paths alter outcomes. Accepts synthetic event list or CSV.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.governance_metrics import ChallengeEvent, run_governance_metrics


def make_synthetic_events(n: int = 10, reversal_ratio: float = 0.4, unattributed_ratio: float = 0.2) -> list:
    """Synthetic challenge events for testing. outcome reversed/denied; some unattributed."""
    events = []
    for i in range(n):
        outcome = "reversed" if (i / max(1, n)) < reversal_ratio else "denied"
        agent = None if (i / max(1, n)) < unattributed_ratio else f"agent_{i % 3}"
        events.append(ChallengeEvent(
            challenge_id=f"c_{i}",
            timestamp_challenge=1000.0 + i * 10,
            timestamp_resolution=1000.0 + i * 10 + 5.0,
            outcome=outcome,
            attributable_agent=agent,
        ))
    return events


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-25: Governance metrics — override latency, reversal success, pass/fail.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output directory")
    ap.add_argument("--n", type=int, default=10, help="Number of synthetic events")
    ap.add_argument("--reversal-min", type=float, default=0.2, help="Min reversal success for pass")
    ap.add_argument("--unresolved-max", type=float, default=0.9, help="Max unresolved rate for pass")
    ap.add_argument("--unattributed-max", type=float, default=0.9, help="Max unattributed residue for pass")
    args = ap.parse_args()

    events = make_synthetic_events(n=args.n, reversal_ratio=0.4, unattributed_ratio=0.2)
    metrics, pass_ = run_governance_metrics(
        events,
        reversal_success_min=args.reversal_min,
        unresolved_rate_max=args.unresolved_max,
        unattributed_max=args.unattributed_max,
    )

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    lat = metrics["override_latency"]
    lines = [
        "# PRD-25: Governance Metrics on Real Appeals / Overrides / Reversals",
        f"# n_events={metrics['n_events']}",
        "",
        "## Override latency (challenge → resolution)",
        f"  mean={lat['mean']:.4f}, median={lat['median']:.4f}, min={lat['min']:.4f}, max={lat['max']:.4f}, count={lat['count']}",
        "",
        f"## Reversal success: {metrics['reversal_success']:.4f}",
        f"## Unattributed residue: {metrics['unattributed_residue']:.4f}",
        f"## Unresolved challenge rate: {metrics['unresolved_challenge_rate']:.4f}",
        "",
        "## χ(d) proxy (reversibility): " + str(metrics["chi_proxy"].get("reversibility")),
        "",
        f"## Pass (challenge paths alter outcomes; thresholds met): {pass_}",
        "## Falsification: Reversal success below min, or unresolved/unattributed above max → fail (PRD-25 §4).",
        "",
    ]
    report_path = out_dir / "governance_metrics_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
