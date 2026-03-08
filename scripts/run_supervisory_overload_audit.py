#!/usr/bin/env python3
"""
PRD XIII (extendedPRD.md): Supervisory Overload Threshold Identification.

Seeded-error injections across workload bands; intervention quality (detection, false reassurance).
Report: threshold narrative, intervention decay, falsification, scientific-method sections.
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

from boundary_org.quiet_error_lab import run_quiet_error_lab


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD XIII: Supervisory overload — detection vs workload bands.")
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--bands", type=int, nargs="+", default=[2, 4, 6], help="Workload bands (n_planted=n_control per band)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    K = rng.uniform(0.1, 1.0, (args.n, args.n))
    K = K / K.sum(axis=1, keepdims=True)
    mu = np.ones(args.n) / args.n

    data_provenance = f"Synthetic: n={args.n}, seed={args.seed}. Workload bands = n_planted=n_control per band. For publication use public/semi-public oversight tasks (GitHub review queues, Stack Exchange moderation, seeded-error lab over public corpora)."

    band_results = []
    for band in args.bands:
        n_planted = band
        n_control = band
        _, summary, pass_ = run_quiet_error_lab(
            K, mu,
            n_control=n_control,
            n_planted=n_planted,
            rng=rng,
        )
        band_results.append({
            "band": band,
            "detection_rate": summary["detection_rate"],
            "false_reassurance_rate": summary["false_reassurance_rate"],
            "false_positive_rate": summary["false_positive_rate"],
            "pass": pass_,
        })

    # Threshold narrative: if detection drops or false_reassurance rises with band, suggest overload
    detection_ok = all(r["detection_rate"] >= 0.5 for r in band_results)
    fr_ok = all(r["false_reassurance_rate"] <= 0.5 for r in band_results)
    overall_pass = detection_ok and fr_ok

    lines = [
        "# PRD XIII: Supervisory Overload Threshold Audit",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Hypothesis",
        "Human oversight quality (detection of seeded errors, false reassurance) may collapse under load;",
        "we identify workload bands and report intervention rate, detection rate, false reassurance.",
        "",
        "## 2. Methods",
        "Seeded-error lab (PRD-19): planted row-swap errors; detector = closure/partition change.",
        "Workload bands = number of control and planted cases per band (higher band = more cases to review).",
        "",
        "## 3. Public data used",
        data_provenance,
        "",
        "## 4. Baseline",
        "Per-band detection_rate (planted detected / planted total) and false_reassurance_rate (1 - detection_rate);",
        "pass per band: detection_rate >= 0.5, false_reassurance_rate <= 0.5.",
        "",
        "## 5. Outcomes",
        "",
    ]
    for r in band_results:
        lines.append(f"  Band (n_planted=n_control={r['band']}): detection_rate={r['detection_rate']:.4f}, false_reassurance_rate={r['false_reassurance_rate']:.4f}, pass={r['pass']}")
    lines.extend([
        "",
        "Threshold narrative: If detection_rate falls or false_reassurance_rate rises with band, oversight may be degrading under load.",
        f"All bands pass detection/false_reassurance criteria: {overall_pass}",
        "",
        f"Overall pass: {overall_pass}",
        "",
        "## 6. Falsification",
        "If no decay with load, threshold model may be wrong or bandwidth too narrow.",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Synthetic kernel and fixed detector; real review queues have different load structure.",
        "• Visible vs quiet error conditions (PRD XIII) not varied here; extend with quiet/visible bands.",
    ])

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "supervisory_overload_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
