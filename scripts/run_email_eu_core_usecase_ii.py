#!/usr/bin/env python3
"""
Deliverable 1 (organizational_empirical_validation.md): Complete email-Eu-core Usecase II public run.

Runs Usecase II on data/processed/email_eu_core, writes usecase_II_report.txt and an outcomes
summary (outcomes_summary.yaml) for placeholder resolution and findings. Satisfies 4.4.1 and A8.1
when run to completion.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed" / "email_eu_core"
CANONICAL_OUT_DIR = ROOT / "outputs" / "runs" / "email_eu_core_usecase_ii"


def _parse_report(report_path: Path) -> dict:
    """Extract mean_D, ci_lower, ci_upper, S_max, overall pass from usecase_II_report.txt."""
    text = report_path.read_text()
    out = {}
    m = re.search(r"mean_D:\s*([-\d.]+)", text)
    if m:
        out["mean_D"] = float(m.group(1))
    m = re.search(r"CI_lower:\s*([-\d.]+)", text)
    if m:
        out["ci_lower"] = float(m.group(1))
    m = re.search(r"CI_upper:\s*([-\d.]+)", text)
    if m:
        out["ci_upper"] = float(m.group(1))
    m = re.search(r"S_max:\s*([-\d.]+)", text)
    if m:
        out["S_max"] = float(m.group(1))
    m = re.search(r"Overall pass \(null/rival and leverage\):\s*(\w+)", text)
    if m:
        out["overall_pass"] = m.group(1).strip().lower() == "true"
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Deliverable 1: email-Eu-core Usecase II public run.")
    ap.add_argument("--out-dir", type=Path, default=CANONICAL_OUT_DIR, help="Output directory for report and summary")
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR, help="Processed email_eu_core dir containing kernel.npz")
    args_run = ap.parse_args()
    data_dir = Path(args_run.data_dir).resolve()
    out_dir = Path(args_run.out_dir).resolve()

    if not (data_dir / "kernel.npz").exists():
        print(
            f"Missing {data_dir / 'kernel.npz'}. Run: python3 scripts/download_and_normalize.py --source email_eu_core",
            file=sys.stderr,
        )
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_usecase_ii_audit.py"),
        "--data",
        str(data_dir),
        "--out-dir",
        str(out_dir),
    ]
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0 and result.returncode != 1:
        return result.returncode  # 1 is acceptable (overall pass False)

    report_path = out_dir / "usecase_II_report.txt"
    if not report_path.exists():
        print(f"Expected report not found: {report_path}", file=sys.stderr)
        return 2

    summary = _parse_report(report_path)
    summary["run_date_utc"] = datetime.now(timezone.utc).isoformat()
    summary["data_source"] = "email_eu_core"
    summary["report_path"] = str(report_path)

    # Write machine-readable summary for findings/placeholder resolution
    summary_path = out_dir / "outcomes_summary.yaml"
    with open(summary_path, "w") as f:
        f.write("# Deliverable 1: email-Eu-core Usecase II outcomes (organizational_empirical_validation.md)\n")
        for k, v in summary.items():
            if isinstance(v, bool):
                f.write(f"{k}: {str(v).lower()}\n")
            elif isinstance(v, (int, float)):
                f.write(f"{k}: {v}\n")
            else:
                f.write(f"{k}: {repr(v)}\n")
    print(f"Wrote {report_path} and {summary_path}")
    return 0 if summary.get("overall_pass", False) else 1


if __name__ == "__main__":
    sys.exit(main())
