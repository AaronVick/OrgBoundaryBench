#!/usr/bin/env python3
"""
Export staged OrgBench artifacts into an OpenClaw-style skill bundle and validate
against the repository's machine-readable contract.

Bundle outputs:
- task_records.jsonl
- run_records.jsonl
- report.json
- validation_report.json

Exit code:
- 0: valid bundle
- 1: validation errors (unless --allow-invalid)
- 2: fatal build error
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_MANIFEST_CAPABILITIES = {
    "ingest_public_or_local_corpus",
    "build_sqlite_local_rag_index",
    "run_plain_llm_arm",
    "run_math_governed_arm",
    "run_sham_complexity_arm",
    "score_outputs_with_uncertainty",
    "emit_findings_reports",
    "log_model_identity",
    "emit_governance_decision",
    "emit_governance_remediation_actions",
}

ALLOWED_ARMS = {
    "plain_llm",
    "plain_llm_rag",
    "math_governed",
    "sham_complexity",
    "simple_graph",
}

ALLOWED_SPLITS = {"train", "val", "test"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _normalize_task(row: Mapping[str, Any]) -> Dict[str, Any]:
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    dataset = str(meta.get("dataset") or "unknown")
    node_id = int(row.get("node_id", -1))
    degree = float(row.get("degree", 0.0))
    gold_label = int(row.get("gold_label"))
    return {
        "task_id": str(row["task_id"]),
        "dataset": dataset,
        "task_family": "routing_and_ownership",
        "prompt": str(row["prompt"]),
        "context_refs": [f"node:{node_id}", f"dataset:{dataset}"],
        "gold_json": {"label": gold_label},
        "split": str(row["split"]),
        "notes": {
            "node_id": node_id,
            "degree": degree,
            "source": "staged_orgbench_taskset",
        },
    }


def _metric_or_default(metrics: Mapping[str, Any], metric_name: str) -> Dict[str, Any]:
    m = metrics.get(metric_name)
    if not isinstance(m, dict):
        return {"value": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 1}
    return {
        "value": float(m.get("value", 0.0)),
        "ci_low": float(m.get("ci_low", 0.0)),
        "ci_high": float(m.get("ci_high", 0.0)),
        "n": int(m.get("n", 1)),
    }


def _build_run_records(
    workspace_json: Path,
    eval_summary: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    runs = eval_summary.get("runs")
    if not isinstance(runs, dict):
        return []

    out: List[Dict[str, Any]] = []
    for arm, arm_payload in runs.items():
        if not isinstance(arm_payload, dict):
            continue
        run_id = str(arm_payload.get("run_id", ""))
        if not run_id:
            continue
        metrics = arm_payload.get("metrics") if isinstance(arm_payload.get("metrics"), dict) else {}
        identity_path = workspace_json / f"run_identity_{run_id}.json"
        if not identity_path.exists():
            continue
        identity = _read_json(identity_path)
        backend = str(identity.get("backend", "unknown"))

        out.append(
            {
                "run_id": run_id,
                "arm": str(arm),
                "backend": backend,
                "split": str(eval_summary.get("split", "test")),
                "model_identity": {
                    "model_provider": str(identity.get("model_provider", "unknown")),
                    "model_name": str(identity.get("model_name", "unknown")),
                    "model_version": str(identity.get("model_version", "unknown")),
                    "temperature": float(identity.get("temperature", 0.0)),
                    "seed": int(identity.get("seed", 0)),
                    "config_hash": str(identity.get("config_hash", "")),
                    "prompt_hash": str(identity.get("prompt_hash", "")),
                    "rag_hash": str(identity.get("rag_hash", "")),
                    "dataset_version": str(identity.get("dataset_version", "unknown")),
                    "evaluation_timestamp": str(identity.get("evaluation_timestamp", "")),
                },
                "metrics": {
                    "accuracy": _metric_or_default(metrics, "accuracy"),
                    "macro_f1": _metric_or_default(metrics, "macro_f1"),
                    "balanced_accuracy": _metric_or_default(metrics, "balanced_accuracy"),
                },
                "artifact_paths": {
                    "predictions_jsonl": str((workspace_json / f"predictions_{run_id}.jsonl").resolve()),
                    "run_identity_json": str(identity_path.resolve()),
                },
                "status": "completed",
            }
        )
    return out


def _build_report(
    workspace: Path,
    prereg: Mapping[str, Any],
    audit_gate: Mapping[str, Any],
    headline: Mapping[str, Any],
) -> Dict[str, Any]:
    gate_pass = bool(headline.get("gate_pass", False))
    claim_status = "PROMOTE" if gate_pass else "DO_NOT_PROMOTE"
    audit_headline = audit_gate.get("headline") if isinstance(audit_gate.get("headline"), dict) else {}
    null_audit = audit_gate.get("null") if isinstance(audit_gate.get("null"), dict) else {}
    leverage_audit = audit_gate.get("leverage") if isinstance(audit_gate.get("leverage"), dict) else {}

    return {
        "report_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "source_workspace": str(workspace.resolve()),
        "generated_at": _utc_now(),
        "scope": str(prereg.get("scope", "benchmark-in-progress")),
        "hypotheses": list(prereg.get("hypotheses", [])),
        "falsification": list(prereg.get("falsification", [])),
        "gates": dict(prereg.get("gates", {})),
        "headline": {
            "metric": str(audit_headline.get("metric", "accuracy")),
            "math_governed": float(audit_headline.get("math_governed", 0.0)),
            "baseline_metrics": dict(audit_headline.get("baseline_metrics", {})),
            "best_baseline": float(audit_headline.get("best_baseline", 0.0)),
            "delta_vs_best_baseline": float(audit_headline.get("delta_vs_best_baseline", 0.0)),
        },
        "null_audit": {
            "n_permutations": int(null_audit.get("n_permutations", 0)),
            "p_value": float(null_audit.get("p_value", 1.0)),
            "pass": bool(null_audit.get("pass", False)),
        },
        "leverage_audit": {
            "degree_cutoff_90pct": float(leverage_audit.get("degree_cutoff_90pct", 0.0)),
            "delta_full": float(leverage_audit.get("delta_full", 0.0)),
            "delta_without_top_degree": float(leverage_audit.get("delta_without_top_degree", 0.0)),
            "delta_drop": float(leverage_audit.get("delta_drop", 0.0)),
            "pass": bool(leverage_audit.get("pass", False)),
        },
        "gate_pass": gate_pass,
        "claim_status": claim_status,
        "negative_result_reporting": True,
        "rows": [
            {
                "arm": str(r.get("arm", "")),
                "run_id": str(r.get("run_id", "")),
                "metric": str(r.get("metric", "accuracy")),
                "value": float(r.get("value", 0.0)),
                "ci_low": float(r.get("ci_low", 0.0)),
                "ci_high": float(r.get("ci_high", 0.0)),
                "n": int(r.get("n", 0)),
            }
            for r in list(headline.get("rows", []))
        ],
    }


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _validate_task(obj: Mapping[str, Any], where: str, errors: List[str]) -> None:
    req = ["task_id", "dataset", "task_family", "prompt", "context_refs", "gold_json", "split", "notes"]
    for k in req:
        if k not in obj:
            errors.append(f"{where}: missing key {k}")
    if not isinstance(obj.get("task_id"), str) or not obj.get("task_id"):
        errors.append(f"{where}: task_id must be non-empty string")
    if not isinstance(obj.get("dataset"), str) or not obj.get("dataset"):
        errors.append(f"{where}: dataset must be non-empty string")
    if not isinstance(obj.get("prompt"), str) or not obj.get("prompt"):
        errors.append(f"{where}: prompt must be non-empty string")
    if obj.get("split") not in ALLOWED_SPLITS:
        errors.append(f"{where}: split must be one of {sorted(ALLOWED_SPLITS)}")
    if not isinstance(obj.get("context_refs"), list) or not obj.get("context_refs"):
        errors.append(f"{where}: context_refs must be non-empty list")
    if not isinstance(obj.get("gold_json"), dict) or not obj.get("gold_json"):
        errors.append(f"{where}: gold_json must be non-empty object")


def _validate_metric_obj(obj: Mapping[str, Any], where: str, errors: List[str]) -> None:
    for k in ["value", "ci_low", "ci_high", "n"]:
        if k not in obj:
            errors.append(f"{where}: missing metric key {k}")
    if not _is_number(obj.get("value")):
        errors.append(f"{where}: value must be number")
    if not _is_number(obj.get("ci_low")):
        errors.append(f"{where}: ci_low must be number")
    if not _is_number(obj.get("ci_high")):
        errors.append(f"{where}: ci_high must be number")
    n = obj.get("n")
    if not isinstance(n, int) or n < 1:
        errors.append(f"{where}: n must be integer >= 1")


def _validate_run(obj: Mapping[str, Any], where: str, errors: List[str]) -> None:
    req = ["run_id", "arm", "backend", "split", "model_identity", "metrics", "artifact_paths", "status"]
    for k in req:
        if k not in obj:
            errors.append(f"{where}: missing key {k}")
    if obj.get("arm") not in ALLOWED_ARMS:
        errors.append(f"{where}: invalid arm {obj.get('arm')}")
    if obj.get("split") not in ALLOWED_SPLITS:
        errors.append(f"{where}: invalid split {obj.get('split')}")
    if obj.get("status") not in {"completed", "failed", "running"}:
        errors.append(f"{where}: invalid status {obj.get('status')}")

    mid = obj.get("model_identity")
    if not isinstance(mid, dict):
        errors.append(f"{where}: model_identity must be object")
    else:
        for k in [
            "model_provider",
            "model_name",
            "model_version",
            "temperature",
            "seed",
            "config_hash",
            "prompt_hash",
            "rag_hash",
            "dataset_version",
            "evaluation_timestamp",
        ]:
            if k not in mid:
                errors.append(f"{where}: model_identity missing {k}")

    metrics = obj.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{where}: metrics must be object")
    else:
        for k in ["accuracy", "macro_f1", "balanced_accuracy"]:
            if k not in metrics or not isinstance(metrics.get(k), dict):
                errors.append(f"{where}: metrics missing {k}")
            else:
                _validate_metric_obj(metrics[k], f"{where}.metrics.{k}", errors)

    artifacts = obj.get("artifact_paths")
    if not isinstance(artifacts, dict):
        errors.append(f"{where}: artifact_paths must be object")
    else:
        for k in ["predictions_jsonl", "run_identity_json"]:
            if not isinstance(artifacts.get(k), str) or not artifacts.get(k):
                errors.append(f"{where}: artifact_paths.{k} must be non-empty string")


def _validate_report(obj: Mapping[str, Any], where: str, errors: List[str]) -> None:
    req = [
        "report_id",
        "source_workspace",
        "generated_at",
        "scope",
        "hypotheses",
        "falsification",
        "gates",
        "headline",
        "null_audit",
        "leverage_audit",
        "gate_pass",
        "claim_status",
        "negative_result_reporting",
        "rows",
    ]
    for k in req:
        if k not in obj:
            errors.append(f"{where}: missing key {k}")

    if obj.get("claim_status") not in {"PROMOTE", "DO_NOT_PROMOTE"}:
        errors.append(f"{where}: invalid claim_status {obj.get('claim_status')}")
    if not isinstance(obj.get("gate_pass"), bool):
        errors.append(f"{where}: gate_pass must be boolean")
    if not isinstance(obj.get("negative_result_reporting"), bool):
        errors.append(f"{where}: negative_result_reporting must be boolean")

    rows = obj.get("rows")
    if not isinstance(rows, list):
        errors.append(f"{where}: rows must be list")
    else:
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{where}.rows[{i}]: row must be object")
                continue
            for k in ["arm", "run_id", "metric", "value", "ci_low", "ci_high", "n"]:
                if k not in row:
                    errors.append(f"{where}.rows[{i}]: missing {k}")


def _validate_manifest(errors: List[str]) -> Dict[str, Any]:
    manifest_path = ROOT / "skill" / "manifest.json"
    if not manifest_path.exists():
        errors.append("skill/manifest.json is missing")
        return {}
    manifest = _read_json(manifest_path)
    capabilities = set(manifest.get("required_capabilities", []))
    missing_cap = sorted(REQUIRED_MANIFEST_CAPABILITIES - capabilities)
    if missing_cap:
        errors.append(f"manifest missing required capabilities: {missing_cap}")

    contracts = manifest.get("contracts") if isinstance(manifest.get("contracts"), dict) else {}
    for key in ["task_schema", "run_schema", "report_schema", "governance_decision_schema"]:
        rel = contracts.get(key)
        if not isinstance(rel, str) or not rel:
            errors.append(f"manifest contracts.{key} missing")
            continue
        if not (ROOT / rel).exists():
            errors.append(f"manifest contracts.{key} path missing: {rel}")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="Export OpenClaw bundle from staged OrgBench workspace.")
    ap.add_argument("--workspace", type=Path, required=True, help="Workspace path (e.g., outputs/orgbench_real_local)")
    ap.add_argument("--out-dir", type=Path, default=None, help="Bundle output directory (default: <workspace>/openclaw)")
    ap.add_argument("--allow-invalid", action="store_true", help="Return 0 even when validation fails")
    args = ap.parse_args()

    workspace = args.workspace.resolve()
    out_dir = args.out_dir.resolve() if args.out_dir else (workspace / "openclaw")
    workspace_json = workspace / "json"

    try:
        required_files = {
            "taskset": workspace_json / "taskset.jsonl",
            "evaluation": workspace_json / "evaluation_summary.json",
            "headline": workspace_json / "headline_report.json",
            "audit": workspace_json / "audit_gate.json",
            "prereg": workspace_json / "preregistered_claims.json",
        }
        missing_required = [name for name, path in required_files.items() if not path.exists()]
        if missing_required:
            raise FileNotFoundError(f"Missing required staged artifact files: {missing_required}")

        out_dir.mkdir(parents=True, exist_ok=True)

        task_rows_raw = _read_jsonl(required_files["taskset"])
        task_rows = [_normalize_task(r) for r in task_rows_raw]
        run_rows = _build_run_records(workspace_json, _read_json(required_files["evaluation"]))
        report_obj = _build_report(
            workspace,
            _read_json(required_files["prereg"]),
            _read_json(required_files["audit"]),
            _read_json(required_files["headline"]),
        )

        tasks_path = out_dir / "task_records.jsonl"
        runs_path = out_dir / "run_records.jsonl"
        report_path = out_dir / "report.json"
        validation_path = out_dir / "validation_report.json"

        _write_jsonl(tasks_path, task_rows)
        _write_jsonl(runs_path, run_rows)
        report_path.write_text(json.dumps(report_obj, indent=2, sort_keys=True))

        errors: List[str] = []
        _validate_manifest(errors)

        for i, row in enumerate(task_rows):
            _validate_task(row, f"task_records[{i}]", errors)
        for i, row in enumerate(run_rows):
            _validate_run(row, f"run_records[{i}]", errors)
        _validate_report(report_obj, "report", errors)

        valid = len(errors) == 0
        validation = {
            "created_at": _utc_now(),
            "bundle_dir": str(out_dir),
            "schemas": {
                "task": str((ROOT / "schemas" / "task.schema.json").resolve()),
                "run": str((ROOT / "schemas" / "run.schema.json").resolve()),
                "report": str((ROOT / "schemas" / "report.schema.json").resolve()),
            },
            "checks": {
                "task_records_count": len(task_rows),
                "run_records_count": len(run_rows),
                "gate_pass": bool(report_obj.get("gate_pass", False)),
                "claim_status": report_obj.get("claim_status", "DO_NOT_PROMOTE"),
            },
            "valid": valid,
            "errors": errors,
        }
        validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True))

        print(
            json.dumps(
                {
                    "ok": valid,
                    "bundle_dir": str(out_dir),
                    "tasks": str(tasks_path),
                    "runs": str(runs_path),
                    "report": str(report_path),
                    "validation": str(validation_path),
                    "n_errors": len(errors),
                },
                indent=2,
                sort_keys=True,
            )
        )
        if valid or args.allow_invalid:
            return 0
        return 1
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
