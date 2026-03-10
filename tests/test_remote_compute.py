"""Tests for remote-compute pipeline: prepare payload, verify (local vs local), API script fails without key, E2E with API (optional)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Run E2E test (prepare → API → verify → run_report) only when key is available and explicitly requested
RUN_REMOTE_E2E = os.environ.get("RUN_REMOTE_E2E", "").strip() == "1"


def _has_anthropic_key() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return True
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() in ("ANTHROPIC_API_KEY", "anthroptic_API_KEY") and val.strip():
                return True
    return False


def _make_labeled_npz(path: Path, n: int = 24, seed: int = 7) -> Path:
    import numpy as np
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 5, size=n, dtype=np.int64)
    mu = np.ones(n, dtype=np.float64) / n
    np.savez_compressed(path, K=K, labels=labels, mu=mu)
    return path


def test_prepare_remote_compute_payload_script(tmp_path: Path) -> None:
    """prepare_remote_compute_payload.py produces payload.json with required keys."""
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=24)
    out_dir = tmp_path / "payloads"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "prepare_remote_compute_payload.py"),
            "--dataset-npz",
            str(dataset),
            "--out-dir",
            str(out_dir),
            "--max-nodes",
            "24",
            "--n-bootstrap",
            "20",
            "--n-perm",
            "20",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    payload_path = out_dir / "payload.json"
    assert payload_path.exists()
    payload = json.loads(payload_path.read_text())
    assert payload["payload_version"] == "1.0"
    assert payload["task"] in ("bootstrap_null_dominance", "permutation_external_pvals", "combined")
    assert payload["n"] == 24
    assert len(payload["labels"]) == 24
    assert "q_star" in payload and len(payload["q_star"]) >= 1
    assert "rival_partitions" in payload and len(payload["rival_partitions"]) >= 1
    assert payload["n_bootstrap"] == 20
    assert payload["n_perm"] == 20
    assert "seed" in payload


def test_verify_remote_compute_script(tmp_path: Path) -> None:
    """verify_remote_compute.py runs and writes verification_report.json when payload + result exist."""
    import importlib.util
    import numpy as np
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=12)
    out_payload = tmp_path / "payloads"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "prepare_remote_compute_payload.py"),
            "--dataset-npz",
            str(dataset),
            "--out-dir",
            str(out_payload),
            "--max-nodes",
            "12",
            "--n-bootstrap",
            "5",
            "--n-perm",
            "5",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads((out_payload / "payload.json").read_text())
    # Run local bootstrap/perm via verify script's helpers to get a result that matches verification
    spec = importlib.util.spec_from_file_location(
        "verify_remote_compute",
        ROOT / "scripts" / "verify_remote_compute.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(mod)
    n = payload["n"]
    labels = np.array(payload["labels"], dtype=np.int64)
    q_star = payload["q_star"]
    rival_partitions = payload.get("rival_partitions", {})
    n_bootstrap = payload.get("n_bootstrap", 5)
    n_perm = payload.get("n_perm", 5)
    seed = payload.get("seed", 42)
    local_bootstrap = mod._bootstrap_null_dominance_local(
        q_star, rival_partitions, labels, n, n_bootstrap, seed
    )
    local_perm = mod._permutation_external_pvals_local(q_star, labels, n, n_perm, seed)
    result = {
        "run_id": "2026-03-08T120000Z",
        "model_id": "claude-opus-4-6",
        "payload_hash": "test_hash",
        "confirmation": "REMOTE_COMPUTE_v1",
        "bootstrap": local_bootstrap,
        "permutation": local_perm,
    }
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "payload.json").write_text(json.dumps(payload, indent=2))
    (run_dir / "result.json").write_text(json.dumps(result, indent=2))
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_remote_compute.py"),
            "--run-dir",
            str(run_dir),
            "--tolerance",
            "1e-6",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    report_path = run_dir / "verification_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report.get("overall_verified") is True


def test_run_remote_compute_claude_fails_without_api_key(tmp_path: Path) -> None:
    """run_remote_compute_claude.py exits non-zero when ANTHROPIC_API_KEY is unset."""
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=8)
    out_payload = tmp_path / "payloads"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "prepare_remote_compute_payload.py"),
            "--dataset-npz",
            str(dataset),
            "--out-dir",
            str(out_payload),
            "--max-nodes",
            "8",
            "--n-bootstrap",
            "3",
            "--n-perm",
            "3",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    env = {k: v for k, v in __import__("os").environ.items() if k != "ANTHROPIC_API_KEY"}
    env["SKIP_DOTENV"] = "1"  # script must not load repo .env so we truly test "no key"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_remote_compute_claude.py"),
            "--payload",
            str(out_payload / "payload.json"),
            "--out-dir",
            str(tmp_path / "remote_out"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode != 0
    assert "ANTHROPIC" in r.stderr or "Set" in r.stderr


@pytest.mark.skipif(not RUN_REMOTE_E2E or not _has_anthropic_key(), reason="RUN_REMOTE_E2E=1 and ANTHROPIC_API_KEY required for E2E API test")
def test_remote_compute_e2e_with_api(tmp_path: Path) -> None:
    """
    Full E2E: prepare payload → run_remote_compute_claude (real API) → verify → run_report.
    Uses existing testing framework (tmp_path, subprocess, assertions on outputs).
    Documents process and methodology via run_report.md and verification_report.json.
    """
    out_dir = tmp_path / "remote_compute_claude"
    payload_dir = tmp_path / "payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    # Synthetic kernel for reproducible payload
    dataset = _make_labeled_npz(tmp_path / "kernel.npz", n=16, seed=99)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "prepare_remote_compute_payload.py"),
            "--dataset-npz", str(dataset),
            "--out-dir", str(payload_dir),
            "--max-nodes", "16",
            "--n-bootstrap", "15",
            "--n-perm", "15",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_remote_compute_e2e.py"),
            "--out-dir", str(out_dir),
            "--payload-dir", str(payload_dir),
            "--max-nodes", "16",
            "--n-bootstrap", "15",
            "--n-perm", "15",
            "--seed", "99",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    run_dirs = [d for d in out_dir.iterdir() if d.is_dir()]
    assert len(run_dirs) >= 1
    run_dir = max(run_dirs, key=lambda d: d.stat().st_mtime)
    assert (run_dir / "payload.json").exists()
    assert (run_dir / "result.json").exists()
    assert (run_dir / "run_metadata.json").exists()
    assert (run_dir / "run_report.md").exists()
    assert (run_dir / "verification_report.json").exists()
    result = json.loads((run_dir / "result.json").read_text())
    report = (run_dir / "run_report.md").read_text()
    ver = json.loads((run_dir / "verification_report.json").read_text())
    assert result.get("model_id"), "model_id documented"
    assert result.get("confirmation") == "REMOTE_COMPUTE_v1", "confirmation present"
    assert "Hypothesis" in report and "Verification" in report, "run_report has methodology sections"
    assert "overall_verified" in ver, "verification outcome documented"
