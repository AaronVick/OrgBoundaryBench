#!/usr/bin/env python3
"""
Single entry point: run full verification (pytest → report → optional figures and registry).

Usage:
  python scripts/run_verification.py              # pytest + report
  python scripts/run_verification.py --figures    # also plot MVP figures
  python scripts/run_verification.py --registry  # also update claim registry (if tests passed)
  python scripts/run_verification.py --all        # figures + registry

Exit code: 0 if pytest passed, else pytest's exit code. Report and figures are produced regardless.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description="Run verification suite (pytest, report, optional figures/registry).")
    ap.add_argument("--figures", action="store_true", help="Run plot_mvp_figures.py after report")
    ap.add_argument("--registry", action="store_true", help="Update claim_registry.yaml if pytest passed")
    ap.add_argument("--all", action="store_true", help="Equivalent to --figures --registry")
    args = ap.parse_args()
    do_figures = args.figures or args.all
    do_registry = args.registry or args.all

    # 1. Pytest
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=ROOT,
    )
    passed = r.returncode == 0

    # 2. Verification report (always)
    r2 = subprocess.run(
        [sys.executable, "scripts/generate_verification_report.py"],
        cwd=ROOT,
    )
    if r2.returncode != 0:
        print("Warning: generate_verification_report.py failed", file=sys.stderr)

    # 3. Figures (optional)
    if do_figures:
        subprocess.run(
            [sys.executable, "scripts/plot_mvp_figures.py"],
            cwd=ROOT,
        )

    # 4. Registry (only if pytest passed)
    if do_registry and passed:
        subprocess.run(
            [sys.executable, "scripts/update_claim_registry.py", "--result", "pass"],
            cwd=ROOT,
        )
    elif do_registry and not passed:
        subprocess.run(
            [sys.executable, "scripts/update_claim_registry.py", "--result", "fail"],
            cwd=ROOT,
        )

    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
