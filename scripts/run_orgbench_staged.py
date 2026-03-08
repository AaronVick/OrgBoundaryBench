#!/usr/bin/env python3
"""
Staged OrgBench execution runner.

Runs one stage at a time so laptop execution remains stable and resumable:
- storage-review
- lock-scope
- build-taskset
- run-arm (single arm per invocation)
- evaluate
- audit
- report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from boundary_org.orgbench_staged import (
    ARMS,
    BACKENDS,
    build_public_taskset,
    lock_claim_scope,
    run_arm,
    run_null_and_leverage_audit,
    run_storage_review,
    write_headline_table,
    evaluate_latest_runs,
)


def _print_json(obj: dict) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run staged OrgBench pipeline (SQLite + JSON).")
    ap.add_argument(
        "--stage",
        required=True,
        choices=[
            "storage-review",
            "lock-scope",
            "build-taskset",
            "run-arm",
            "evaluate",
            "audit",
            "report",
        ],
    )
    ap.add_argument(
        "--workspace",
        type=Path,
        default=ROOT / "outputs" / "orgbench_staged",
        help="Workspace for sqlite/json/reports artifacts",
    )
    ap.add_argument(
        "--dataset-npz",
        type=Path,
        default=ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz",
        help="Labeled kernel npz (K, labels) used for taskset + runs",
    )
    ap.add_argument("--db-path", type=Path, default=None, help="SQLite path (default: <workspace>/sqlite/orgbench.db)")
    ap.add_argument("--max-nodes", type=int, default=120, help="Node cap for staged local runs")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--arm", choices=ARMS, default="plain_llm")
    ap.add_argument("--backend", choices=BACKENDS, default="local_heuristic")
    ap.add_argument("--split", choices=["train", "val", "test"], default="test")
    ap.add_argument("--top-k-rag", type=int, default=8)
    ap.add_argument("--max-greedy-n", type=int, default=40, help="Use greedy q* only up to this n; above uses fast fallback")
    ap.add_argument("--model-provider", type=str, default=None)
    ap.add_argument("--model-name", type=str, default=None)
    ap.add_argument("--model-version", type=str, default="1.0")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--openai-base-url", type=str, default=None)
    ap.add_argument("--openai-api-key-env", type=str, default="OPENAI_API_KEY")
    ap.add_argument("--anthropic-base-url", type=str, default=None)
    ap.add_argument("--anthropic-api-key-env", type=str, default="ANTHROPIC_API_KEY")
    ap.add_argument("--anthropic-version", type=str, default="2023-06-01")
    ap.add_argument("--allow-fallback", action="store_true", help="Fallback to local heuristic if backend call errors")
    ap.add_argument("--n-bootstrap", type=int, default=100)
    ap.add_argument("--n-permutations", type=int, default=200)
    ap.add_argument("--metric", type=str, default="accuracy", choices=["accuracy", "macro_f1", "balanced_accuracy"])
    args = ap.parse_args()

    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    db_path = args.db_path.resolve() if args.db_path else (workspace / "sqlite" / "orgbench.db")
    dataset_npz = args.dataset_npz.resolve()

    try:
        if args.stage == "storage-review":
            out = run_storage_review(workspace, dataset_npz, max_nodes=args.max_nodes)
            _print_json(out)
            return 0

        if args.stage == "lock-scope":
            out = lock_claim_scope(workspace)
            _print_json(out)
            return 0

        if args.stage == "build-taskset":
            out = build_public_taskset(
                db_path,
                dataset_npz,
                max_nodes=args.max_nodes,
                seed=args.seed,
                workspace=workspace,
            )
            _print_json(out)
            return 0

        if args.stage == "run-arm":
            out = run_arm(
                db_path,
                dataset_npz,
                arm=args.arm,
                backend=args.backend,
                split=args.split,
                max_nodes=args.max_nodes,
                seed=args.seed,
                top_k_rag=args.top_k_rag,
                max_greedy_n=args.max_greedy_n,
                model_provider=args.model_provider,
                model_name=args.model_name,
                model_version=args.model_version,
                temperature=args.temperature,
                openai_base_url=args.openai_base_url,
                openai_api_key_env=args.openai_api_key_env,
                anthropic_base_url=args.anthropic_base_url,
                anthropic_api_key_env=args.anthropic_api_key_env,
                anthropic_version=args.anthropic_version,
                strict_backend=not args.allow_fallback,
                workspace=workspace,
            )
            _print_json(out)
            return 0

        if args.stage == "evaluate":
            out = evaluate_latest_runs(
                db_path,
                split=args.split,
                n_bootstrap=args.n_bootstrap,
                seed=args.seed,
                workspace=workspace,
            )
            _print_json(out)
            return 0

        if args.stage == "audit":
            out = run_null_and_leverage_audit(
                db_path,
                metric=args.metric,
                n_permutations=args.n_permutations,
                seed=args.seed,
                workspace=workspace,
            )
            _print_json(out)
            return 0 if out.get("pass", False) else 1

        if args.stage == "report":
            out = write_headline_table(
                db_path,
                workspace=workspace,
                metric=args.metric,
            )
            _print_json(out)
            return 0 if out.get("gate_pass", False) else 1

        raise ValueError(f"Unhandled stage: {args.stage}")
    except Exception as e:
        print(json.dumps({"stage": args.stage, "error": str(e)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
