#!/usr/bin/env python3
"""
Usecase PRD VIII (useccases.md): Model Identity, Reproducibility, and Dev-Test Logging.

Emits a structured run-identity block and usecase_VIII_report.txt so every run can be audited.
For non-LLM runs we log: script, python version, seed, dataset_version, evaluation_timestamp,
config_hash; when LLM arms exist they add model_provider, model_name, etc.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git_commit() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Usecase PRD VIII: Emit run identity block and scientific-method report."
    )
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dataset-version", type=str, default="synthetic", help="e.g. synthetic, or path/version of dataset")
    ap.add_argument("--script-name", type=str, default="run_usecase_viii_identity.py")
    args = ap.parse_args()

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    config_str = f"script={args.script_name},seed={args.seed},dataset={args.dataset_version}"
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]

    identity = {
        "model_provider": "N/A (non-LLM run)",
        "model_name": args.script_name,
        "model_version": "1.0",
        "api_or_local_backend": "local",
        "temperature": None,
        "top_p": None,
        "seed": args.seed,
        "context_window": None,
        "embedding_model": None,
        "reranker_model": None,
        "tooling_enabled": [],
        "prompt_hash": None,
        "retrieval_config_hash": None,
        "config_hash": config_hash,
        "git_commit": _git_commit(),
        "dataset_version": args.dataset_version,
        "evaluation_timestamp": evaluation_timestamp,
        "python_version": sys.version.split()[0],
    }

    out_dir = args.out_dir or (ROOT / "outputs" / "runs" / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ"))
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "run_identity.json").write_text(json.dumps(identity, indent=2))

    data_provenance = (
        f"Dataset version: {args.dataset_version}. No public dataset loaded in this identity-only run. "
        "For LLM runs, model_provider, model_name, model_version, temperature, prompt_hash, etc. must be set."
    )
    lines = [
        "# Usecase PRD VIII: Model Identity, Reproducibility, and Dev-Test Logging",
        f"# Generated: {evaluation_timestamp}",
        "",
        "## 1. Hypothesis",
        "Every run must be auditable by model/backend and configuration; no run counts as valid without full identity (useccases.md PRD VIII).",
        "",
        "## 2. Methods",
        "Emit structured identity block (run_identity.json) with model_provider, model_name, seed, config_hash, git_commit, dataset_version, evaluation_timestamp.",
        "For non-LLM runs we log script name, python version, seed, dataset_version; LLM runs would add model_provider, model_name, temperature, prompt_hash, etc.",
        "",
        "## 3. Public data used",
        data_provenance,
        "",
        "## 4. Baseline",
        "N/A (identity contract only). Benchmark reports must group results by model/backend when multiple backends exist.",
        "",
        "## 5. Outcomes",
        "",
        f"  config_hash: {config_hash}",
        f"  git_commit: {identity['git_commit']}",
        f"  dataset_version: {identity['dataset_version']}",
        f"  evaluation_timestamp: {identity['evaluation_timestamp']}",
        "",
        "Identity block written to run_identity.json. Pass: identity emitted.",
        "",
        "## 6. Falsification",
        "Runs without identity block are not valid for benchmark reporting.",
        "",
        "## 7. What would make this look good while still being wrong?",
        "• Model drift (e.g. API version change) masquerading as algorithmic improvement if identity is not logged.",
        "• Benchmark-generation model vs evaluated assistant model must be distinguished when both exist.",
    ]
    report_path = out_dir / "usecase_VIII_report.txt"
    report_path.write_text("\n".join(lines))
    print(f"Wrote {report_path}")
    print(f"Wrote {out_dir / 'run_identity.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
