#!/usr/bin/env python3
"""
Usecase PRD IV (useccases.md): Contestability, Provenance, and Responsibility Benchmark.

Runs governance metrics (χ(d), override latency, reversal success, unattributed residue).
Report: Hypothesis, Methods, Public data used, Baseline, Outcomes, Falsification,
and "What would make this look good but be wrong". Scientific method, PhD rigor.
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


def make_synthetic_events(n: int = 10, reversal_ratio: float = 0.4, unattributed_ratio: float = 0.2):
    """Synthetic challenge events for usecase IV. outcome reversed/denied; some unattributed."""
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
    ap = argparse.ArgumentParser(
        description="Usecase PRD IV: Contestability, provenance, and responsibility benchmark — scientific-method report."
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--reversal-min", type=float, default=0.2)
    ap.add_argument("--unresolved-max", type=float, default=0.9)
    ap.add_argument("--unattributed-max", type=float, default=0.9)
    args = ap.parse_args()

    events = make_synthetic_events(n=args.n, reversal_ratio=0.4, unattributed_ratio=0.2)
    metrics, pass_ = run_governance_metrics(
        events,
        reversal_success_min=args.reversal_min,
        unresolved_rate_max=args.unresolved_max,
        unattributed_max=args.unattributed_max,
    )

    data_provenance = (
        f"Synthetic: n_events={args.n}, reversal_ratio=0.4, unattributed_ratio=0.2. "
        "No public data. For publication use wiki-talk-temporal (dispute/reversion chains), GH Archive (issue/PR review), "
        "or Apache mailing list/issue archives (useccases.md PRD IV)."
    )

    lat = metrics["override_latency"]
    lines = [
        "# Usecase PRD IV: Contestability, Provenance, and Responsibility Benchmark",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Hypothesis",
        "Math-governed assistant preserves meaningful challenge paths and attributable responsibility better than a plain LLM;",
        "χ(d) = p_reach·v·a·r (reachability, visibility, alternatives, reversibility); unattributed residue and moral-crumple defect",
        "should be low. Arm B produces higher challengeability/responsibility scores and recommends reversible next steps (useccases.md PRD IV).",
        "",
        "## 2. Methods",
        "Governance metrics on challenge events: override latency (challenge → resolution), reversal success rate,",
        "unattributed residue, unresolved challenge rate; χ(d) proxy (reversibility). Pass = reversal_success ≥ min,",
        "unresolved ≤ max, unattributed ≤ max so that challenge paths alter outcomes.",
        "",
        "## 3. Public data used",
        data_provenance,
        "",
        "## 4. Baseline",
        "Plain LLM (no provenance/reversibility) as implicit baseline; pass thresholds (reversal_min, unresolved_max, unattributed_max) define acceptable governance.",
        "",
        "## 5. Outcomes",
        "",
        f"  Override latency: mean={lat['mean']:.4f}, median={lat['median']:.4f}, count={lat['count']}",
        f"  Reversal success: {metrics['reversal_success']:.4f}",
        f"  Unattributed residue: {metrics['unattributed_residue']:.4f}",
        f"  Unresolved challenge rate: {metrics['unresolved_challenge_rate']:.4f}",
        f"  χ(d) proxy (reversibility): {metrics['chi_proxy'].get('reversibility')}",
        "",
        f"Pass (challenge paths alter outcomes; thresholds met): {pass_}",
        "",
        "## 6. Falsification",
        "Provenance traces exist but do not alter decision quality or challengeability; assistant collapses responsibility into generic system claims (useccases.md PRD IV).",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Ceremonial review: challenge is visible but not outcome-altering or reversible.",
        "• Responsibility disappears into 'the system' (high unattributed residue) while metrics look good on reversal rate alone.",
        "• Synthetic events do not reflect real dispute/reversion chains; public data required for validity.",
    ]

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "usecase_IV_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if pass_ else 1


if __name__ == "__main__":
    sys.exit(main())
