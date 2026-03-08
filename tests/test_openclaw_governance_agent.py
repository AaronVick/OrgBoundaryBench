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


def _make_labeled_npz(path: Path, n: int = 20, seed: int = 43) -> Path:
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 3, size=n, dtype=np.int64)
    np.savez_compressed(path, K=K, labels=labels)
    return path


def test_governance_agent_emits_actionable_decision(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    db_path = workspace / "sqlite" / "orgbench.db"
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=20)

    lock_claim_scope(workspace)
    build_public_taskset(db_path, dataset, max_nodes=20, seed=9, workspace=workspace)
    for arm in ARMS:
        run_arm(
            db_path,
            dataset,
            arm=arm,
            backend="local_heuristic",
            split="test",
            max_nodes=20,
            seed=9,
            top_k_rag=5,
            workspace=workspace,
        )
    evaluate_latest_runs(db_path, split="test", n_bootstrap=20, seed=9, workspace=workspace)
    run_null_and_leverage_audit(db_path, metric="accuracy", n_permutations=20, seed=9, workspace=workspace)
    write_headline_table(db_path, workspace=workspace, metric="accuracy")

    bundle_dir = workspace / "openclaw"
    export_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "export_openclaw_bundle.py"),
        "--workspace",
        str(workspace),
        "--out-dir",
        str(bundle_dir),
    ]
    export_proc = subprocess.run(export_cmd, cwd=ROOT, capture_output=True, text=True)
    assert export_proc.returncode == 0, export_proc.stderr

    gov_out = bundle_dir / "governance"
    gov_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_openclaw_governance_agent.py"),
        "--bundle-dir",
        str(bundle_dir),
        "--out-dir",
        str(gov_out),
        "--policy",
        str(ROOT / "skill" / "governance_policy.json"),
    ]
    gov_proc = subprocess.run(gov_cmd, cwd=ROOT, capture_output=True, text=True)
    assert gov_proc.returncode == 0, gov_proc.stderr

    decision_path = gov_out / "governance_decision.json"
    actions_path = gov_out / "governance_actions.jsonl"
    brief_path = gov_out / "governance_brief.md"

    assert decision_path.exists()
    assert actions_path.exists()
    assert brief_path.exists()

    decision = json.loads(decision_path.read_text())
    assert decision["recommendation"] in {
        "BLOCK_DEPLOYMENT",
        "LIMITED_SHADOW_ONLY",
        "ALLOW_CONSTRAINED_DEPLOYMENT",
    }
    assert decision["operating_mode"] in {"blocked", "shadow", "constrained_live"}
    assert isinstance(decision["required_remediations"], list)
    assert "policy" in decision and "min_test_tasks_per_arm" in decision["policy"]

    # With small synthetic test slices and strict policy, governance should block deployment.
    assert decision["recommendation"] == "BLOCK_DEPLOYMENT"
