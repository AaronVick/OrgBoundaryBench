from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from boundary_org.orgbench_staged import (
    ARMS,
    build_public_taskset,
    evaluate_latest_runs,
    lock_claim_scope,
    run_arm,
    run_null_and_leverage_audit,
    run_storage_review,
    write_headline_table,
)


def _make_labeled_npz(path: Path, n: int = 24, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 4, size=n, dtype=np.int64)
    np.savez_compressed(path, K=K, labels=labels)
    return path


def test_staged_pipeline_core(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    db_path = workspace / "sqlite" / "orgbench.db"
    dataset = _make_labeled_npz(tmp_path / "kernel.npz")

    review = run_storage_review(workspace, dataset, max_nodes=20)
    assert review["max_nodes_requested"] == 20

    prereg = lock_claim_scope(workspace)
    assert prereg["scope"] == "benchmark-in-progress"
    assert "H1" in prereg["hypotheses"][0]

    taskset = build_public_taskset(db_path, dataset, max_nodes=20, seed=5, workspace=workspace)
    assert taskset["n_tasks"] == 20
    assert taskset["split_counts"]["test"] > 0

    for arm in ARMS:
        out = run_arm(
            db_path,
            dataset,
            arm=arm,
            split="test",
            max_nodes=20,
            seed=11,
            top_k_rag=5,
            workspace=workspace,
        )
        assert out["arm"] == arm
        assert out["n_eval"] > 0

    eval_summary = evaluate_latest_runs(db_path, split="test", n_bootstrap=20, seed=13, workspace=workspace)
    assert "runs" in eval_summary and len(eval_summary["runs"]) >= 3
    for arm in ("plain_llm", "math_governed"):
        assert "accuracy" in eval_summary["runs"][arm]["metrics"]

    audit = run_null_and_leverage_audit(
        db_path,
        metric="accuracy",
        n_permutations=20,
        seed=17,
        workspace=workspace,
    )
    assert "null" in audit and "leverage" in audit
    assert "p_value" in audit["null"]

    report = write_headline_table(db_path, workspace=workspace, metric="accuracy")
    assert Path(report["headline_csv"]).exists()
    assert Path(report["headline_md"]).exists()
    headline = json.loads((workspace / "json" / "headline_report.json").read_text())
    assert "rows" in headline


def test_staged_runner_script(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    dataset = _make_labeled_npz(tmp_path / "kernel_script.npz", n=18, seed=19)

    def run_stage(stage: str, *extra: str) -> subprocess.CompletedProcess:
        cmd = [
            sys.executable,
            str(root / "scripts" / "run_orgbench_staged.py"),
            "--stage",
            stage,
            "--workspace",
            str(workspace),
            "--dataset-npz",
            str(dataset),
            "--max-nodes",
            "18",
            "--seed",
            "3",
            *extra,
        ]
        return subprocess.run(cmd, cwd=root, capture_output=True, text=True)

    assert run_stage("storage-review").returncode == 0
    assert run_stage("lock-scope").returncode == 0
    assert run_stage("build-taskset").returncode == 0
    assert run_stage("run-arm", "--arm", "plain_llm").returncode == 0
    assert run_stage("run-arm", "--arm", "plain_llm_rag").returncode == 0
    assert run_stage("run-arm", "--arm", "math_governed").returncode == 0
    assert run_stage("run-arm", "--arm", "sham_complexity").returncode == 0
    assert run_stage("run-arm", "--arm", "simple_graph").returncode == 0
    assert run_stage("evaluate", "--n-bootstrap", "10").returncode == 0
    # audit/report can return non-zero on gate failure; require artifact generation.
    audit = run_stage("audit", "--n-permutations", "10")
    assert (workspace / "json" / "audit_gate.json").exists(), audit.stderr
    report = run_stage("report")
    assert (workspace / "reports" / "headline_report.md").exists(), report.stderr


def test_anthropic_backend_requires_api_key(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    db_path = workspace / "sqlite" / "orgbench.db"
    dataset = _make_labeled_npz(tmp_path / "kernel_anthropic.npz", n=20, seed=23)
    build_public_taskset(db_path, dataset, max_nodes=20, seed=7, workspace=workspace)

    with pytest.raises(RuntimeError, match="Missing API key in env var: TEST_MISSING_ANTHROPIC_KEY"):
        run_arm(
            db_path,
            dataset,
            arm="plain_llm",
            backend="anthropic",
            split="test",
            max_nodes=20,
            seed=11,
            anthropic_api_key_env="TEST_MISSING_ANTHROPIC_KEY",
            workspace=workspace,
        )
