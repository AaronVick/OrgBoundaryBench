from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def _make_labeled_npz(path: Path, n: int = 24, seed: int = 99) -> Path:
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 4, size=n, dtype=np.int64)
    np.savez_compressed(path, K=K, labels=labels)
    return path


def test_run_orgbench_public_campaign_script(tmp_path: Path) -> None:
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=24)
    out_dir = tmp_path / "campaign"

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_orgbench_public_campaign.py"),
        "--out-dir",
        str(out_dir),
        "--dataset-npz",
        str(dataset),
        "--node-schedule",
        "12,16",
        "--backend",
        "local_heuristic",
        "--n-bootstrap",
        "10",
        "--n-permutations",
        "10",
    ]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    payload = json.loads(r.stdout)
    assert payload["ok"] is True
    assert Path(payload["campaign_summary_json"]).exists()
    assert Path(payload["campaign_summary_csv"]).exists()
    assert Path(payload["campaign_summary_md"]).exists()

    summary = json.loads(Path(payload["campaign_summary_json"]).read_text())
    assert "phases" in summary and len(summary["phases"]) >= 1
    first_phase = summary["phases"][0]
    assert "openclaw_export" in first_phase
    assert "governance" in first_phase
