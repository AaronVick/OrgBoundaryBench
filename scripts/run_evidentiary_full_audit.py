#!/usr/bin/env python3
"""
Run the evidentiary full audit on email-Eu-core: ensure kernel exists (build if missing),
then run PRD-31 full null/rival/leverage audit. Output: outputs/email_eu_core_full_audit_evidentiary/.

Use this to push for evidentiary testing. See docs/evidentiary_roadmap.md.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz"
OUT_DIR = ROOT / "outputs" / "email_eu_core_full_audit_evidentiary"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Evidentiary full audit: build email-Eu-core kernel if needed, run PRD-31 full audit."
    )
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--feasible", action="store_true", help="Use --max-nodes 400 when building (faster/smaller run).")
    ap.add_argument("--bootstrap", type=int, default=100)
    ap.add_argument("--n-trials", type=int, default=5)
    ap.add_argument("--no-build", action="store_true", help="Do not build kernel if missing; exit with error.")
    args = ap.parse_args()

    kernel = KERNEL_PATH.resolve()
    if not kernel.exists():
        if args.no_build:
            print(f"Missing {kernel}. Run: python3 scripts/download_and_normalize.py --source email_eu_core [--full]", file=sys.stderr)
            return 1
        max_nodes = 400 if args.feasible else None
        cmd = [sys.executable, str(ROOT / "scripts" / "download_and_normalize.py"), "--source", "email_eu_core"]
        if max_nodes is not None:
            cmd += ["--max-nodes", "400"]
        else:
            cmd += ["--full"]
        print(f"Building kernel: {' '.join(cmd)}")
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            print("download_and_normalize failed.", file=sys.stderr)
            return 1
        if not kernel.exists():
            print("Kernel still missing after build.", file=sys.stderr)
            return 1

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd_audit = [
        sys.executable,
        str(ROOT / "scripts" / "run_email_eu_core_full_audit.py"),
        "--out-dir", str(out_dir),
        "--dataset-npz", str(kernel),
        "--bootstrap", str(args.bootstrap),
        "--n-trials", str(args.n_trials),
    ]
    print(f"Running full audit: {' '.join(cmd_audit)}")
    r = subprocess.run(cmd_audit, cwd=ROOT)
    if r.returncode != 0:
        print("Full audit script exited non-zero (gates may have failed; check report).", file=sys.stderr)
    print(f"Outputs: {out_dir}")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
