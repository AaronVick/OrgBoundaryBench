#!/usr/bin/env python3
"""
PRD XV (extendedPRD.md): Contestability and Legitimacy Field Benchmark.

Test whether better contestability improves perceived legitimacy and better decisions.
χ = min(p_reach, v, a, r). Experimental conditions (plain, +provenance, +alternatives,
+reversible, full Aaron) — this run uses synthetic event sets as structural proxy.
Report: Hypothesis, Methods, Public data used, Baseline, Outcomes (contestability-performance
tradeoff, contestability-legitimacy relationship), Falsification, "What would make this look good but be wrong".
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


def make_events(n: int, reversal_ratio: float, unattributed_ratio: float, seed: int = 42) -> list:
    import numpy as np
    rng = np.random.default_rng(seed)
    events = []
    for i in range(n):
        outcome = "reversed" if rng.random() < reversal_ratio else "denied"
        agent = None if rng.random() < unattributed_ratio else f"agent_{i % 3}"
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
        description="PRD XV: Contestability and legitimacy field benchmark — scientific-method report."
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    # Structural proxy for conditions: "low contestability" vs "high contestability" event sets
    low_cont = make_events(args.n, reversal_ratio=0.2, unattributed_ratio=0.6, seed=args.seed)
    high_cont = make_events(args.n, reversal_ratio=0.6, unattributed_ratio=0.15, seed=args.seed + 1)

    m_low, pass_low = run_governance_metrics(low_cont, reversal_success_min=0.2, unresolved_rate_max=0.9, unattributed_max=0.9)
    m_high, pass_high = run_governance_metrics(high_cont, reversal_success_min=0.2, unresolved_rate_max=0.9, unattributed_max=0.9)

    data_provenance = (
        f"Synthetic: n={args.n}, seed={args.seed}. Two event sets (low vs high reversal/attribution) as structural proxy for "
        "experimental conditions (plain assistant vs +provenance vs +reversible vs full Aaron). "
        "No public data. extendedPRD XV: public GitHub decision/review tasks, wiki governance/dispute tasks, "
        "public discussion-thread escalation; local user-study layer over public corpora for publication."
    )

    # Contestability-performance: higher reversal + lower unattributed → pass more often
    # Contestability-legitimacy: structural proxy (reversal_success, unattributed) as stand-in for perceived legitimacy
    tradeoff_ok = m_high["reversal_success"] >= m_low["reversal_success"] and m_high["unattributed_residue"] <= m_low["unattributed_residue"]
    chaos_note = "Cases where more contestability creates chaos: not assessed in this run (single synthetic comparison)."

    lines = [
        "# PRD XV: Contestability and Legitimacy Field Benchmark",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Hypothesis",
        "Better contestability (χ = min(p_reach, v, a, r)) improves perceived legitimacy and better decisions. "
        "Extended PRD XV: experimental conditions plain assistant, +provenance, +alternatives, +reversible, full Aaron; "
        "outcomes: challenge rate, challenge success, decision correction, perceived legitimacy, time to recover, reduction in ceremonial oversight.",
        "",
        "## 2. Methods",
        "We run governance metrics on two synthetic event sets (low vs high reversal/attribution) as a structural proxy for "
        "low vs high contestability. Metrics: reversal success, unattributed residue, unresolved rate, χ(d) proxy. "
        "Contestability-performance tradeoff: higher reversal and lower unattributed in high-contestability set. "
        "Full experiment requires user-study or public task comparison across conditions.",
        "",
        "## 3. Public data used",
        data_provenance,
        "",
        "## 4. Baseline",
        "Plain assistant (no provenance/reversibility) = low-contestability proxy. High-contestability set = structural proxy for "
        "+provenance, +alternatives, +reversible or full Aaron design. Pass thresholds (reversal_min, unattributed_max) define acceptable governance.",
        "",
        "## 5. Outcomes",
        "",
        "Low contestability (proxy):",
        f"  reversal_success={m_low['reversal_success']:.4f}, unattributed_residue={m_low['unattributed_residue']:.4f}, pass={pass_low}",
        "",
        "High contestability (proxy):",
        f"  reversal_success={m_high['reversal_success']:.4f}, unattributed_residue={m_high['unattributed_residue']:.4f}, pass={pass_high}",
        "",
        "Contestability-performance tradeoff (high ≥ reversal of low, high ≤ unattributed of low): " + str(tradeoff_ok),
        "Contestability-legitimacy relationship: structural proxy only; perceived legitimacy requires user-study or survey.",
        "",
        chaos_note,
        "",
        "Pass (both sets evaluated; tradeoff direction as expected): " + str(tradeoff_ok),
        "",
        "## 6. Falsification",
        "If more contestability does not improve outcomes or legitimacy in controlled comparison; or if contestability creates chaos "
        "rather than real governance (extendedPRD XV).",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Reversal rate high but responsibility still collapsed (unattributed); report both reversal and unattributed.",
        "• Synthetic events do not reflect real GitHub/wiki/Apache tasks; public-data or user-study required.",
        "• Perceived legitimacy and ceremonial oversight reduction require human subjects or survey; not in this run.",
    ]

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "extended_contestability_legitimacy_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if tradeoff_ok else 1


if __name__ == "__main__":
    sys.exit(main())
