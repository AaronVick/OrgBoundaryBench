#!/usr/bin/env python3
"""
RCTI verification: run Relational Closure pipeline on synthetic/small graph and write outputs.

Produces empirical findings from the math (C1, C4b, C2F, barcode) into outputs/runs/<run_id>/.
PRD-13, docs/FRAMEWORKS.md. Use --out-dir to specify run directory (default: outputs/runs/<timestamp>).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from relational_closure.pipeline import run_pipeline


def make_synthetic_directed_cycle(n: int = 6, noise: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Directed cycle with optional random edges (for non-trivial β₁)."""
    if rng is None:
        rng = np.random.default_rng(42)
    W = np.zeros((n, n))
    for i in range(n):
        W[i, (i + 1) % n] = 1.0
    if noise > 0:
        for i in range(n):
            for j in range(n):
                if i != j and (i + 1) % n != j:
                    if rng.random() < noise:
                        W[i, j] = rng.uniform(0.3, 1.0)
    return W


def main() -> int:
    ap = argparse.ArgumentParser(description="RCTI verification: directed flag → barcode → C1/C4b/C2F.")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output run directory (default: outputs/runs/<ISO timestamp>)")
    ap.add_argument("--n", type=int, default=6, help="Synthetic cycle size")
    ap.add_argument("--noise", type=float, default=0.2, help="Extra edge noise for richer topology")
    ap.add_argument("--tau", type=float, default=0.1, help="C1 lifespan threshold")
    ap.add_argument("--no-gudhi", action="store_true", help="Disable gudhi (use cycle-rank proxy)")
    args = ap.parse_args()

    out_dir = args.out_dir
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out_dir = ROOT / "outputs" / "runs" / ts
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    W = make_synthetic_directed_cycle(n=args.n, noise=args.noise)
    result = run_pipeline(W, threshold=None, max_dim=4, tau=args.tau, use_gudhi=not args.no_gudhi)

    # Serializable summary (no numpy)
    barcode = result["barcode_dict"].get("barcode", {})
    barcode_ser = {str(k): [(float(b), float(d)) for (b, d) in v] for k, v in barcode.items()}
    betti_ser = {int(k): int(v) for k, v in result["betti"].items()}

    # 1. rcti_verification_report.txt
    lines = [
        "# RCTI verification report (Relational Closure / Topology of Interiority)",
        f"# Pipeline: directed_flag → persistence → C1/C4b/C2F",
        f"# Method: {result.get('method', 'unknown')}",
        "",
        f"C1: {result['C1']['message']}",
        f"C4b: {result['C4b']['message']}",
        f"Persistence entropy: {result['persistence_entropy']:.6f}",
        f"n_simplices: {result['n_simplices']}",
        "",
    ]
    if result.get("C2F") is not None:
        lines.append(f"C2F: {result['C2F']:.4f}")
    with open(out_dir / "rcti_verification_report.txt", "w") as f:
        f.write("\n".join(lines))

    # 2. barcode_summary.json
    with open(out_dir / "barcode_summary.json", "w") as f:
        json.dump({
            "barcode": barcode_ser,
            "betti": betti_ser,
            "method": result.get("method", "unknown"),
            "persistence_entropy": result["persistence_entropy"],
        }, f, indent=2)

    # 3. conditions_C1_C4_C2F.yaml (minimal YAML)
    yaml_lines = [
        "C1:",
        f"  satisfied: {result['C1']['satisfied']}",
        f"  message: \"{result['C1']['message']}\"",
        "C4b:",
        f"  satisfied: {result['C4b']['satisfied']}",
        f"  message: \"{result['C4b']['message']}\"",
    ]
    if result.get("C2F") is not None:
        yaml_lines.append(f"C2F: {result['C2F']:.4f}")
    with open(out_dir / "conditions_C1_C4_C2F.yaml", "w") as f:
        f.write("\n".join(yaml_lines))

    # 4. falsification_F1_F5.md
    fals = [
        "# Falsification checklist (PRD-13 §3)",
        "",
        "| ID | Condition | Status |",
        "|----|-----------|--------|",
        "| F1 | Barcode discrimination (conscious vs unconscious) | Not tested (synthetic only) |",
        "| F2 | C2F decorrelation with self-boundary phenomenology | Not tested |",
        "| F3 | Transformer surprise (C1–C4 satisfied by LLM) | Not tested |",
        "| F4 | Dissociation (HC vs C2F) | Not tested (single run) |",
        "| F5 | Density artifact (matched-density control) | N/A (single threshold) |",
        "",
        "Methodological constraints: matched-density and multi-construction required for neural/real-data runs.",
    ]
    with open(out_dir / "falsification_F1_F5.md", "w") as f:
        f.write("\n".join(fals))

    print("RCTI verification written to:", out_dir)
    print(result["C1"]["message"])
    print(result["C4b"]["message"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
