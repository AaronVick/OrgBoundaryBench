#!/usr/bin/env python3
"""
Run a staged OrgBench public campaign across increasing taskset sizes with hard gates,
OpenClaw export, and governance decisioning.

This script is designed to replace one-shot monolithic runs with phase-by-phase execution.
Each phase writes full artifacts and can stop early on governance block.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from boundary_org.orgbench_staged import (  # noqa: E402
    ARMS,
    BACKENDS,
    build_public_taskset,
    evaluate_latest_runs,
    lock_claim_scope,
    run_arm,
    run_null_and_leverage_audit,
    run_storage_review,
    write_headline_table,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_schedule(text: str) -> List[int]:
    vals: List[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        vals.append(int(part))
    if not vals:
        raise ValueError("node schedule is empty")
    # preserve order while removing duplicates
    seen = set()
    out: List[int] = []
    for v in vals:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


def _run_script(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def _export_openclaw(workspace: Path, out_dir: Path) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "export_openclaw_bundle.py"),
        "--workspace",
        str(workspace),
        "--out-dir",
        str(out_dir),
    ]
    r = _run_script(cmd)
    payload = json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "error": r.stderr.strip()}
    payload["returncode"] = r.returncode
    return payload


def _run_governance(bundle_dir: Path, out_dir: Path, policy: Path) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_openclaw_governance_agent.py"),
        "--bundle-dir",
        str(bundle_dir),
        "--out-dir",
        str(out_dir),
        "--policy",
        str(policy),
    ]
    r = _run_script(cmd)
    payload = json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "error": r.stderr.strip()}
    payload["returncode"] = r.returncode
    return payload


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _phase_row_from_report(phase: str, max_nodes: int, report_json: Dict[str, Any], governance_json: Dict[str, Any]) -> Dict[str, Any]:
    rows = report_json.get("rows", []) if isinstance(report_json.get("rows"), list) else []
    metric_math = None
    metric_best = None
    for r in rows:
        if not isinstance(r, dict):
            continue
        if r.get("arm") == "math_governed":
            metric_math = float(r.get("value", 0.0))
    audit = report_json.get("audit") if isinstance(report_json.get("audit"), dict) else {}
    headline = audit.get("headline") if isinstance(audit.get("headline"), dict) else {}
    metric_best = float(headline.get("best_baseline", 0.0)) if headline else 0.0
    return {
        "phase": phase,
        "max_nodes": max_nodes,
        "gate_pass": bool(report_json.get("gate_pass", False)),
        "math_governed_metric": metric_math if metric_math is not None else 0.0,
        "best_baseline_metric": metric_best if metric_best is not None else 0.0,
        "delta_vs_best": (metric_math if metric_math is not None else 0.0) - (metric_best if metric_best is not None else 0.0),
        "governance_recommendation": str(governance_json.get("recommendation", "UNKNOWN")),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run staged public OrgBench campaign across node-size phases.")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "orgbench_campaign")
    ap.add_argument("--dataset-npz", type=Path, default=ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz")
    ap.add_argument("--node-schedule", type=str, default="80,120,160", help="Comma-separated max_nodes phases")
    ap.add_argument("--backend", choices=BACKENDS, default="local_heuristic")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--top-k-rag", type=int, default=8)
    ap.add_argument("--max-greedy-n", type=int, default=40)
    ap.add_argument("--model-provider", type=str, default=None)
    ap.add_argument("--model-name", type=str, default=None)
    ap.add_argument("--model-version", type=str, default="1.0")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--openai-base-url", type=str, default=None)
    ap.add_argument("--openai-api-key-env", type=str, default="OPENAI_API_KEY")
    ap.add_argument("--anthropic-base-url", type=str, default=None)
    ap.add_argument("--anthropic-api-key-env", type=str, default="ANTHROPIC_API_KEY")
    ap.add_argument("--anthropic-version", type=str, default="2023-06-01")
    ap.add_argument("--allow-fallback", action="store_true")
    ap.add_argument("--n-bootstrap", type=int, default=100)
    ap.add_argument("--n-permutations", type=int, default=200)
    ap.add_argument("--metric", choices=["accuracy", "macro_f1", "balanced_accuracy"], default="accuracy")
    ap.add_argument("--policy", type=Path, default=ROOT / "skill" / "governance_policy.json")
    ap.add_argument("--stop-on-block", action="store_true", default=True)
    args = ap.parse_args()

    out_dir = args.out_dir.resolve()
    dataset_npz = args.dataset_npz.resolve()
    policy = args.policy.resolve()
    schedule = _parse_schedule(args.node_schedule)

    out_dir.mkdir(parents=True, exist_ok=True)

    campaign: Dict[str, Any] = {
        "created_at": _utc_now(),
        "dataset_npz": str(dataset_npz),
        "backend": args.backend,
        "seed": args.seed,
        "node_schedule": schedule,
        "phases": [],
        "stopped_early": False,
        "stop_reason": None,
    }

    for idx, max_nodes in enumerate(schedule, start=1):
        phase_name = f"phase_{idx:02d}_n{max_nodes}"
        workspace = out_dir / phase_name
        db_path = workspace / "sqlite" / "orgbench.db"
        workspace.mkdir(parents=True, exist_ok=True)

        phase: Dict[str, Any] = {
            "phase": phase_name,
            "max_nodes": max_nodes,
            "started_at": _utc_now(),
            "status": "running",
        }
        try:
            phase["storage_review"] = run_storage_review(workspace, dataset_npz, max_nodes=max_nodes)
            phase["scope"] = lock_claim_scope(workspace)
            phase["taskset"] = build_public_taskset(
                db_path,
                dataset_npz,
                max_nodes=max_nodes,
                seed=args.seed,
                workspace=workspace,
            )

            arm_runs: Dict[str, Any] = {}
            for arm in ARMS:
                arm_runs[arm] = run_arm(
                    db_path,
                    dataset_npz,
                    arm=arm,
                    backend=args.backend,
                    split="test",
                    max_nodes=max_nodes,
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
            phase["arm_runs"] = arm_runs

            phase["evaluation"] = evaluate_latest_runs(
                db_path,
                split="test",
                n_bootstrap=args.n_bootstrap,
                seed=args.seed,
                workspace=workspace,
            )
            phase["audit"] = run_null_and_leverage_audit(
                db_path,
                metric=args.metric,
                n_permutations=args.n_permutations,
                seed=args.seed,
                workspace=workspace,
            )
            phase["report"] = write_headline_table(db_path, workspace=workspace, metric=args.metric)

            openclaw_dir = workspace / "openclaw"
            phase["openclaw_export"] = _export_openclaw(workspace, openclaw_dir)
            gov_dir = openclaw_dir / "governance"
            phase["governance"] = _run_governance(openclaw_dir, gov_dir, policy)

            # Parse canonical files for summary regardless of script stdout.
            report_json = _read_json(workspace / "json" / "headline_report.json")
            governance_json = _read_json(gov_dir / "governance_decision.json")
            phase["summary"] = _phase_row_from_report(phase_name, max_nodes, report_json, governance_json)

            phase["status"] = "completed"
            phase["ended_at"] = _utc_now()
            campaign["phases"].append(phase)

            if args.stop_on_block and phase["summary"]["governance_recommendation"] == "BLOCK_DEPLOYMENT":
                campaign["stopped_early"] = True
                campaign["stop_reason"] = f"BLOCK_DEPLOYMENT at {phase_name}"
                break

        except Exception as e:
            phase["status"] = "failed"
            phase["ended_at"] = _utc_now()
            phase["error"] = str(e)
            campaign["phases"].append(phase)
            campaign["stopped_early"] = True
            campaign["stop_reason"] = f"error at {phase_name}: {e}"
            break

    # write campaign summaries
    summary_json_path = out_dir / "campaign_summary.json"
    summary_md_path = out_dir / "campaign_summary.md"
    summary_csv_path = out_dir / "campaign_summary.csv"

    summary_json_path.write_text(json.dumps(campaign, indent=2, sort_keys=True))

    rows = []
    for p in campaign["phases"]:
        if p.get("status") != "completed":
            continue
        s = p.get("summary", {})
        rows.append(
            {
                "phase": s.get("phase", p.get("phase")),
                "max_nodes": s.get("max_nodes", p.get("max_nodes")),
                "gate_pass": s.get("gate_pass", False),
                "math_governed_metric": s.get("math_governed_metric", 0.0),
                "best_baseline_metric": s.get("best_baseline_metric", 0.0),
                "delta_vs_best": s.get("delta_vs_best", 0.0),
                "governance_recommendation": s.get("governance_recommendation", "UNKNOWN"),
            }
        )

    with summary_csv_path.open("w", newline="") as f:
        fieldnames = [
            "phase",
            "max_nodes",
            "gate_pass",
            "math_governed_metric",
            "best_baseline_metric",
            "delta_vs_best",
            "governance_recommendation",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    md_lines = [
        "# OrgBench Public Campaign Summary",
        f"Generated: {_utc_now()}",
        "",
        f"Dataset: `{dataset_npz}`",
        f"Backend: `{args.backend}`",
        f"Node schedule: `{schedule}`",
        "",
        "| Phase | max_nodes | gate_pass | math_governed | best_baseline | delta | governance_recommendation |",
        "|---|---:|---|---:|---:|---:|---|",
    ]
    for r in rows:
        md_lines.append(
            f"| {r['phase']} | {r['max_nodes']} | {r['gate_pass']} | {r['math_governed_metric']:.4f} | {r['best_baseline_metric']:.4f} | {r['delta_vs_best']:.4f} | {r['governance_recommendation']} |"
        )
    md_lines.extend(
        [
            "",
            f"Stopped early: `{campaign['stopped_early']}`",
            f"Stop reason: `{campaign['stop_reason']}`",
        ]
    )
    summary_md_path.write_text("\n".join(md_lines) + "\n")

    out = {
        "ok": True,
        "campaign_summary_json": str(summary_json_path),
        "campaign_summary_csv": str(summary_csv_path),
        "campaign_summary_md": str(summary_md_path),
        "n_phases_completed": len(rows),
        "stopped_early": campaign["stopped_early"],
        "stop_reason": campaign["stop_reason"],
    }
    print(json.dumps(out, indent=2, sort_keys=True))

    if campaign["stopped_early"] and campaign["stop_reason"] and str(campaign["stop_reason"]).startswith("error"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
