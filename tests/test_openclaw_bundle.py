from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from boundary_org.orgbench_staged import (
    ARMS,
    build_public_taskset,
    evaluate_latest_runs,
    lock_claim_scope,
    run_arm,
    run_null_and_leverage_audit,
    write_headline_table,
)


ROOT = Path(__file__).resolve().parents[1]


def _make_labeled_npz(path: Path, n: int = 20, seed: int = 31) -> Path:
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 3, size=n, dtype=np.int64)
    np.savez_compressed(path, K=K, labels=labels)
    return path


def test_openclaw_manifest_and_schemas_exist() -> None:
    manifest_path = ROOT / "skill" / "manifest.json"
    task_schema = ROOT / "schemas" / "task.schema.json"
    run_schema = ROOT / "schemas" / "run.schema.json"
    report_schema = ROOT / "schemas" / "report.schema.json"
    governance_schema = ROOT / "schemas" / "governance_decision.schema.json"

    assert manifest_path.exists()
    assert task_schema.exists()
    assert run_schema.exists()
    assert report_schema.exists()
    assert governance_schema.exists()

    manifest = json.loads(manifest_path.read_text())
    caps = set(manifest.get("required_capabilities", []))
    required = {
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
    assert required.issubset(caps)


def test_export_openclaw_bundle_from_staged_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    db_path = workspace / "sqlite" / "orgbench.db"
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=20)

    lock_claim_scope(workspace)
    build_public_taskset(db_path, dataset, max_nodes=20, seed=7, workspace=workspace)
    for arm in ARMS:
        run_arm(
            db_path,
            dataset,
            arm=arm,
            backend="local_heuristic",
            split="test",
            max_nodes=20,
            seed=7,
            top_k_rag=5,
            workspace=workspace,
        )
    evaluate_latest_runs(db_path, split="test", n_bootstrap=20, seed=7, workspace=workspace)
    run_null_and_leverage_audit(db_path, metric="accuracy", n_permutations=20, seed=7, workspace=workspace)
    write_headline_table(db_path, workspace=workspace, metric="accuracy")

    out_dir = workspace / "openclaw"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "export_openclaw_bundle.py"),
        "--workspace",
        str(workspace),
        "--out-dir",
        str(out_dir),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr

    tasks_path = out_dir / "task_records.jsonl"
    runs_path = out_dir / "run_records.jsonl"
    report_path = out_dir / "report.json"
    validation_path = out_dir / "validation_report.json"
    assert tasks_path.exists()
    assert runs_path.exists()
    assert report_path.exists()
    assert validation_path.exists()

    validation = json.loads(validation_path.read_text())
    assert validation["valid"] is True
    assert validation["checks"]["task_records_count"] > 0
    assert validation["checks"]["run_records_count"] >= 5

    report = json.loads(report_path.read_text())
    assert report["claim_status"] in {"PROMOTE", "DO_NOT_PROMOTE"}
    assert report["negative_result_reporting"] is True
    assert isinstance(report["gate_pass"], bool)
