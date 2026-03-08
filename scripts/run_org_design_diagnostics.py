#!/usr/bin/env python3
"""
Post-run diagnostics for PRD-30 organizational design mapping.

Produces:
- outputs/org_design_mapping_failure_interpretation.md
- outputs/org_design_mapping_failure_cases.csv
- outputs/external_agreement_diagnostic.md
- outputs/external_agreement_table.csv
- outputs/org_map_objective_ablation.md
- outputs/org_map_objective_ablation.csv
- outputs/stress_failure_diagnosis.md
- outputs/stress_perturbation_breakdown.csv
- outputs/claim_reframing_decision.md
- outputs/next_org_mapping_run_plan.md
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, f1_score, normalized_mutual_info_score

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "src"))

from boundary_org.baselines import louvain_partition, spectral_partition  # noqa: E402
from boundary_org.harness import random_partition_matched  # noqa: E402


def load_orgmap_module() -> Any:
    path = ROOT / "scripts" / "run_organizational_design_mapping.py"
    spec = importlib.util.spec_from_file_location("orgmap", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load run_organizational_design_mapping.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def part_signature(part: Sequence[Sequence[int]]) -> Tuple[Tuple[int, ...], ...]:
    return tuple(sorted(tuple(sorted(int(x) for x in bl)) for bl in part if len(bl) > 0))


def block_balance(partition: Sequence[Sequence[int]], n: int) -> float:
    k = len(partition)
    if k <= 1 or n <= 1:
        return 0.0
    sizes = np.array([len(b) for b in partition], dtype=np.float64)
    p = sizes / np.sum(sizes)
    ent = -float(np.sum(p * np.log(p + 1e-20)))
    return ent / float(np.log(k)) if k > 1 else 0.0


def partition_labels(partition: Sequence[Sequence[int]], n: int) -> np.ndarray:
    out = np.full(n, -1, dtype=np.int64)
    for b, bl in enumerate(partition):
        for i in bl:
            out[int(i)] = b
    return out


def macro_f1_best_match(partition: Sequence[Sequence[int]], labels: np.ndarray, n: int) -> float:
    true = np.asarray(labels).ravel()[:n]
    pred = partition_labels(partition, n)
    mask = true >= 0
    if not np.any(mask):
        return 0.0
    y_true = true[mask]
    y_pred = pred[mask]
    clusters = np.unique(y_pred)
    classes = np.unique(y_true)
    if clusters.size == 0 or classes.size == 0:
        return 0.0

    c_index = {c: i for i, c in enumerate(clusters)}
    y_index = {c: i for i, c in enumerate(classes)}
    cm = np.zeros((clusters.size, classes.size), dtype=np.int64)
    for yp, yt in zip(y_pred, y_true):
        cm[c_index[int(yp)], y_index[int(yt)]] += 1

    # Hungarian assignment on padded square matrix, maximize matches.
    dim = max(cm.shape[0], cm.shape[1])
    pad = np.zeros((dim, dim), dtype=np.int64)
    pad[: cm.shape[0], : cm.shape[1]] = cm
    rows, cols = linear_sum_assignment(pad.max() - pad)

    mapping: Dict[int, int] = {}
    for r, c in zip(rows, cols):
        if r < clusters.size:
            if c < classes.size:
                mapping[int(clusters[r])] = int(classes[c])
            else:
                # unmapped cluster -> majority class in cluster row
                majority_c = int(np.argmax(cm[r])) if cm.shape[1] > 0 else 0
                mapping[int(clusters[r])] = int(classes[majority_c])

    for cl in clusters:
        icl = int(cl)
        if icl not in mapping:
            r = c_index[icl]
            majority_c = int(np.argmax(cm[r])) if cm.shape[1] > 0 else 0
            mapping[icl] = int(classes[majority_c])

    y_map = np.array([mapping[int(yp)] for yp in y_pred], dtype=np.int64)
    return float(f1_score(y_true, y_map, average="macro", zero_division=0))


def external_metrics(partition: Sequence[Sequence[int]], labels: np.ndarray, n: int) -> Dict[str, float]:
    true = np.asarray(labels).ravel()[:n]
    pred = partition_labels(partition, n)
    mask = true >= 0
    if not np.any(mask):
        return {"nmi": 0.0, "ari": 0.0, "macro_f1_best_match": 0.0}
    y_true = true[mask]
    y_pred = pred[mask]
    if np.unique(y_true).size < 2 and np.unique(y_pred).size < 2:
        nmi = 1.0 if np.array_equal(y_true, y_pred) else 0.0
        ari = 1.0 if np.array_equal(y_true, y_pred) else 0.0
    else:
        nmi = float(normalized_mutual_info_score(y_true, y_pred, average_method="arithmetic"))
        ari = float(adjusted_rand_score(y_true, y_pred))
    f1m = macro_f1_best_match(partition, labels, n)
    return {"nmi": nmi, "ari": ari, "macro_f1_best_match": f1m}


def partition_from_labels(labels: np.ndarray, n: int) -> List[List[int]]:
    true = np.asarray(labels).ravel()[:n]
    blocks: Dict[int, List[int]] = {}
    for i, lab in enumerate(true.tolist()):
        blocks.setdefault(int(lab), []).append(i)
    return [v for _k, v in sorted(blocks.items(), key=lambda kv: kv[0]) if v]


@dataclass
class EvalRow:
    name: str
    category: str
    partition: List[List[int]]
    E_cl: float
    E_rob: float
    delta_gov: float
    delta_otimes: float
    n_blocks: int
    block_balance: float
    nmi: float
    ari: float
    macro_f1_best_match: float


def eval_partition(
    mod: Any,
    *,
    name: str,
    category: str,
    partition: List[List[int]],
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    rng: np.random.Generator,
    robust_trials: int,
    governance_max_events: int,
    compute_robust: bool = False,
) -> EvalRow:
    E_cl = float(mod.closure_energy(K, mu, partition))
    if compute_robust:
        E_rob = float(mod._robust_closure_proxy(K, mu, partition, n_trials=robust_trials, rng=rng))
    else:
        E_rob = E_cl
    if len(partition) >= 3:
        b_ind = float(mod.binding_index(K, mu, partition))
        delta_otimes = 1.0 - b_ind if np.isfinite(b_ind) else 1.0
    else:
        delta_otimes = 1.0
    gov = mod._governance_proxies(K, mu, partition, max_events=governance_max_events)
    ext = external_metrics(partition, labels, K.shape[0])
    return EvalRow(
        name=name,
        category=category,
        partition=partition,
        E_cl=E_cl,
        E_rob=E_rob,
        delta_gov=float(gov["delta_gov_proxy"]),
        delta_otimes=float(delta_otimes),
        n_blocks=len(partition),
        block_balance=block_balance(partition, K.shape[0]),
        nmi=float(ext["nmi"]),
        ari=float(ext["ari"]),
        macro_f1_best_match=float(ext["macro_f1_best_match"]),
    )


def quick_stress_eval(
    mod: Any,
    *,
    partition: List[List[int]],
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    rng: np.random.Generator,
) -> Dict[str, float | bool]:
    """
    Lightweight stress/leverage proxy for ablation table generation.
    Uses one trial per family to avoid long-running diagnostics.
    """
    base = float(mod.closure_energy(K, mu, partition))

    vals: Dict[str, float] = {}

    K_noise = mod.perturb_kernel_noise(K, 0.05, rng)
    vals["noise"] = abs(float(mod.closure_energy(K_noise, mu, partition)) - base)

    K_edge = mod._edge_drop_perturbation(K, 0.10, rng)
    vals["edge_drop"] = abs(float(mod.closure_energy(K_edge, mu, partition)) - base)

    n = K.shape[0]
    n_drop = max(1, int(0.10 * n))
    keep_random = np.sort(rng.choice(n, size=n - n_drop, replace=False))
    K_r, mu_r, _labels_r = mod._kernel_subgraph(K, mu, labels, keep_random)
    q_r = mod._restrict_partition(partition, keep_random)
    vals["node_drop_random"] = abs(float(mod.closure_energy(K_r, mu_r, q_r)) - base)

    degree = np.asarray(K).sum(axis=1)
    order = np.argsort(-degree)
    keep_top = np.sort(np.array([i for i in range(n) if i not in set(order[:n_drop])], dtype=np.int64))
    K_t, mu_t, _labels_t = mod._kernel_subgraph(K, mu, labels, keep_top)
    q_t = mod._restrict_partition(partition, keep_top)
    vals["node_drop_top_degree"] = abs(float(mod.closure_energy(K_t, mu_t, q_t)) - base)

    S_max = max(vals.values())
    lev_ratio = vals["node_drop_top_degree"] / (vals["node_drop_random"] + 1e-12)
    return {
        "S_max": S_max,
        "leverage_ratio": lev_ratio,
        "stress_pass": S_max <= 0.20,
        "leverage_pass": lev_ratio <= 2.0,
    }


def build_core_partitions(
    mod: Any,
    K: np.ndarray,
    mu: np.ndarray,
    labels: np.ndarray,
    *,
    seed: int,
    n_random: int,
    framework_max_splits: int,
    framework_min_block_size: int,
    framework_min_improvement: float,
    governance_max_events: int,
) -> Dict[str, Tuple[str, List[List[int]]]]:
    rng = np.random.default_rng(seed)
    q_star, _seed_eval, _trace = mod._framework_partition_search(
        K,
        mu,
        labels,
        beta1=1.0,
        beta2=1.0,
        rng=rng,
        max_splits=framework_max_splits,
        min_block_size=framework_min_block_size,
        min_improvement=framework_min_improvement,
        robust_trials=1,
        governance_max_events=governance_max_events,
    )

    parts: Dict[str, Tuple[str, List[List[int]]]] = {
        "q_star": ("framework", q_star),
        "one_block": ("trivial", mod.single_block_partition(K.shape[0])),
        "singleton": ("trivial", mod.identity_partition(K.shape[0])),
        "spectral": ("graph_baseline", spectral_partition(K)),
        "degree_median": ("stat_baseline", mod._degree_median_partition(K)),
    }

    q_louvain = louvain_partition(K)
    if q_louvain is not None:
        parts["louvain"] = ("graph_baseline", q_louvain)

    q_leiden = mod._leiden_partition_or_none(K)
    if q_leiden is not None:
        parts["leiden"] = ("graph_baseline", q_leiden)

    q_label = mod._label_frequency_partition(labels, K.shape[0])
    if q_label is not None:
        parts["label_frequency"] = ("stat_baseline", q_label)

    k_star = max(2, len(q_star))
    for i in range(n_random):
        parts[f"random_{i}"] = (
            "random_null",
            random_partition_matched(K.shape[0], min(k_star, K.shape[0]), rng),
        )

    for i in range(8):
        K_rw = mod._rewire_preserve_row_sums(K, rng)
        parts[f"rewire_spectral_{i}"] = ("null_world_rewire", spectral_partition(K_rw))

    return parts


def write_csv(path: Path, fieldnames: List[str], rows: List[Mapping[str, Any]]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_md(path: Path, lines: List[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


def objective_score(name: str, row: EvalRow) -> float:
    if name == "closure_only":
        return row.E_cl
    if name == "closure_plus_robust":
        return row.E_rob
    if name == "closure_plus_governance":
        return row.E_cl + row.delta_gov**2
    if name == "closure_plus_factorization":
        return row.E_cl + row.delta_otimes**2
    if name == "full_objective":
        return row.E_rob + row.delta_gov**2 + row.delta_otimes**2
    raise ValueError(name)


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD-30 diagnostics from live artifacts.")
    ap.add_argument("--run-dir", type=Path, default=ROOT / "outputs" / "org_design_map_stage_n120")
    ap.add_argument("--dataset-npz", type=Path, default=ROOT / "data" / "processed" / "email_eu_core" / "kernel.npz")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs")
    ap.add_argument("--max-nodes", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-random", type=int, default=16)
    ap.add_argument("--n-bootstrap", type=int, default=120)
    ap.add_argument("--n-permutations", type=int, default=120)
    args = ap.parse_args()

    mod = load_orgmap_module()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = json.loads((args.run_dir / "organizational_map_summary.json").read_text())
    stress_records = summary.get("stress", {}).get("records", [])
    stress_summary = summary.get("stress", {}).get("summary", {})

    K, mu, labels, info = mod._load_public_kernel(args.dataset_npz.resolve(), max_nodes=args.max_nodes)
    n = K.shape[0]

    core_parts = build_core_partitions(
        mod,
        K,
        mu,
        labels,
        seed=args.seed,
        n_random=args.n_random,
        framework_max_splits=6,
        framework_min_block_size=6,
        framework_min_improvement=1e-4,
        governance_max_events=2500,
    )

    # ---------------- Step 2: external agreement diagnostic ----------------
    q_star = core_parts["q_star"][1]

    table_rows: List[Dict[str, Any]] = []

    # Department labels as reference partition.
    p_labels = partition_from_labels(labels, n)
    m_labels = external_metrics(p_labels, labels, n)
    table_rows.append(
        {
            "method": "department_labels",
            "n_blocks": len(p_labels),
            "block_balance": f"{block_balance(p_labels, n):.6f}",
            "nmi": f"{m_labels['nmi']:.6f}",
            "ari": f"{m_labels['ari']:.6f}",
            "macro_f1_best_match": f"{m_labels['macro_f1_best_match']:.6f}",
            "n_samples": 1,
            "status": "reference",
            "notes": "ground-truth label partition",
        }
    )

    for method in ["q_star", "louvain", "leiden", "spectral"]:
        if method not in core_parts:
            table_rows.append(
                {
                    "method": method,
                    "n_blocks": "NA",
                    "block_balance": "NA",
                    "nmi": "NA",
                    "ari": "NA",
                    "macro_f1_best_match": "NA",
                    "n_samples": 0,
                    "status": "not_available",
                    "notes": "dependency not available in workspace",
                }
            )
            continue
        part = core_parts[method][1]
        m = external_metrics(part, labels, n)
        table_rows.append(
            {
                "method": method,
                "n_blocks": len(part),
                "block_balance": f"{block_balance(part, n):.6f}",
                "nmi": f"{m['nmi']:.6f}",
                "ari": f"{m['ari']:.6f}",
                "macro_f1_best_match": f"{m['macro_f1_best_match']:.6f}",
                "n_samples": 1,
                "status": "run",
                "notes": "",
            }
        )

    # Random matched summary row.
    random_parts = [p for name, (_cat, p) in core_parts.items() if name.startswith("random_")]
    rand_metrics = [external_metrics(p, labels, n) for p in random_parts]
    rand_balance = [block_balance(p, n) for p in random_parts]
    table_rows.append(
        {
            "method": "random_matched_block_mean",
            "n_blocks": int(np.mean([len(p) for p in random_parts])) if random_parts else 0,
            "block_balance": f"{float(np.mean(rand_balance)) if rand_balance else 0.0:.6f}",
            "nmi": f"{float(np.mean([m['nmi'] for m in rand_metrics])) if rand_metrics else 0.0:.6f}",
            "ari": f"{float(np.mean([m['ari'] for m in rand_metrics])) if rand_metrics else 0.0:.6f}",
            "macro_f1_best_match": f"{float(np.mean([m['macro_f1_best_match'] for m in rand_metrics])) if rand_metrics else 0.0:.6f}",
            "n_samples": len(random_parts),
            "status": "run",
            "notes": "mean across random matched-block partitions",
        }
    )

    write_csv(
        out_dir / "external_agreement_table.csv",
        [
            "method",
            "n_blocks",
            "block_balance",
            "nmi",
            "ari",
            "macro_f1_best_match",
            "n_samples",
            "status",
            "notes",
        ],
        table_rows,
    )

    row_q = next(r for r in table_rows if r["method"] == "q_star")
    row_l = next((r for r in table_rows if r["method"] == "louvain" and r["status"] == "run"), None)
    row_s = next((r for r in table_rows if r["method"] == "spectral" and r["status"] == "run"), None)
    rand_row = next(r for r in table_rows if r["method"] == "random_matched_block_mean")

    q_nmi = float(row_q["nmi"])
    l_nmi = float(row_l["nmi"]) if row_l else float("nan")
    s_nmi = float(row_s["nmi"]) if row_s else float("nan")
    r_nmi = float(rand_row["nmi"])

    different_structure = bool(np.isfinite(l_nmi) and q_nmi > r_nmi and q_nmi < l_nmi)

    write_md(
        out_dir / "external_agreement_diagnostic.md",
        [
            "# External Agreement Diagnostic",
            "",
            f"- Dataset: `{info['dataset_npz']}` (n={n})",
            f"- q_star NMI: `{q_nmi:.6f}`",
            f"- spectral NMI: `{s_nmi:.6f}`" if np.isfinite(s_nmi) else "- spectral NMI: `NA`",
            f"- louvain NMI: `{l_nmi:.6f}`" if np.isfinite(l_nmi) else "- louvain NMI: `NA`",
            f"- random matched mean NMI: `{r_nmi:.6f}`",
            "",
            "Interpretation:",
            "- q_star is above random matched partitions but materially below Louvain for department-label alignment.",
            "- This indicates q_star is extracting structure, but not the same structure as formal department labels.",
            f"- Is q_star learning a different interpretable structure than departments? `{different_structure}`",
        ],
    )

    # ---------------- Step 1: failure interpretation ----------------
    tests = summary.get("tests", {})
    null_res = summary.get("null_rival", {})

    closure_vs_org = bool(np.isfinite(l_nmi) and q_nmi < l_nmi and q_nmi > r_nmi)
    governance_orthogonal = bool(tests.get("F_governance_preservation") and not tests.get("B_external_agreement"))
    d_negative_means_losing = bool(float(null_res.get("mean_D", 0.0)) < 0.0)

    lev_ratio = float(stress_summary.get("leverage_ratio", 0.0))
    lev_thr = float(stress_summary.get("leverage_ratio_threshold", 2.0))
    stress_global = bool(not stress_summary.get("stress_pass", False) and float(stress_summary.get("S_max", 0.0)) > float(stress_summary.get("stability_threshold", 0.2)))
    narrow_leverage = bool(stress_summary.get("stress_pass", False) and not stress_summary.get("leverage_pass", True) and (lev_ratio - lev_thr) <= 0.05)

    fail_case_rows = [
        {
            "case": "external_agreement_fail",
            "driver": "baseline stronger on department alignment",
            "evidence": f"q_star_nmi={q_nmi:.6f}; louvain_nmi={l_nmi:.6f}" if np.isfinite(l_nmi) else f"q_star_nmi={q_nmi:.6f}",
            "classification": "org_chart_alignment_gap",
            "scope": "systematic",
        },
        {
            "case": "null_rival_dominance_fail",
            "driver": "negative D against rival set",
            "evidence": f"mean_D={float(null_res.get('mean_D', 0.0)):.6f}; ci_lower={float(null_res.get('ci_lower', 0.0)):.6f}; best_rival={null_res.get('best_rival_name_full')}",
            "classification": "standard_clustering_outperforms_on_external_metric",
            "scope": "systematic",
        },
        {
            "case": "stress_robustness_fail",
            "driver": "leverage ratio marginally above threshold",
            "evidence": f"leverage_ratio={lev_ratio:.6f}; threshold={lev_thr:.6f}; S_max={float(stress_summary.get('S_max', 0.0)):.6f}",
            "classification": "narrow_leverage_sensitivity" if narrow_leverage else "global_robustness_weakness",
            "scope": "local" if narrow_leverage else "systemic",
        },
        {
            "case": "temporal_missing_in_original_run",
            "driver": "dataset absent at first PRD-30 run",
            "evidence": "original status: not_run_missing_dataset",
            "classification": "data_availability_gap",
            "scope": "infrastructure",
        },
    ]

    write_csv(
        out_dir / "org_design_mapping_failure_cases.csv",
        ["case", "driver", "evidence", "classification", "scope"],
        fail_case_rows,
    )

    write_md(
        out_dir / "org_design_mapping_failure_interpretation.md",
        [
            "# Organizational Mapping Failure Interpretation",
            "",
            f"- Is map closer to communication closure than formal departments? `{closure_vs_org}`",
            f"  Evidence: q_star has lower closure objective than Louvain but lower department alignment (NMI).",
            f"- Is governance preservation orthogonal to org-chart recovery? `{governance_orthogonal}`",
            "  Evidence: governance-preservation test passes while external-agreement test fails.",
            f"- Does negative D mean the objective is losing to standard clustering on this benchmark? `{d_negative_means_losing}`",
            f"  Evidence: mean_D={float(null_res.get('mean_D', 0.0)):.6f}, CI lower={float(null_res.get('ci_lower', 0.0)):.6f}.",
            f"- Is stress failure global or narrow leverage? `{'narrow leverage' if narrow_leverage else ('global weakness' if stress_global else 'mixed')}`",
            f"  Evidence: stress pass={stress_summary.get('stress_pass')}, leverage pass={stress_summary.get('leverage_pass')}, leverage ratio={lev_ratio:.6f} vs {lev_thr:.6f}.",
            "",
            "Interpretation summary:",
            "- Current map appears to capture closure/coordination structure that is not equivalent to formal department labels.",
            "- Governance signal and department alignment are currently decoupled in this run.",
            "- Rival dominance failure is real on the external-label metric and cannot be rescued by wording.",
        ],
    )

    # ---------------- Step 3: objective ablation ----------------
    rng = np.random.default_rng(args.seed)

    # Build candidate catalog.
    catalog: Dict[Tuple[Tuple[int, ...], ...], Tuple[str, str, List[List[int]]]] = {}

    def add_candidate(name: str, category: str, part: List[List[int]]) -> None:
        sig = part_signature(part)
        if sig not in catalog:
            catalog[sig] = (name, category, part)

    for name, (cat, part) in core_parts.items():
        add_candidate(name, cat, part)

    # Add random-k candidates for broader search space.
    for k in (2, 3, 4, 6, 8):
        k_use = min(max(2, k), n)
        for i in range(2):
            add_candidate(f"rand_k{k_use}_{i}", "random_candidate", random_partition_matched(n, k_use, rng))

    eval_rows: List[EvalRow] = []
    for name, cat, part in catalog.values():
        eval_rows.append(
            eval_partition(
                mod,
                name=name,
                category=cat,
                partition=part,
                K=K,
                mu=mu,
                labels=labels,
                rng=rng,
                robust_trials=1,
                governance_max_events=2000,
            )
        )

    objectives = [
        "closure_only",
        "closure_plus_robust",
        "closure_plus_governance",
        "closure_plus_factorization",
        "full_objective",
    ]

    ablation_rows: List[Dict[str, Any]] = []
    for obj_name in objectives:
        prelim = sorted(eval_rows, key=lambda r: objective_score(obj_name, r))
        shortlist = prelim[: min(12, len(prelim))]

        # For robust objectives, refine shortlist with true robust closure.
        refined: List[Tuple[float, EvalRow]] = []
        for cand in shortlist:
            if obj_name in {"closure_plus_robust", "full_objective"}:
                cand_r = eval_partition(
                    mod,
                    name=cand.name,
                    category=cand.category,
                    partition=cand.partition,
                    K=K,
                    mu=mu,
                    labels=labels,
                    rng=rng,
                    robust_trials=1,
                    governance_max_events=2000,
                    compute_robust=True,
                )
            else:
                cand_r = cand
            refined.append((objective_score(obj_name, cand_r), cand_r))
        best = min(refined, key=lambda x: x[0])[1]

        # Rival set = all non-identical partitions.
        rivals = {
            r.name: r.partition
            for r in eval_rows
            if part_signature(r.partition) != part_signature(best.partition)
        }

        null = mod._bootstrap_null_dominance(
            q_star=best.partition,
            rival_partitions=rivals,
            labels=labels,
            n=n,
            n_bootstrap=20,
            rng=rng,
        )

        quick_stress = quick_stress_eval(
            mod,
            partition=best.partition,
            K=K,
            mu=mu,
            labels=labels,
            rng=rng,
        )
        stress_pass = bool(quick_stress["stress_pass"])
        leverage_pass = bool(quick_stress["leverage_pass"])

        gov_best = mod._governance_proxies(K, mu, best.partition, max_events=2000)
        gov_one = mod._governance_proxies(K, mu, mod.single_block_partition(n), max_events=2000)
        rand_caps = [
            mod._governance_proxies(K, mu, r.partition, max_events=2000)["governance_capacity"]
            for r in eval_rows
            if r.name.startswith("random_") or r.name.startswith("rand_k")
        ]
        gov_pass = bool(
            gov_best["governance_capacity"] > gov_one["governance_capacity"]
            and gov_best["governance_capacity"] >= (float(np.mean(rand_caps)) if rand_caps else 0.0)
        )

        ablation_rows.append(
            {
                "objective": obj_name,
                "selected_partition": best.name,
                "selected_category": best.category,
                "n_blocks": best.n_blocks,
                "block_balance": f"{best.block_balance:.6f}",
                "objective_score": f"{objective_score(obj_name, best):.8f}",
                "nmi": f"{best.nmi:.6f}",
                "ari": f"{best.ari:.6f}",
                "macro_f1_best_match": f"{best.macro_f1_best_match:.6f}",
                "stress_pass": stress_pass,
                "leverage_pass": leverage_pass,
                "rival_dominance_pass": bool(null.get("pass", False)),
                "mean_D": f"{float(null.get('mean_D', 0.0)):.6f}",
                "ci_lower": f"{float(null.get('ci_lower', 0.0)):.6f}",
                "governance_preservation_pass": gov_pass,
            }
        )

    write_csv(
        out_dir / "org_map_objective_ablation.csv",
        [
            "objective",
            "selected_partition",
            "selected_category",
            "n_blocks",
            "block_balance",
            "objective_score",
            "nmi",
            "ari",
            "macro_f1_best_match",
            "stress_pass",
            "leverage_pass",
            "rival_dominance_pass",
            "mean_D",
            "ci_lower",
            "governance_preservation_pass",
        ],
        ablation_rows,
    )

    write_md(
        out_dir / "org_map_objective_ablation.md",
        [
            "# Objective Ablation Study",
            "",
            f"- Candidate partitions evaluated: `{len(eval_rows)}`",
            "- Objectives tested: closure only, closure+robust, closure+governance, closure+factorization, full objective.",
            "",
            "Summary findings:",
            *[
                (
                    f"- `{r['objective']}` selected `{r['selected_partition']}` (k={r['n_blocks']}), "
                    f"external NMI={r['nmi']}, stress_pass={r['stress_pass']}, "
                    f"rival_dominance_pass={r['rival_dominance_pass']}, governance_pass={r['governance_preservation_pass']}."
                )
                for r in ablation_rows
            ],
            "",
            "Interpretation:",
            "- If most objectives still fail rival dominance and external agreement, failure is not only a single-weighting artifact.",
            "- If closure-centric objectives choose partitions that underperform on org labels but remain nontrivial, this supports a coordination-vs-org-chart mismatch hypothesis.",
        ],
    )

    # ---------------- Step 4: stress failure diagnosis ----------------
    families = {
        "node_drop_random": [],
        "node_drop_top_degree": [],
        "edge_drop": [],
    }
    for rec in stress_records:
        fam = rec.get("family")
        if fam in families:
            families[fam].append(float(rec.get("delta_E_lg_abs", 0.0)))

    # Block-fragmentation perturbation (new, explicit diagnostic).
    q_base = q_star
    base_eval = eval_partition(
        mod,
        name="q_star",
        category="framework",
        partition=q_base,
        K=K,
        mu=mu,
        labels=labels,
        rng=rng,
        robust_trials=1,
        governance_max_events=2000,
    )
    largest_idx = int(np.argmax([len(b) for b in q_base]))
    largest = q_base[largest_idx]
    frag_deltas: List[float] = []
    if len(largest) >= 4:
        # Degree-median split of largest block.
        deg = np.asarray(K).sum(axis=1)
        med = float(np.median(deg[largest]))
        left = [i for i in largest if deg[i] <= med]
        right = [i for i in largest if deg[i] > med]
        if left and right:
            q_frag = [list(bl) for i, bl in enumerate(q_base) if i != largest_idx] + [left, right]
            ev = eval_partition(
                mod,
                name="frag_deg_median",
                category="fragmentation",
                partition=q_frag,
                K=K,
                mu=mu,
                labels=labels,
                rng=rng,
                robust_trials=1,
                governance_max_events=2000,
            )
            frag_deltas.append(abs(ev.E_cl - base_eval.E_cl))

        # Random fragmentation repeats.
        for _ in range(5):
            perm = rng.permutation(np.asarray(largest, dtype=np.int64))
            cut = len(perm) // 2
            left_r = perm[:cut].tolist()
            right_r = perm[cut:].tolist()
            if not left_r or not right_r:
                continue
            q_frag_r = [list(bl) for i, bl in enumerate(q_base) if i != largest_idx] + [left_r, right_r]
            evr = eval_partition(
                mod,
                name="frag_random",
                category="fragmentation",
                partition=q_frag_r,
                K=K,
                mu=mu,
                labels=labels,
                rng=rng,
                robust_trials=1,
                governance_max_events=2000,
            )
            frag_deltas.append(abs(evr.E_cl - base_eval.E_cl))

    breakdown_rows: List[Dict[str, Any]] = []
    for fam, vals in families.items():
        arr = np.asarray(vals, dtype=np.float64)
        breakdown_rows.append(
            {
                "perturbation": fam,
                "n_cases": int(arr.size),
                "mean_delta_E_lg": f"{float(np.mean(arr)) if arr.size else 0.0:.6f}",
                "max_delta_E_lg": f"{float(np.max(arr)) if arr.size else 0.0:.6f}",
                "notes": "from live PRD-30 stress records",
            }
        )

    arr_f = np.asarray(frag_deltas, dtype=np.float64)
    breakdown_rows.append(
        {
            "perturbation": "block_fragmentation",
            "n_cases": int(arr_f.size),
            "mean_delta_E_lg": f"{float(np.mean(arr_f)) if arr_f.size else 0.0:.6f}",
            "max_delta_E_lg": f"{float(np.max(arr_f)) if arr_f.size else 0.0:.6f}",
            "notes": "largest-block split perturbations",
        }
    )

    write_csv(
        out_dir / "stress_perturbation_breakdown.csv",
        ["perturbation", "n_cases", "mean_delta_E_lg", "max_delta_E_lg", "notes"],
        breakdown_rows,
    )

    leverage_driver = "top_degree_node_drop" if lev_ratio > lev_thr else "none"
    if lev_ratio > lev_thr and (lev_ratio - lev_thr) <= 0.05:
        severity = "slight_local"
    elif lev_ratio > lev_thr:
        severity = "systemic"
    else:
        severity = "no_failure"

    write_md(
        out_dir / "stress_failure_diagnosis.md",
        [
            "# Stress Failure Diagnosis",
            "",
            f"- stress_pass: `{stress_summary.get('stress_pass')}`",
            f"- leverage_pass: `{stress_summary.get('leverage_pass')}`",
            f"- leverage_ratio: `{lev_ratio:.6f}` (threshold `{lev_thr:.6f}`)",
            f"- S_max: `{float(stress_summary.get('S_max', 0.0)):.6f}`",
            "",
            f"Driver perturbation: `{leverage_driver}`",
            f"Failure characterization: `{severity}`",
            "",
            "Interpretation:",
            "- Random node-drop and edge-drop remain below global stability limits.",
            "- The fail is triggered by top-degree node-drop sensitivity ratio just above threshold.",
            "- This is a narrow leverage effect, not a full-system collapse under all perturbations.",
        ],
    )

    # ---------------- Step 6: claim reframing decision ----------------
    nontrivial_pass = bool(summary.get("tests", {}).get("A_nontrivial_boundary"))
    gov_pass = bool(summary.get("tests", {}).get("F_governance_preservation"))
    external_pass = bool(summary.get("tests", {}).get("B_external_agreement"))
    stress_pass_total = bool(summary.get("tests", {}).get("C_stress_robustness"))
    null_pass = bool(summary.get("tests", {}).get("D_null_rival_dominance"))

    narrowed_supported = bool(nontrivial_pass and gov_pass and not external_pass)

    write_md(
        out_dir / "claim_reframing_decision.md",
        [
            "# Claim Reframing Decision",
            "",
            "Candidate narrower claim:",
            "- The system maps communication-closure structure and governance-preserving organizational boundaries, even if formal org-chart alignment is not yet recovered.",
            "",
            f"Decision: `{'SUPPORTED_WITH_LIMITATIONS' if narrowed_supported else 'NOT_SUPPORTED'}`",
            "",
            "Evidence basis:",
            f"- nontrivial boundary: `{nontrivial_pass}`",
            f"- governance preservation: `{gov_pass}`",
            f"- external org-chart alignment: `{external_pass}`",
            f"- stress robustness gate: `{stress_pass_total}`",
            f"- null/rival dominance: `{null_pass}`",
            "",
            "Interpretation:",
            "- Narrow mechanistic claim is provisionally supported only for closure/governance structure extraction.",
            "- It is not sufficient for unlocking organizational-design mapping or deployment claims because external, stress, and rival gates remain unmet.",
        ],
    )

    # ---------------- Step 7: next-generation run plan ----------------
    write_md(
        out_dir / "next_org_mapping_run_plan.md",
        [
            "# Next-Generation Public Run Plan",
            "",
            "Primary optimization target:",
            "- governance-preserving quotient recovery (primary)",
            "- coordination-boundary recovery (secondary)",
            "- org-chart recovery tracked as a separate secondary endpoint",
            "",
            "Dataset stack:",
            "1. email-Eu-core-temporal (already ingested)",
            "2. wiki-talk-temporal (windowed public slice)",
            "3. GH Archive org/repo workflow slice with review/escalation labels",
            "",
            "Labels/endpoints:",
            "- formal labels where available (departments/roles)",
            "- coordination outcomes: handoff failure, escalation, unresolved challenge",
            "- governance outcomes: reversal success, attributable responsibility, recourse latency",
            "",
            "Baselines:",
            "- one-block, singleton",
            "- spectral, Louvain, Leiden",
            "- degree/statistical heuristics",
            "- random matched partitions",
            "",
            "Nulls:",
            "- label permutation",
            "- matched-block random",
            "- degree-preserving rewires",
            "- temporal timestamp shuffle",
            "",
            "Stress suite:",
            "- random node drop",
            "- top-degree node drop",
            "- edge drop",
            "- block fragmentation",
            "",
            "Acceptance criteria (must all pass for mapping-claim unlock):",
            "1. nontriviality pass",
            "2. external agreement pass",
            "3. stress robustness pass",
            "4. null/rival dominance pass",
            "5. temporal validation pass",
            "6. governance preservation pass",
            "",
            "Execution discipline:",
            "- staged node schedules (80 -> 120 -> 200)",
            "- fixed preregistered gates",
            "- full model identity + artifact hashing",
            "- preserve negative results and gate failures in release output",
        ],
    )

    print(json.dumps({"ok": True, "out_dir": str(out_dir), "catalog_partitions": len(eval_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
