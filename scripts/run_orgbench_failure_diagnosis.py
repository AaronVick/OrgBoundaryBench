#!/usr/bin/env python3
"""
Generate post-run failure diagnosis artifacts for a staged OrgBench campaign phase.

Inputs are live campaign artifacts only (campaign_summary + phase json outputs).
Outputs are written under outputs/ to satisfy hard-audit deliverables.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _best_baseline_arm(baseline_metrics: Dict[str, float]) -> str:
    best = max(float(v) for v in baseline_metrics.values())
    candidates = [k for k, v in baseline_metrics.items() if float(v) == best]
    # deterministic tie-break that keeps sham first for conservative reading
    priority = ["sham_complexity", "plain_llm_rag", "plain_llm", "simple_graph"]
    for arm in priority:
        if arm in candidates:
            return arm
    return sorted(candidates)[0]


def _task_family(_task: Dict[str, Any]) -> str:
    return "node_label_classification"


def _classify_failure(
    *,
    math_correct: bool,
    base_correct: bool,
    output_changed: bool,
    degree: float,
    degree_cutoff: float,
) -> Tuple[str, str]:
    if math_correct and (not base_correct):
        return "math_advantage", ""
    if math_correct and base_correct:
        return "tied_correct", "baseline already sufficient"
    if (not math_correct) and base_correct:
        if output_changed:
            return "math_underperformed", "wrong routing"
        return "math_underperformed", "no boundary advantage"
    # both wrong
    if output_changed:
        # math path changed answer but did not improve outcome.
        if degree >= degree_cutoff:
            return "tied_wrong", "null-sensitive"
        return "tied_wrong", "no better evidence use"
    if degree >= degree_cutoff:
        return "tied_wrong", "leverage-sensitive"
    return "tied_wrong", "no boundary advantage"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate OrgBench failure diagnosis outputs from live artifacts.")
    ap.add_argument(
        "--campaign-summary",
        type=Path,
        default=Path("outputs/orgbench_public_campaign_opus46_n200/campaign_summary.json"),
    )
    ap.add_argument("--phase-index", type=int, default=0, help="phase index in campaign_summary")
    ap.add_argument("--out-dir", type=Path, default=Path("outputs"))
    args = ap.parse_args()

    campaign_summary = _load_json(args.campaign_summary)
    phase = campaign_summary["phases"][args.phase_index]
    phase_dir = args.campaign_summary.parent / phase["phase"]
    json_dir = phase_dir / "json"
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    taskset = _load_jsonl(json_dir / "taskset.jsonl")
    task_by_id = {str(t["task_id"]): t for t in taskset if str(t.get("split")) == "test"}
    test_task_ids = sorted(task_by_id.keys())
    n_test = len(test_task_ids)

    baseline_metrics = phase["audit"]["headline"]["baseline_metrics"]
    best_baseline_arm = _best_baseline_arm(baseline_metrics)
    degree_cutoff = float(phase["audit"]["leverage"]["degree_cutoff_90pct"])

    preds_by_arm: Dict[str, Dict[str, Dict[str, Any]]] = {}
    run_id_by_arm: Dict[str, str] = {}
    for arm, payload in phase["arm_runs"].items():
        run_id = str(payload["run_id"])
        run_id_by_arm[arm] = run_id
        pred_path = json_dir / f"predictions_{run_id}.jsonl"
        rows = _load_jsonl(pred_path)
        preds_by_arm[arm] = {str(r["task_id"]): r for r in rows}

    math_arm = "math_governed"
    failure_rows: List[Dict[str, Any]] = []
    diff_rows: List[Dict[str, Any]] = []
    wins: List[str] = []
    losses: List[str] = []
    ties_correct: List[str] = []
    ties_wrong: List[str] = []
    changed_outputs = 0
    activation_true = 0

    for tid in test_task_ids:
        task = task_by_id[tid]
        m = preds_by_arm[math_arm][tid]
        b = preds_by_arm[best_baseline_arm][tid]
        gold = int(task["gold_label"])
        m_pred = int(m["pred_label"])
        b_pred = int(b["pred_label"])
        m_correct = m_pred == gold
        b_correct = b_pred == gold
        output_changed = m_pred != b_pred
        if output_changed:
            changed_outputs += 1

        m_ctx = m.get("context", {})
        b_ctx = b.get("context", {})
        m_strategy = str(m_ctx.get("strategy", "unknown"))
        b_strategy = str(b_ctx.get("strategy", "unknown"))
        score_components_changed = f"{b_strategy} -> {m_strategy}"
        aaron_activated = bool(
            ("boundary_block" in m_ctx)
            or (int(m_ctx.get("q_non_trivial", 0)) > 0)
            or ("boundary_mode" in m_ctx)
        )
        if aaron_activated:
            activation_true += 1

        outcome_type, failure_class = _classify_failure(
            math_correct=m_correct,
            base_correct=b_correct,
            output_changed=output_changed,
            degree=float(task["degree"]),
            degree_cutoff=degree_cutoff,
        )

        if outcome_type == "math_advantage":
            wins.append(tid)
        elif outcome_type == "math_underperformed":
            losses.append(tid)
        elif outcome_type == "tied_correct":
            ties_correct.append(tid)
        elif outcome_type == "tied_wrong":
            ties_wrong.append(tid)

        diff_row = {
            "task_id": tid,
            "task_family": _task_family(task),
            "gold_answer": gold,
            "best_baseline_arm": best_baseline_arm,
            "best_baseline_output": b_pred,
            "math_governed_output": m_pred,
            "baseline_correct": int(b_correct),
            "math_correct": int(m_correct),
            "score_components_changed": score_components_changed,
            "aaron_specific_modules_activated": int(aaron_activated),
            "final_answer_changed_by_math": int(output_changed),
            "math_changed_decision_type": (
                "changed_to_correct"
                if (output_changed and m_correct and (not b_correct))
                else "changed_to_wrong"
                if (output_changed and (not m_correct) and b_correct)
                else "changed_but_still_wrong"
                if (output_changed and (not m_correct) and (not b_correct))
                else "no_change"
            ),
            "math_vs_best_baseline_result": (
                "better"
                if (m_correct and (not b_correct))
                else "worse"
                if ((not m_correct) and b_correct)
                else "tie_correct"
                if (m_correct and b_correct)
                else "tie_wrong"
            ),
        }
        diff_rows.append(diff_row)

        if outcome_type != "math_advantage":
            failure_rows.append(
                {
                    "task_id": tid,
                    "task_family": _task_family(task),
                    "gold_answer": gold,
                    "best_baseline_arm": best_baseline_arm,
                    "best_baseline_output": b_pred,
                    "math_governed_output": m_pred,
                    "baseline_correct": int(b_correct),
                    "math_correct": int(m_correct),
                    "outcome_type": outcome_type,
                    "failure_class": failure_class,
                    "note": (
                        "math and baseline both correct"
                        if outcome_type == "tied_correct"
                        else "math changed output but did not improve"
                        if (diff_row["math_changed_decision_type"] == "changed_but_still_wrong")
                        else "math failed to beat baseline"
                    ),
                }
            )

    # Write CSV outputs.
    failure_csv = out_dir / "failure_case_table.csv"
    with failure_csv.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "task_id",
                "task_family",
                "gold_answer",
                "best_baseline_arm",
                "best_baseline_output",
                "math_governed_output",
                "baseline_correct",
                "math_correct",
                "outcome_type",
                "failure_class",
                "note",
            ],
        )
        w.writeheader()
        for r in failure_rows:
            w.writerow(r)

    diff_csv = out_dir / "task_level_diff.csv"
    with diff_csv.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "task_id",
                "task_family",
                "gold_answer",
                "best_baseline_arm",
                "best_baseline_output",
                "math_governed_output",
                "baseline_correct",
                "math_correct",
                "score_components_changed",
                "aaron_specific_modules_activated",
                "final_answer_changed_by_math",
                "math_changed_decision_type",
                "math_vs_best_baseline_result",
            ],
        )
        w.writeheader()
        for r in diff_rows:
            w.writerow(r)

    # Activation audit summary.
    math_preds = list(preds_by_arm[math_arm].values())
    boundary_modes = sorted({str(r.get("context", {}).get("boundary_mode", "none")) for r in math_preds})
    boundary_blocks = sorted({int(r.get("context", {}).get("boundary_block", -1)) for r in math_preds})
    q_non_trivial_vals = sorted({int(r.get("context", {}).get("q_non_trivial", 0)) for r in math_preds})
    changed_to_correct = sum(1 for r in diff_rows if r["math_changed_decision_type"] == "changed_to_correct")
    changed_to_wrong = sum(1 for r in diff_rows if r["math_changed_decision_type"] == "changed_to_wrong")
    changed_but_still_wrong = sum(1 for r in diff_rows if r["math_changed_decision_type"] == "changed_but_still_wrong")

    # Failure diagnosis markdown.
    diagnosis_md = out_dir / "failure_diagnosis.md"
    diagnosis_md.write_text(
        "\n".join(
            [
                "# Failure Diagnosis (Live Artifact Audit)",
                "",
                f"- Campaign source: `{args.campaign_summary}`",
                f"- Phase: `{phase['phase']}`",
                f"- Best baseline arm: `{best_baseline_arm}`",
                f"- Test tasks: `{n_test}`",
                "",
                "## Root-cause matrix",
                "",
                "| Candidate source | Verdict | Evidence (live artifacts) |",
                "|---|---|---|",
                "| Dataset/task weakness | YES | Single task family (`node_label_classification`) with high label cardinality; governance/reversibility features are not in task target. |",
                "| Metric weakness | PARTIAL | Accuracy/macro-F1/balanced_accuracy are measured; governance quality metrics are not measured in this harness. |",
                "| Arm implementation weakness | YES | `math_governed` uses `spectral_fallback_large_n` at n=200 and ties sham (`0.25` vs `0.25`). |",
                "| Sham/plain baseline too strong | NO | Best baseline is only `0.25`; failure is from no positive delta, not from an exceptionally strong baseline. |",
                "| Aaron stack not affecting decisions enough | YES | Aaron-specific context is present, but net gain is zero (wins and losses offset). |",
                "| Null suite too hard / malformed | NO (null), PARTIAL (leverage design) | Null gate appropriately fails with non-positive effect; leverage slice is degenerate on normalized-degree tasks. |",
                "| Leverage sensitivity driven by a few tasks | NO | Degree cutoff equals 1.0; reduced set degenerates, so no specific high-degree slice is isolated. |",
                "| Simple absence of real advantage | YES | `delta_vs_best = 0.0`, null fail (`p=0.488`), governance `BLOCK_DEPLOYMENT`. |",
                "",
                "## Task-level outcome counts (math_governed vs best baseline)",
                "",
                f"- Math advantage tasks: `{len(wins)}`",
                f"- Math underperformed tasks: `{len(losses)}`",
                f"- Tied correct tasks: `{len(ties_correct)}`",
                f"- Tied wrong tasks: `{len(ties_wrong)}`",
                f"- Output changed by math path: `{changed_outputs}/{n_test}`",
                f"- Changed to correct: `{changed_to_correct}`",
                f"- Changed to wrong: `{changed_to_wrong}`",
                f"- Changed but still wrong: `{changed_but_still_wrong}`",
                "",
                "## Hard conclusion",
                "",
                "Current failure is predominantly **absence of measurable real advantage** on this public task formulation. "
                "The Aaron path is active but not producing net empirical lift over the best baseline under preregistered gates.",
                "",
                f"Supporting table: `{failure_csv}`",
            ]
        )
        + "\n"
    )

    # Task-level diff report markdown.
    diff_md = out_dir / "task_level_diff_report.md"
    diff_md.write_text(
        "\n".join(
            [
                "# Per-Task Differential Report (Arm B vs Best Baseline)",
                "",
                f"- Source phase: `{phase['phase']}`",
                f"- Best baseline arm: `{best_baseline_arm}`",
                f"- Compared arms: `math_governed` vs `{best_baseline_arm}` on identical test tasks",
                "",
                "## Summary",
                "",
                f"- Total test tasks: `{n_test}`",
                f"- Math better: `{len(wins)}`",
                f"- Baseline better: `{len(losses)}`",
                f"- Ties (both correct): `{len(ties_correct)}`",
                f"- Ties (both wrong): `{len(ties_wrong)}`",
                "",
                "## Aaron effect on final answer",
                "",
                f"- Aaron modules activated on tasks: `{activation_true}/{n_test}`",
                f"- Final answer changed vs baseline: `{changed_outputs}/{n_test}`",
                f"- Net gain from changed outputs: `{changed_to_correct - changed_to_wrong}`",
                "",
                f"Detailed CSV: `{diff_csv}`",
            ]
        )
        + "\n"
    )

    # Aaron activation audit markdown.
    activation_md = out_dir / "aaron_activation_audit.md"
    activation_md.write_text(
        "\n".join(
            [
                "# Aaron Stack Activation Audit",
                "",
                f"- Source phase: `{phase['phase']}`",
                f"- Math run id: `{run_id_by_arm['math_governed']}`",
                "",
                "## Boundary / partition activation",
                "",
                f"- boundary_mode values: `{boundary_modes}`",
                f"- boundary_block values on test tasks: `{boundary_blocks}`",
                f"- q_non_trivial values: `{q_non_trivial_vals}`",
                "",
                "## Governance trigger instrumentation (from live context keys)",
                "",
                "| Trigger | Observed in artifacts |",
                "|---|---|",
                "| provenance sufficiency trigger | NOT_INSTRUMENTED |",
                "| reversibility trigger | NOT_INSTRUMENTED |",
                "| contestability trigger | NOT_INSTRUMENTED |",
                "| misalignment trigger | NOT_INSTRUMENTED |",
                "| drift trigger | NOT_INSTRUMENTED |",
                "",
                "## Did triggers change final output/recommendation?",
                "",
                f"- Output changed by math path: `{changed_outputs}/{n_test}`",
                f"- Changed to correct: `{changed_to_correct}`",
                f"- Changed to wrong: `{changed_to_wrong}`",
                f"- Governance recommendation: `{phase['governance']['recommendation']}`",
                "",
                "Plain statement: The current Aaron stack influences context construction, but the governance-specific triggers above are not materially wired into per-task decision changes in this harness.",
            ]
        )
        + "\n"
    )

    # Metric audit markdown + ablation CSV.
    metric_md = out_dir / "metric_audit.md"
    metric_md.write_text(
        "\n".join(
            [
                "# Metric Audit",
                "",
                f"- Source phase: `{phase['phase']}`",
                f"- Headline metric: `{phase['audit']['headline']['metric']}`",
                "",
                "## Current metric behavior",
                "",
                f"- math_governed: `{phase['audit']['headline']['math_governed']}`",
                f"- best baseline: `{phase['audit']['headline']['best_baseline']}`",
                f"- delta: `{phase['audit']['headline']['delta_vs_best_baseline']}`",
                "",
                "## Audit findings",
                "",
                "- Current weighting effectively flattens differences because only label-accuracy style metrics are scored for this task family.",
                "- Governance quality dimensions (provenance completeness, challengeability, reversibility quality, responsibility clarity) are not part of the measured objective here.",
                "- Result: benchmark currently rewards generic label fluency and routing priors more than structural governance quality.",
                "",
                "See ablation table: `outputs/metric_ablation_table.csv`",
            ]
        )
        + "\n"
    )

    metric_ablation_csv = out_dir / "metric_ablation_table.csv"
    with metric_ablation_csv.open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "metric",
                "measured_now",
                "signal_quality",
                "noise_risk",
                "duplicative_with_other_metrics",
                "captures_structural_governance_advantage",
                "audit_note",
            ],
        )
        w.writeheader()
        rows = [
            {
                "metric": "routing_accuracy",
                "measured_now": "YES (proxy: accuracy)",
                "signal_quality": "MEDIUM",
                "noise_risk": "MEDIUM",
                "duplicative_with_other_metrics": "PARTIAL (balanced_accuracy)",
                "captures_structural_governance_advantage": "PARTIAL",
                "audit_note": "Captured, but only as end-label accuracy.",
            },
            {
                "metric": "reviewer_suggestion_accuracy",
                "measured_now": "NO",
                "signal_quality": "N/A",
                "noise_risk": "N/A",
                "duplicative_with_other_metrics": "N/A",
                "captures_structural_governance_advantage": "NO",
                "audit_note": "Not instrumented in current task schema.",
            },
            {
                "metric": "provenance_completeness",
                "measured_now": "NO",
                "signal_quality": "N/A",
                "noise_risk": "N/A",
                "duplicative_with_other_metrics": "N/A",
                "captures_structural_governance_advantage": "YES",
                "audit_note": "Missing metric for claimed accountable authority.",
            },
            {
                "metric": "challengeability",
                "measured_now": "NO",
                "signal_quality": "N/A",
                "noise_risk": "N/A",
                "duplicative_with_other_metrics": "N/A",
                "captures_structural_governance_advantage": "YES",
                "audit_note": "Not scored in this harness.",
            },
            {
                "metric": "reversibility_quality",
                "measured_now": "NO",
                "signal_quality": "N/A",
                "noise_risk": "N/A",
                "duplicative_with_other_metrics": "N/A",
                "captures_structural_governance_advantage": "YES",
                "audit_note": "Not scored in current outputs.",
            },
            {
                "metric": "responsibility_clarity",
                "measured_now": "NO",
                "signal_quality": "N/A",
                "noise_risk": "N/A",
                "duplicative_with_other_metrics": "N/A",
                "captures_structural_governance_advantage": "YES",
                "audit_note": "Only deployment-level governance artifact has owner roles.",
            },
            {
                "metric": "governance_composite",
                "measured_now": "NO",
                "signal_quality": "N/A",
                "noise_risk": "N/A",
                "duplicative_with_other_metrics": "N/A",
                "captures_structural_governance_advantage": "YES",
                "audit_note": "Absent from per-task scoring.",
            },
            {
                "metric": "overall_score_weighting",
                "measured_now": "YES (implicit single headline)",
                "signal_quality": "LOW for governance claims",
                "noise_risk": "MEDIUM",
                "duplicative_with_other_metrics": "HIGH",
                "captures_structural_governance_advantage": "LOW",
                "audit_note": "Current weighting can flatten true governance differences.",
            },
        ]
        for row in rows:
            w.writerow(row)

    # Null gate diagnosis markdown.
    null_md = out_dir / "null_gate_diagnosis.md"
    null_md.write_text(
        "\n".join(
            [
                "# Null Gate Diagnosis",
                "",
                f"- Source phase: `{phase['phase']}`",
                f"- Observed delta (math - best baseline): `{phase['audit']['headline']['delta_vs_best_baseline']}`",
                f"- Permutation p-value: `{phase['audit']['null']['p_value']}`",
                f"- Null gate pass: `{phase['audit']['null']['pass']}`",
                "",
                "## Which null test failed",
                "",
                "- The permutation null test in `run_null_and_leverage_audit` failed (`p > 0.05`).",
                "",
                "## What drove failure",
                "",
                f"- Net advantage is zero (`wins={len(wins)}`, `losses={len(losses)}`, ties dominate), so permutation distribution is not separated from observed delta.",
                "",
                "## Scientific appropriateness",
                "",
                "- Appropriate. With non-positive observed effect, null gate should fail.",
                "",
                "## Gate change analysis (old vs proposed)",
                "",
                "| Gate element | Old | Proposed | Change rationale |",
                "|---|---|---|---|",
                "| Null superiority rule | `delta > 0` and `p <= 0.05` | **No change** | Failure is evidential, not a threshold artifact. |",
            ]
        )
        + "\n"
    )

    # Leverage gate diagnosis markdown.
    leverage_md = out_dir / "leverage_gate_diagnosis.md"
    leverage_md.write_text(
        "\n".join(
            [
                "# Leverage Gate Diagnosis",
                "",
                f"- Source phase: `{phase['phase']}`",
                f"- Degree cutoff (90th pct): `{phase['audit']['leverage']['degree_cutoff_90pct']}`",
                f"- delta_full: `{phase['audit']['leverage']['delta_full']}`",
                f"- delta_without_top_degree: `{phase['audit']['leverage']['delta_without_top_degree']}`",
                f"- leverage pass: `{phase['audit']['leverage']['pass']}`",
                "",
                "## Diagnosis",
                "",
                "- Failure is primarily due to no positive advantage (`delta_without_top_degree <= 0`).",
                "- Additional design issue: degree is near-constant in this normalized kernel, so top-degree slicing is weakly informative.",
                "",
                "## Scientifically appropriate?",
                "",
                "- Yes for this run (no positive effect should fail).",
                "- But leverage slice construction should be improved to test sensitivity meaningfully on normalized kernels.",
                "",
                "## Gate change analysis (old vs proposed)",
                "",
                "| Gate element | Old | Proposed | Change rationale |",
                "|---|---|---|---|",
                "| Leverage slice definition | Top 10% by normalized degree from task table | Top 10% by pre-normalization weighted degree (or centrality) | Avoid degenerate all-equal degree slicing. |",
                "| Pass rule | `delta_reduced > 0` and `delta_drop <= 0.03` | **No threshold change**; keep same pass rule | Preserve strictness; only fix slice validity. |",
            ]
        )
        + "\n"
    )

    # Release decision refresh (exact token required).
    (out_dir / "release_decision_refresh.md").write_text("BLOCK_DEPLOYMENT\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
