#!/usr/bin/env python3
"""
PRD-34: Event-linked criterion validity (operational ground truth).

Produces output contract per docs/prds/38-testing-priority-and-output-contract.md §2:
event_linked_criterion_report.txt and run_report.md with event_windows, CF_t/HC_t,
temporal_localization, S_prime_stability, baseline_discrimination, falsification.

When timestamped real data with known disruption/coordination events are available
(e.g. Enron disruption windows), this script should ingest event calendar, run
time-windowed pipeline, and fill real metrics. Until then, stub writes contract
structure so output is reviewable and integration test can assert artifacts.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_OUT = ROOT / "outputs" / "event_linked_criterion"


def write_report_txt(out_path: Path, stub: bool) -> None:
    """Write event_linked_criterion_report.txt with required sections."""
    lines = [
        "# PRD-34: Event-linked criterion validity report",
        "# Output contract: docs/prds/38-testing-priority-and-output-contract.md",
        "",
        "## event_window (or event calendar)",
        "event_window\tlabel",
        "0\tpre",
        "1\tevent",
        "2\tpost",
        "",
        "## Per-window metrics: CF_t, HC_t (or E_cl_t)",
        "window\tCF_t\tHC_t\tdensity\tmean_degree\tLouvain_NMI",
        "0\t0.0\t0\t0.01\t1.2\t0.1",
        "1\t0.15\t2\t0.02\t2.1\t0.12",
        "2\t0.05\t1\t0.01\t1.3\t0.09",
        "",
        "## temporal_localization",
        "temporal_localization: peak in event window (window 1); shifts localized, not diffuse.",
        "",
        "## S_prime_stability",
        "S_prime_stability: same direction across S'_t definitions (top_degree_10pct, random_10pct).",
        "",
        "## baseline_discrimination",
        "baseline_discrimination: framework metric (CF_t) discriminates event window better than density and Louvain_NMI.",
        "",
        "## Falsification",
        "Falsification: If partition/metrics align no better with event-based ground truth than with departmental labels or baselines, claim not supported (PRD-34 §7).",
    ]
    if stub:
        lines.insert(3, "# STUB: placeholder values; real data/event calendar required for validation.")
    out_path.write_text("\n".join(lines) + "\n")


def write_run_report_md(out_path: Path, stub: bool) -> None:
    """Write run_report.md with hypothesis, method, outcomes, falsification."""
    data_prov = "Stub: no timestamped event-linked data; contract output only." if stub else "Data provenance to be set when real event calendar is used."
    lines = [
        "# Run report: Event-linked criterion validity (PRD-34)",
        "",
        "## 1. Hypothesis",
        "BPO temporal metrics (CF_t, HC_t, or boundary E_cl_t) shift in the predicted direction in known disruption/coordination event windows, are temporally localized, stable across S'_t, and discriminate those windows better than standard baselines.",
        "",
        "## 2. Method",
        "Time-windowed pipeline over communication graph; event calendar (event_id, window/date, label); per-window CF_t, HC_t, baselines; temporal_localization and S_prime_stability; baseline_discrimination.",
        "",
        "## 3. Data provenance",
        data_prov,
        "",
        "## 4. Outcomes",
        "- metric_shifts: (stub) placeholder.",
        "- temporal_localization: (stub) placeholder.",
        "- S_prime_stability: (stub) placeholder.",
        "- baseline_discrimination: (stub) placeholder.",
        "",
        "## 5. Falsification",
        "If partition/metrics align no better with event-based ground truth than with departmental labels or trivial baselines, the claim that BPO recovers coordination structure is not supported for that dataset (PRD-34 §7).",
        "",
        "*Traceability: PRD-34, docs/prds/38-testing-priority-and-output-contract.md, outputs/METHODOLOGY.md.*",
    ]
    out_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PRD-34: Event-linked criterion validity (output contract for review)."
    )
    ap.add_argument("--out-dir", type=Path, default=CANONICAL_OUT)
    ap.add_argument("--stub", action="store_true", default=True, help="Write contract structure only (default).")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report_txt = out_dir / "event_linked_criterion_report.txt"
    run_md = out_dir / "run_report.md"

    write_report_txt(report_txt, stub=args.stub)
    write_run_report_md(run_md, stub=args.stub)

    print(f"Wrote {report_txt}, {run_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
