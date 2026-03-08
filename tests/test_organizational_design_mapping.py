from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def _make_labeled_npz(path: Path, n: int = 30, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 5, size=n, dtype=np.int64)
    mu = np.ones(n, dtype=np.float64) / n
    np.savez_compressed(path, K=K, labels=labels, mu=mu)
    return path


def test_run_organizational_design_mapping_script(tmp_path: Path) -> None:
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=30)
    out_dir = tmp_path / "org_map"

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_organizational_design_mapping.py"),
        "--dataset-npz",
        str(dataset),
        "--out-dir",
        str(out_dir),
        "--max-nodes",
        "30",
        "--n-random",
        "4",
        "--n-rewire",
        "2",
        "--n-permutations",
        "20",
        "--n-bootstrap",
        "20",
        "--framework-max-splits",
        "3",
        "--governance-max-events",
        "400",
    ]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert r.returncode in (0, 1), r.stderr

    payload = json.loads(r.stdout)
    assert payload["ok"] is True
    assert payload["decision"] in {"PASS", "FAIL"}

    required = [
        "organizational_design_map_report.md",
        "boundary_leaderboard.csv",
        "external_agreement_report.md",
        "stress_robustness_report.md",
        "null_rival_audit_report.md",
        "governance_preservation_report.md",
        "temporal_drift_report.md",
        "organizational_map_summary.json",
    ]
    for name in required:
        assert (out_dir / name).exists(), name

    summary = json.loads((out_dir / "organizational_map_summary.json").read_text())
    assert "tests" in summary
    assert "A_nontrivial_boundary" in summary["tests"]
    assert "decision" in summary
