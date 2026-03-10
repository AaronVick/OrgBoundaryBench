#!/usr/bin/env python3
"""
End-to-end remote compute run: prepare payload → Claude API → verify → run_report.

Aligns with outputs/METHODOLOGY.md and scientific method: hypothesis, method, execution,
analysis (verification), reporting. Writes run_report.md and methodology-aligned
artifacts into outputs/remote_compute_claude/<run_id>/.

Run when ANTHROPIC_API_KEY is set (or in .env). See docs/REMOTE_COMPUTE_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]


def _make_labeled_npz(path: Path, n: int = 20, seed: int = 42) -> Path:
    import numpy as np
    rng = np.random.default_rng(seed)
    K = rng.uniform(0.1, 1.0, size=(n, n))
    K = K / K.sum(axis=1, keepdims=True)
    labels = rng.integers(0, 4, size=n, dtype=np.int64)
    mu = np.ones(n, dtype=np.float64) / n
    np.savez_compressed(path, K=K, labels=labels, mu=mu)
    return path


def _run(cmd: list[str], cwd: Path, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable] + cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def _latest_run_dir(out_dir: Path) -> Optional[Path]:
    if not out_dir.is_dir():
        return None
    dirs = [d for d in out_dir.iterdir() if d.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.stat().st_mtime)


def _write_run_report(run_dir: Path, run_id: str, model_id: str, payload_hash: str,
                      result: Dict[str, Any], verification: Dict[str, Any],
                      payload: Dict[str, Any], elapsed_seconds: float) -> None:
    """Write methodology-aligned run_report.md (PhD rigor, scientific method)."""
    bootstrap = result.get("bootstrap") or {}
    permutation = result.get("permutation") or {}
    lines = [
        "# Run report: Remote compute (Claude API)",
        "",
        f"**Run ID:** {run_id}  ",
        f"**Model:** {model_id}  ",
        "**Framework:** Boundary-Preserving Organization (null/rival audit, external agreement). Remote compute protocol: `docs/REMOTE_COMPUTE_PROTOCOL.md`.",
        "",
        "---",
        "",
        "## 1. Hypothesis and method",
        "",
        "- **Hypothesis:** The same bootstrap null-dominance and permutation external p-value procedures used in organizational design mapping can be executed in-context by Claude Opus 4.6 when given a small payload and explicit math instructions; results can be verified by re-running the same payload locally.",
        "- **Test design:** Payload (n, labels, q_star, rival_partitions, n_bootstrap, n_perm, seed) is sent with procedural instructions; model returns structured JSON (bootstrap CI, permutation p-values); verification compares remote result to local run on same payload.",
        "- **Falsification:** Remote result fails verification (numeric mismatch beyond tolerance); or model fails to return valid JSON.",
        "",
        "## 2. Environment",
        "",
        "| Item | Value |",
        "|------|--------|",
        f"| Model | {model_id} |",
        f"| Payload hash | {payload_hash} |",
        f"| Payload n | {payload.get('n', '—')} |",
        f"| n_bootstrap | {payload.get('n_bootstrap', '—')} |",
        f"| n_perm | {payload.get('n_perm', '—')} |",
        f"| seed | {payload.get('seed', '—')} |",
        f"| API elapsed (s) | {elapsed_seconds} |",
        "",
        "## 3. Commands executed",
        "",
        "```bash",
        "# Prepare payload (synthetic or from dataset)",
        "python scripts/prepare_remote_compute_payload.py --out-dir outputs/remote_compute_payloads ...",
        "# Remote compute via Claude API",
        "python scripts/run_remote_compute_claude.py --payload outputs/remote_compute_payloads/payload.json",
        "# Verify remote result against local run",
        "python scripts/verify_remote_compute.py --run-dir outputs/remote_compute_claude/<run_id>",
        "```",
        "",
        "## 4. Results (from model)",
        "",
        "### Bootstrap null dominance",
        "",
        "| Metric | Value |",
        "|--------|--------|",
    ]
    for k in ("mean_D", "std_D", "ci_lower", "ci_upper", "star_nmi_full", "best_rival_name_full", "best_rival_nmi_full", "pass"):
        v = bootstrap.get(k)
        if v is not None:
            lines.append(f"| {k} | {v} |")
    lines.extend([
        "",
        "### Permutation external p-values",
        "",
        "| Metric | Value |",
        "|--------|--------|",
    ])
    for k in ("nmi_star", "ari_star", "f1_star", "nmi_p_value", "ari_p_value", "f1_p_value"):
        v = permutation.get(k)
        if v is not None:
            lines.append(f"| {k} | {v} |")
    lines.extend([
        "",
        "## 5. Verification (local vs remote)",
        "",
        f"- **Bootstrap verified:** {verification.get('bootstrap_verified', '—')}",
        f"- **Permutation verified:** {verification.get('permutation_verified', '—')}",
        f"- **Overall verified:** {verification.get('overall_verified', '—')}",
        "",
        "## 6. Findings and limitations",
        "",
        "- **Process:** Data and instructions were sent to Claude Opus 4.6; the model returned structured JSON. Verification compares these to deterministic local runs on the same payload and seed.",
        "- **Limitations:** Context and token limits cap problem size; numeric precision and resampling order in the model may differ slightly from local numpy; API responses may vary. Results are documented as remote-compute runs and do not replace local runs where feasible.",
        "",
        "---",
        "",
        "*Generated by scripts/run_remote_compute_e2e.py. Traceability: docs/REMOTE_COMPUTE_PROTOCOL.md, outputs/METHODOLOGY.md §7.*",
    ])
    (run_dir / "run_report.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="E2E remote compute: prepare → API → verify → run_report.")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "remote_compute_claude")
    ap.add_argument("--payload-dir", type=Path, default=ROOT / "outputs" / "remote_compute_payloads")
    ap.add_argument("--dataset-npz", type=Path, default=None, help="If set, use this kernel; else create synthetic.")
    ap.add_argument("--max-nodes", type=int, default=24)
    ap.add_argument("--n-bootstrap", type=int, default=30)
    ap.add_argument("--n-perm", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out_dir = args.out_dir.resolve()
    payload_dir = args.payload_dir.resolve()
    payload_path = payload_dir / "payload.json"

    # 1. Ensure payload exists
    if not payload_path.exists():
        if args.dataset_npz and args.dataset_npz.exists():
            r = _run([
                str(ROOT / "scripts" / "prepare_remote_compute_payload.py"),
                "--dataset-npz", str(args.dataset_npz),
                "--out-dir", str(payload_dir),
                "--max-nodes", str(args.max_nodes),
                "--n-bootstrap", str(args.n_bootstrap),
                "--n-perm", str(args.n_perm),
                "--seed", str(args.seed),
            ], ROOT)
        else:
            tmp = out_dir / ".." / "remote_compute_e2e_tmp"
            tmp = tmp.resolve()
            tmp.mkdir(parents=True, exist_ok=True)
            kernel_path = tmp / "kernel_e2e.npz"
            _make_labeled_npz(kernel_path, n=args.max_nodes, seed=args.seed)
            payload_dir.mkdir(parents=True, exist_ok=True)
            r = _run([
                str(ROOT / "scripts" / "prepare_remote_compute_payload.py"),
                "--dataset-npz", str(kernel_path),
                "--out-dir", str(payload_dir),
                "--max-nodes", str(args.max_nodes),
                "--n-bootstrap", str(args.n_bootstrap),
                "--n-perm", str(args.n_perm),
                "--seed", str(args.seed),
            ], ROOT)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            return 1
    if not payload_path.exists():
        print("Payload not found after prepare", file=sys.stderr)
        return 1

    # 2. Run remote compute (API)
    r = _run([
        str(ROOT / "scripts" / "run_remote_compute_claude.py"),
        "--payload", str(payload_path),
        "--out-dir", str(out_dir),
    ], ROOT)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return 1
    run_dir = _latest_run_dir(out_dir)
    if not run_dir or not (run_dir / "result.json").exists():
        print("No run directory or result.json after API run", file=sys.stderr)
        return 1

    # 3. Verify
    r = _run([
        str(ROOT / "scripts" / "verify_remote_compute.py"),
        "--run-dir", str(run_dir),
        "--tolerance", "1e-2",
    ], ROOT)
    if r.returncode not in (0, 1):
        print(r.stderr, file=sys.stderr)
        return 1
    verification = {}
    v_path = run_dir / "verification_report.json"
    if v_path.exists():
        verification = json.loads(v_path.read_text())

    # 4. Write run_report.md
    result = json.loads((run_dir / "result.json").read_text())
    payload = json.loads((run_dir / "payload.json").read_text())
    meta = json.loads((run_dir / "run_metadata.json").read_text())
    _write_run_report(
        run_dir,
        run_id=meta.get("run_id", "unknown"),
        model_id=meta.get("model_id", "claude-opus-4-6"),
        payload_hash=meta.get("payload_hash", ""),
        result=result,
        verification=verification,
        payload=payload,
        elapsed_seconds=meta.get("elapsed_seconds", 0),
    )
    print(f"E2E complete: {run_dir}")
    print(f"  run_report.md, result.json, verification_report.json, payload.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
