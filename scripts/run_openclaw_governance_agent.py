#!/usr/bin/env python3
"""
Actionable governance operator for OpenClaw bundles.

Consumes an exported OpenClaw bundle and emits an enforceable deployment decision:
- BLOCK_DEPLOYMENT
- LIMITED_SHADOW_ONLY
- ALLOW_CONSTRAINED_DEPLOYMENT

Outputs:
- governance/governance_decision.json
- governance/governance_actions.jsonl
- governance/governance_brief.md

This is intended for organizational governance role execution, not theoretical reporting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

ROOT = Path(__file__).resolve().parents[1]


DEFAULT_POLICY: Dict[str, Any] = {
    "metric": "accuracy",
    "required_arms": [
        "plain_llm",
        "plain_llm_rag",
        "math_governed",
        "sham_complexity",
        "simple_graph",
    ],
    "min_test_tasks_per_arm": 30,
    "min_delta_vs_baseline": 0.02,
    "max_ci_width": 0.40,
    "require_gate_pass": True,
    "require_bundle_valid": True,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(dict(r), sort_keys=True) + "\n")


def _load_policy(path: Path | None) -> Dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if path is not None:
        policy.update(_read_json(path))
    return policy


def _metric_value(run: Mapping[str, Any], metric: str) -> float:
    metrics = run.get("metrics")
    if not isinstance(metrics, dict):
        return 0.0
    m = metrics.get(metric)
    if not isinstance(m, dict):
        return 0.0
    return float(m.get("value", 0.0))


def _metric_n(run: Mapping[str, Any], metric: str) -> int:
    metrics = run.get("metrics")
    if not isinstance(metrics, dict):
        return 0
    m = metrics.get(metric)
    if not isinstance(m, dict):
        return 0
    return int(m.get("n", 0))


def _metric_ci_width(run: Mapping[str, Any], metric: str) -> float:
    metrics = run.get("metrics")
    if not isinstance(metrics, dict):
        return 0.0
    m = metrics.get(metric)
    if not isinstance(m, dict):
        return 0.0
    lo = float(m.get("ci_low", 0.0))
    hi = float(m.get("ci_high", 0.0))
    return hi - lo


def _index_runs_by_arm(runs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for r in runs:
        arm = str(r.get("arm", ""))
        if arm:
            out[arm] = r
    return out


def _model_identity_missing_fields(run: Mapping[str, Any]) -> List[str]:
    required = [
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
    ]
    mid = run.get("model_identity")
    if not isinstance(mid, dict):
        return required
    missing: List[str] = []
    for k in required:
        if k not in mid:
            missing.append(k)
            continue
        v = mid[k]
        if isinstance(v, str) and not v.strip():
            missing.append(k)
    return missing


def _remediation_for_code(code: str) -> Dict[str, Any]:
    mapping = {
        "bundle_invalid": (
            "Re-run bundle export and resolve contract validation errors before any governance decision.",
            "benchmark_operator",
            True,
        ),
        "gate_failed": (
            "Do not deploy. Re-run staged arms and pass null+leverage gates with preregistered thresholds.",
            "research_lead",
            True,
        ),
        "missing_required_arms": (
            "Run all required arms (plain_llm, plain_llm_rag, math_governed, sham_complexity, simple_graph) on same split/budget.",
            "benchmark_operator",
            True,
        ),
        "math_not_better_than_plain": (
            "No governance deployment claim allowed until math_governed beats plain_llm by configured minimum delta.",
            "research_lead",
            True,
        ),
        "math_not_better_than_rag": (
            "No governance deployment claim allowed until math_governed beats plain_llm_rag by configured minimum delta.",
            "research_lead",
            True,
        ),
        "math_not_better_than_sham": (
            "No governance deployment claim allowed until math_governed beats sham_complexity by configured minimum delta.",
            "research_lead",
            True,
        ),
        "sample_size_too_small": (
            "Increase task count per arm to policy minimum before deployment decision.",
            "benchmark_operator",
            True,
        ),
        "ci_too_wide": (
            "Increase evaluation sample and bootstrap stability to narrow uncertainty intervals.",
            "benchmark_operator",
            False,
        ),
        "model_identity_incomplete": (
            "Fix run identity logging for all arms (provider/name/version/hash/timestamp) before deployment decision.",
            "ml_platform_owner",
            True,
        ),
    }
    action, owner, blocking = mapping.get(
        code,
        ("Investigate governance policy failure and produce corrective action.", "governance_lead", True),
    )
    return {
        "id": code,
        "action": action,
        "owner_role": owner,
        "blocking": bool(blocking),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run OpenClaw governance operator on exported bundle.")
    ap.add_argument("--bundle-dir", type=Path, required=True, help="Path to OpenClaw bundle directory")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output dir (default: <bundle-dir>/governance)")
    ap.add_argument("--policy", type=Path, default=ROOT / "skill" / "governance_policy.json", help="Governance policy JSON")
    ap.add_argument("--exit-on-block", action="store_true", help="Return exit code 1 when recommendation is BLOCK_DEPLOYMENT")
    args = ap.parse_args()

    bundle_dir = args.bundle_dir.resolve()
    out_dir = args.out_dir.resolve() if args.out_dir else (bundle_dir / "governance")

    report_path = bundle_dir / "report.json"
    runs_path = bundle_dir / "run_records.jsonl"
    validation_path = bundle_dir / "validation_report.json"

    try:
        for p in [report_path, runs_path, validation_path]:
            if not p.exists():
                raise FileNotFoundError(f"Missing required bundle artifact: {p}")

        policy = _load_policy(args.policy.resolve() if args.policy else None)
        metric = str(policy.get("metric", "accuracy"))
        required_arms = [str(x) for x in policy.get("required_arms", [])]
        min_test_tasks = int(policy.get("min_test_tasks_per_arm", 1))
        min_delta = float(policy.get("min_delta_vs_baseline", 0.0))
        max_ci_width = float(policy.get("max_ci_width", 1.0))
        require_gate_pass = bool(policy.get("require_gate_pass", True))
        require_bundle_valid = bool(policy.get("require_bundle_valid", True))

        report = _read_json(report_path)
        runs = _read_jsonl(runs_path)
        validation = _read_json(validation_path)
        runs_by_arm = _index_runs_by_arm(runs)

        hard_failures: List[str] = []
        soft_failures: List[str] = []

        bundle_valid = bool(validation.get("valid", False))
        if require_bundle_valid and not bundle_valid:
            hard_failures.append("bundle_invalid")

        gate_pass = bool(report.get("gate_pass", False))
        if require_gate_pass and not gate_pass:
            hard_failures.append("gate_failed")

        missing_arms = [a for a in required_arms if a not in runs_by_arm]
        if missing_arms:
            hard_failures.append("missing_required_arms")

        # Model identity completeness.
        for arm, run in runs_by_arm.items():
            missing_mid = _model_identity_missing_fields(run)
            if missing_mid:
                hard_failures.append("model_identity_incomplete")
                break

        # Performance deltas against governance-critical baselines.
        if "math_governed" in runs_by_arm:
            math_val = _metric_value(runs_by_arm["math_governed"], metric)
            if "plain_llm" in runs_by_arm:
                if (math_val - _metric_value(runs_by_arm["plain_llm"], metric)) <= min_delta:
                    hard_failures.append("math_not_better_than_plain")
            if "plain_llm_rag" in runs_by_arm:
                if (math_val - _metric_value(runs_by_arm["plain_llm_rag"], metric)) <= min_delta:
                    hard_failures.append("math_not_better_than_rag")
            if "sham_complexity" in runs_by_arm:
                if (math_val - _metric_value(runs_by_arm["sham_complexity"], metric)) <= min_delta:
                    hard_failures.append("math_not_better_than_sham")

        # Sample size / uncertainty sufficiency.
        too_small = False
        ci_wide = False
        for arm, run in runs_by_arm.items():
            n = _metric_n(run, metric)
            if n < min_test_tasks:
                too_small = True
            if _metric_ci_width(run, metric) > max_ci_width:
                ci_wide = True
        if too_small:
            hard_failures.append("sample_size_too_small")
        if ci_wide:
            soft_failures.append("ci_too_wide")

        # Deduplicate while preserving order.
        hard_failures = list(dict.fromkeys(hard_failures))
        soft_failures = list(dict.fromkeys(soft_failures))

        if hard_failures:
            recommendation = "BLOCK_DEPLOYMENT"
            operating_mode = "blocked"
        elif soft_failures:
            recommendation = "LIMITED_SHADOW_ONLY"
            operating_mode = "shadow"
        else:
            recommendation = "ALLOW_CONSTRAINED_DEPLOYMENT"
            operating_mode = "constrained_live"

        remediations = [_remediation_for_code(c) for c in hard_failures + soft_failures]

        decision = {
            "decision_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_openclaw_gov",
            "generated_at": _utc_now(),
            "bundle_dir": str(bundle_dir),
            "recommendation": recommendation,
            "operating_mode": operating_mode,
            "hard_failures": hard_failures,
            "soft_failures": soft_failures,
            "required_remediations": remediations,
            "evidence": {
                "report_json": str(report_path),
                "run_records_jsonl": str(runs_path),
                "validation_report_json": str(validation_path),
            },
            "policy": {
                "metric": metric,
                "required_arms": required_arms,
                "min_test_tasks_per_arm": min_test_tasks,
                "min_delta_vs_baseline": min_delta,
                "max_ci_width": max_ci_width,
                "require_gate_pass": require_gate_pass,
                "require_bundle_valid": require_bundle_valid,
                "policy_hash": _sha16(json.dumps(policy, sort_keys=True)),
            },
        }

        out_dir.mkdir(parents=True, exist_ok=True)
        decision_path = out_dir / "governance_decision.json"
        actions_path = out_dir / "governance_actions.jsonl"
        brief_path = out_dir / "governance_brief.md"

        decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True))

        actions_rows = []
        for idx, r in enumerate(remediations, start=1):
            actions_rows.append(
                {
                    "action_id": f"A{idx:03d}",
                    "decision_id": decision["decision_id"],
                    "blocking": bool(r["blocking"]),
                    "owner_role": r["owner_role"],
                    "action": r["action"],
                }
            )
        _write_jsonl(actions_path, actions_rows)

        brief_lines = [
            "# OpenClaw Governance Brief",
            f"Generated: {decision['generated_at']}",
            "",
            f"Recommendation: **{recommendation}**",
            f"Operating mode: `{operating_mode}`",
            "",
            "## Hard failures",
        ]
        if hard_failures:
            for c in hard_failures:
                brief_lines.append(f"- {c}")
        else:
            brief_lines.append("- none")

        brief_lines.append("")
        brief_lines.append("## Soft failures")
        if soft_failures:
            for c in soft_failures:
                brief_lines.append(f"- {c}")
        else:
            brief_lines.append("- none")

        brief_lines.append("")
        brief_lines.append("## Required remediations")
        if remediations:
            for r in remediations:
                brief_lines.append(
                    f"- [{ 'BLOCKING' if r['blocking'] else 'NON-BLOCKING' }] {r['id']}: {r['action']} (owner: {r['owner_role']})"
                )
        else:
            brief_lines.append("- none")

        brief_path.write_text("\n".join(brief_lines) + "\n")

        print(
            json.dumps(
                {
                    "ok": True,
                    "decision": str(decision_path),
                    "actions": str(actions_path),
                    "brief": str(brief_path),
                    "recommendation": recommendation,
                },
                indent=2,
                sort_keys=True,
            )
        )

        if args.exit_on_block and recommendation == "BLOCK_DEPLOYMENT":
            return 1
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
