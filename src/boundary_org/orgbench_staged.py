"""
Staged OrgBench pipeline (PRD I/II/III/VIII style) with SQLite + JSON artifacts.

Design goal:
- Avoid monolithic long-running benchmarks on local machines.
- Run in explicit stages with resumable state.
- Keep outputs machine-readable for later export/publication gates.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from .baselines import spectral_partition
from .greedy import greedy_coarse_graining


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  node_id INTEGER NOT NULL,
  prompt TEXT NOT NULL,
  gold_label INTEGER NOT NULL,
  split TEXT NOT NULL,
  degree REAL NOT NULL,
  meta_json TEXT
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  arm TEXT NOT NULL,
  model_provider TEXT NOT NULL,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  dataset_version TEXT NOT NULL,
  seed INTEGER NOT NULL,
  config_hash TEXT NOT NULL,
  prompt_hash TEXT,
  rag_hash TEXT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
  run_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  pred_label INTEGER NOT NULL,
  confidence REAL NOT NULL,
  tokens_in INTEGER NOT NULL,
  tokens_out INTEGER NOT NULL,
  latency_ms REAL NOT NULL,
  cost_estimate REAL NOT NULL,
  context_json TEXT,
  PRIMARY KEY (run_id, task_id)
);

CREATE TABLE IF NOT EXISTS metrics (
  run_id TEXT NOT NULL,
  split TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  ci_low REAL,
  ci_high REAL,
  n INTEGER NOT NULL,
  PRIMARY KEY (run_id, split, metric_name)
);

CREATE TABLE IF NOT EXISTS audits (
  audit_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  headline_json TEXT NOT NULL,
  null_json TEXT NOT NULL,
  leverage_json TEXT NOT NULL,
  pass INTEGER NOT NULL
);
"""


ARMS = (
    "plain_llm",
    "plain_llm_rag",
    "math_governed",
    "sham_complexity",
    "simple_graph",
)

BACKENDS = (
    "local_heuristic",
    "openai",
    "local_ollama",
    "anthropic",
)


@dataclass(frozen=True)
class DatasetBundle:
    K: np.ndarray
    labels: np.ndarray
    degrees: np.ndarray
    dataset_version: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def connect_db(db_path: Path) -> sqlite3.Connection:
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def set_metadata(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO metadata(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def get_metadata(conn: sqlite3.Connection, key: str, default: Optional[str] = None) -> Optional[str]:
    row = conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return str(row[0])


def _row_stochastic(K: np.ndarray) -> np.ndarray:
    K = np.asarray(K, dtype=np.float64)
    row_sums = K.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    return K / row_sums


def load_dataset(npz_path: Path, *, max_nodes: int = 120) -> DatasetBundle:
    data = np.load(npz_path, allow_pickle=False)
    if "K" not in data or "labels" not in data:
        raise ValueError(f"{npz_path} must contain K and labels arrays")
    K = np.asarray(data["K"], dtype=np.float64)
    labels = np.asarray(data["labels"], dtype=np.int64).ravel()
    if K.shape[0] != labels.shape[0]:
        raise ValueError("K/labels shape mismatch")
    n = K.shape[0]
    degree = np.asarray(K).sum(axis=1)
    if 0 < max_nodes < n:
        order = np.argsort(-degree)
        keep = np.sort(order[:max_nodes])
        K = K[np.ix_(keep, keep)]
        labels = labels[keep]
        degree = degree[keep]
    K = _row_stochastic(K)
    dataset_version = f"{npz_path.name}:n={K.shape[0]}"
    return DatasetBundle(K=K, labels=labels, degrees=degree, dataset_version=dataset_version)


def _stratified_split(labels: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Return split labels array with values in {"train","val","test"}.
    Deterministic per seed while retaining class coverage where possible.
    """
    n = labels.shape[0]
    split = np.array(["train"] * n, dtype=object)
    classes = np.unique(labels)
    for c in classes:
        idx = np.where(labels == c)[0]
        rng.shuffle(idx)
        m = len(idx)
        if m <= 2:
            # keep tiny classes in train to avoid empty train label priors
            continue
        n_train = max(1, int(round(0.6 * m)))
        n_val = max(1, int(round(0.2 * m)))
        if n_train + n_val >= m:
            n_val = max(1, m - n_train - 1)
        split[idx[n_train:n_train + n_val]] = "val"
        split[idx[n_train + n_val:]] = "test"
    # Ensure at least one test task exists.
    if np.sum(split == "test") == 0 and n > 0:
        split[int(rng.integers(0, n))] = "test"
    return split


def lock_claim_scope(
    workspace: Path,
    *,
    metric: str = "accuracy",
    min_delta_vs_plain: float = 0.02,
    p_value_max: float = 0.05,
    leverage_drop_max: float = 0.03,
) -> Dict[str, Any]:
    """
    Freeze preregistered claims and success gates for staged Arm A/B/C benchmarks.
    """
    ensure_dir(workspace / "json")
    prereg = {
        "created_at": utc_now(),
        "scope": "benchmark-in-progress",
        "arms": {
            "A": "plain_llm",
            "B": "math_governed",
            "C": "sham_complexity",
            "A_plus_rag": "plain_llm_rag",
            "simple_graph": "simple_graph",
        },
        "primary_metric": metric,
        "hypotheses": [
            "H1: math_governed > plain_llm on out-of-sample public tasks",
            "H2: math_governed > plain_llm_rag on same split and budget",
            "H3: math_governed > sham_complexity on same split and budget",
        ],
        "falsification": [
            "Any required arm missing on same split -> no public superiority claim",
            "Primary metric delta <= 0 vs any required baseline -> fail claim",
            "Permutation null p-value > threshold -> fail claim",
            "Top-degree leverage drop above threshold -> fail claim",
        ],
        "gates": {
            "min_delta_vs_plain": min_delta_vs_plain,
            "p_value_max": p_value_max,
            "leverage_drop_max": leverage_drop_max,
        },
        "mandatory_outputs": [
            "task metrics with uncertainty",
            "null-world audit",
            "outlier/leverage audit",
            "model identity log",
            "config hashes",
            "dataset provenance",
            "wrong-but-impressive section",
        ],
    }
    out = workspace / "json" / "preregistered_claims.json"
    out.write_text(json.dumps(prereg, indent=2))
    return prereg


def run_storage_review(workspace: Path, dataset_npz: Path, *, max_nodes: int) -> Dict[str, Any]:
    """
    Lightweight storage planning report to avoid oversized runs on local hardware.
    """
    ensure_dir(workspace / "json")
    usage = shutil.disk_usage(workspace)
    dataset_bytes = dataset_npz.stat().st_size if dataset_npz.exists() else 0
    # Rough estimates for staged benchmark artifacts.
    est_tasks = max_nodes
    est_predictions = est_tasks * len(ARMS)
    est_sqlite_bytes = int(est_predictions * 600) + int(est_tasks * 300)
    est_json_bytes = int(est_predictions * 450) + int(est_tasks * 220)
    review = {
        "created_at": utc_now(),
        "workspace": str(workspace),
        "dataset_npz": str(dataset_npz),
        "dataset_size_mb": round(dataset_bytes / (1024 * 1024), 3),
        "disk_total_gb": round(usage.total / (1024**3), 3),
        "disk_free_gb": round(usage.free / (1024**3), 3),
        "max_nodes_requested": max_nodes,
        "estimated_tasks": est_tasks,
        "estimated_predictions": est_predictions,
        "estimated_sqlite_mb": round(est_sqlite_bytes / (1024 * 1024), 3),
        "estimated_json_mb": round(est_json_bytes / (1024 * 1024), 3),
        "recommendation": "stage-by-stage execution; keep max_nodes <= 150 on laptop unless free disk > 5 GB",
    }
    (workspace / "json" / "storage_review.json").write_text(json.dumps(review, indent=2))
    return review


def build_public_taskset(
    db_path: Path,
    dataset_npz: Path,
    *,
    max_nodes: int = 120,
    seed: int = 42,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Build a public task set from a labeled graph (e.g., email-Eu-core).
    Tasks are lightweight classification prompts tied to node-level ground truth.
    """
    bundle = load_dataset(dataset_npz, max_nodes=max_nodes)
    rng = np.random.default_rng(seed)
    splits = _stratified_split(bundle.labels, rng)
    conn = connect_db(db_path)
    conn.execute("DELETE FROM tasks")
    rows: List[Tuple[str, int, str, int, str, float, str]] = []
    for i in range(bundle.K.shape[0]):
        prompt = (
            f"Task: predict the organizational label for actor {i}. "
            "Use retrieved context and return an integer label."
        )
        task_id = f"task_{i:05d}"
        meta = {"source_node": int(i), "dataset": bundle.dataset_version}
        rows.append(
            (
                task_id,
                int(i),
                prompt,
                int(bundle.labels[i]),
                str(splits[i]),
                float(bundle.degrees[i]),
                json.dumps(meta),
            )
        )
    conn.executemany(
        """
        INSERT INTO tasks(task_id,node_id,prompt,gold_label,split,degree,meta_json)
        VALUES(?,?,?,?,?,?,?)
        """,
        rows,
    )
    set_metadata(conn, "dataset_npz", str(dataset_npz))
    set_metadata(conn, "dataset_version", bundle.dataset_version)
    set_metadata(conn, "max_nodes", str(bundle.K.shape[0]))
    set_metadata(conn, "taskset_seed", str(seed))
    conn.commit()
    conn.close()

    if workspace is not None:
        ensure_dir(workspace / "json")
        path = workspace / "json" / "taskset.jsonl"
        with path.open("w") as f:
            for task_id, node_id, prompt, gold, split, degree, meta in rows:
                f.write(
                    json.dumps(
                        {
                            "task_id": task_id,
                            "node_id": node_id,
                            "prompt": prompt,
                            "gold_label": gold,
                            "split": split,
                            "degree": degree,
                            "meta": json.loads(meta),
                        }
                    )
                    + "\n"
                )

    return {
        "dataset_version": bundle.dataset_version,
        "n_tasks": len(rows),
        "split_counts": {
            "train": int(np.sum(splits == "train")),
            "val": int(np.sum(splits == "val")),
            "test": int(np.sum(splits == "test")),
        },
    }


def _tasks_for_split(conn: sqlite3.Connection, split: str) -> List[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        "SELECT task_id,node_id,prompt,gold_label,split,degree FROM tasks WHERE split = ? ORDER BY task_id",
        (split,),
    ).fetchall()


def _train_priors(tasks_train: Sequence[sqlite3.Row]) -> Dict[int, float]:
    counts: Dict[int, float] = {}
    for row in tasks_train:
        label = int(row["gold_label"])
        counts[label] = counts.get(label, 0.0) + 1.0
    # Laplace-ish smoothing keeps all labels possible.
    for label in list(counts):
        counts[label] += 1.0
    return counts


def _neighbor_votes(
    K: np.ndarray,
    node_id: int,
    train_label_by_node: Dict[int, int],
    *,
    top_k: Optional[int],
) -> Tuple[Dict[int, float], List[int]]:
    row = np.asarray(K[node_id], dtype=np.float64)
    order = np.argsort(-row)
    votes: Dict[int, float] = {}
    used: List[int] = []
    for j in order:
        if j == node_id:
            continue
        if j not in train_label_by_node:
            continue
        w = float(row[j])
        if w <= 0:
            continue
        lbl = int(train_label_by_node[j])
        votes[lbl] = votes.get(lbl, 0.0) + w
        used.append(int(j))
        if top_k is not None and len(used) >= top_k:
            break
    return votes, used


def _block_map(partition: Sequence[Sequence[int]], n: int) -> np.ndarray:
    out = np.full(n, -1, dtype=np.int64)
    for b, block in enumerate(partition):
        for i in block:
            out[int(i)] = b
    return out


def _scores_to_pred(scores: Dict[int, float]) -> Tuple[int, float]:
    labels = sorted(scores)
    vec = np.array([scores[l] for l in labels], dtype=np.float64)
    vec = vec - np.max(vec)
    exp = np.exp(vec)
    probs = exp / np.sum(exp)
    idx = int(np.argmax(probs))
    return int(labels[idx]), float(probs[idx])


def _extract_label_from_text(text: str, allowed_labels: Sequence[int], fallback_label: int) -> int:
    if not text:
        return int(fallback_label)
    allowed = set(int(x) for x in allowed_labels)
    # Prefer explicit "label: <int>" style matches.
    m = re.search(r"label\s*[:=]\s*(-?\d+)", text, flags=re.IGNORECASE)
    if m:
        v = int(m.group(1))
        if v in allowed:
            return v
    # Fallback to first integer mention.
    m = re.search(r"-?\d+", text)
    if m:
        v = int(m.group(0))
        if v in allowed:
            return v
    return int(fallback_label)


def _score_summary(scores: Dict[int, float], top_n: int = 5) -> List[Tuple[int, float]]:
    return sorted(((int(k), float(v)) for k, v in scores.items()), key=lambda x: x[1], reverse=True)[:top_n]


def _build_llm_prompt(
    *,
    row_prompt: str,
    arm: str,
    allowed_labels: Sequence[int],
    scores: Dict[int, float],
    context: Dict[str, Any],
) -> str:
    label_text = ", ".join(str(int(x)) for x in sorted(set(int(a) for a in allowed_labels)))
    summary = _score_summary(scores, top_n=min(5, len(scores)))
    summary_text = ", ".join(f"{lbl}:{val:.4f}" for lbl, val in summary)
    strategy = str(context.get("strategy", "none"))
    return (
        "You are a classification assistant.\n"
        f"Allowed labels: [{label_text}]\n"
        f"Arm: {arm}\n"
        f"Strategy: {strategy}\n"
        f"Heuristic score summary (higher is better): {summary_text}\n"
        f"Task: {row_prompt}\n\n"
        "Return exactly one line in the format: label: <integer>\n"
    )


def _predict_openai(
    *,
    prompt: str,
    allowed_labels: Sequence[int],
    fallback_label: int,
    model_name: str,
    temperature: float,
    openai_base_url: Optional[str],
    openai_api_key_env: str,
) -> Tuple[int, float, Dict[str, Any]]:
    api_key = os.environ.get(openai_api_key_env, "").strip()
    if not api_key:
        raise RuntimeError(f"Missing API key in env var: {openai_api_key_env}")
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("openai package is required for backend=openai. Install with: pip install openai") from e

    kwargs: Dict[str, Any] = {"api_key": api_key}
    if openai_base_url:
        kwargs["base_url"] = openai_base_url
    client = OpenAI(**kwargs)
    t0 = time.perf_counter()
    resp = client.responses.create(
        model=model_name,
        temperature=float(temperature),
        input=prompt,
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0

    text = getattr(resp, "output_text", "") or ""
    pred = _extract_label_from_text(text, allowed_labels, fallback_label)
    usage = getattr(resp, "usage", None)
    in_tok = 0
    out_tok = 0
    if usage is not None:
        in_tok = int(getattr(usage, "input_tokens", 0) or 0)
        out_tok = int(getattr(usage, "output_tokens", 0) or 0)
    if in_tok <= 0:
        in_tok = max(1, len(prompt.split()))
    if out_tok <= 0:
        out_tok = max(1, len(text.split()))
    meta = {
        "backend": "openai",
        "raw_response": text,
        "latency_ms": latency_ms,
        "tokens_in": in_tok,
        "tokens_out": out_tok,
    }
    # Confidence proxy for text-only response backends.
    return int(pred), 0.6, meta


def _predict_anthropic(
    *,
    prompt: str,
    allowed_labels: Sequence[int],
    fallback_label: int,
    model_name: str,
    temperature: float,
    anthropic_base_url: Optional[str],
    anthropic_api_key_env: str,
    anthropic_version: str,
) -> Tuple[int, float, Dict[str, Any]]:
    api_key = os.environ.get(anthropic_api_key_env, "").strip()
    if not api_key:
        raise RuntimeError(f"Missing API key in env var: {anthropic_api_key_env}")
    url = (anthropic_base_url or "https://api.anthropic.com/v1/messages").strip()
    payload = {
        "model": model_name,
        "temperature": float(temperature),
        "max_tokens": 64,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        url=url,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": anthropic_version,
        },
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"anthropic API HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"anthropic API URL error: {e.reason}") from e
    latency_ms = (time.perf_counter() - t0) * 1000.0

    parsed = json.loads(raw)
    content = parsed.get("content", [])
    text_chunks: List[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_chunks.append(str(item.get("text", "")))
    text = "\n".join(c for c in text_chunks if c).strip()
    pred = _extract_label_from_text(text, allowed_labels, fallback_label)

    usage = parsed.get("usage", {}) if isinstance(parsed.get("usage"), dict) else {}
    in_tok = int(usage.get("input_tokens", 0) or 0)
    out_tok = int(usage.get("output_tokens", 0) or 0)
    if in_tok <= 0:
        in_tok = max(1, len(prompt.split()))
    if out_tok <= 0:
        out_tok = max(1, len(text.split()))
    meta = {
        "backend": "anthropic",
        "raw_response": text,
        "latency_ms": latency_ms,
        "tokens_in": in_tok,
        "tokens_out": out_tok,
        "endpoint": url,
        "anthropic_version": anthropic_version,
    }
    return int(pred), 0.6, meta


def _predict_local_ollama(
    *,
    prompt: str,
    allowed_labels: Sequence[int],
    fallback_label: int,
    model_name: str,
) -> Tuple[int, float, Dict[str, Any]]:
    cmd = ["ollama", "run", model_name, prompt]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"ollama run failed: {err}")
    text = (proc.stdout or "").strip()
    pred = _extract_label_from_text(text, allowed_labels, fallback_label)
    in_tok = max(1, len(prompt.split()))
    out_tok = max(1, len(text.split()))
    meta = {
        "backend": "local_ollama",
        "raw_response": text,
        "latency_ms": latency_ms,
        "tokens_in": in_tok,
        "tokens_out": out_tok,
    }
    return int(pred), 0.6, meta


def _bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_name: str,
    *,
    n_bootstrap: int,
    seed: int,
) -> Tuple[float, float]:
    if len(y_true) <= 1:
        v = _metric(metric_name, y_true, y_pred)
        return float(v), float(v)
    rng = np.random.default_rng(seed)
    vals: List[float] = []
    n = len(y_true)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        vals.append(_metric(metric_name, y_true[idx], y_pred[idx]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def _metric(metric_name: str, y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if metric_name == "accuracy":
        return float(accuracy_score(y_true, y_pred))
    if metric_name == "macro_f1":
        return float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    if metric_name == "balanced_accuracy":
        return float(balanced_accuracy_score(y_true, y_pred))
    raise ValueError(f"Unknown metric: {metric_name}")


def run_arm(
    db_path: Path,
    dataset_npz: Path,
    *,
    arm: str,
    backend: str = "local_heuristic",
    split: str = "test",
    max_nodes: int = 120,
    seed: int = 42,
    top_k_rag: int = 8,
    max_greedy_n: int = 40,
    model_provider: Optional[str] = None,
    model_name: Optional[str] = None,
    model_version: str = "1.0",
    temperature: float = 0.0,
    openai_base_url: Optional[str] = None,
    openai_api_key_env: str = "OPENAI_API_KEY",
    anthropic_base_url: Optional[str] = None,
    anthropic_api_key_env: str = "ANTHROPIC_API_KEY",
    anthropic_version: str = "2023-06-01",
    strict_backend: bool = True,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"Unknown arm: {arm}")
    if backend not in BACKENDS:
        raise ValueError(f"Unknown backend: {backend}")
    bundle = load_dataset(dataset_npz, max_nodes=max_nodes)
    mu = np.ones(bundle.K.shape[0], dtype=np.float64) / bundle.K.shape[0]
    conn = connect_db(db_path)
    conn.row_factory = sqlite3.Row
    tasks_train = _tasks_for_split(conn, "train")
    tasks_eval = _tasks_for_split(conn, split)
    if not tasks_train or not tasks_eval:
        raise ValueError("Taskset missing required train/eval splits. Run build-taskset stage first.")

    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{arm}"
    if model_provider is None:
        model_provider = {
            "local_heuristic": "local-simulated",
            "openai": "openai",
            "local_ollama": "local-ollama",
            "anthropic": "anthropic",
        }[backend]
    if model_name is None:
        model_name = {
            "local_heuristic": "local_prompt_model_v1",
            "openai": "gpt-4.1-mini",
            "local_ollama": "llama3.1:8b",
            "anthropic": "claude-opus-4-1-20250805",
        }[backend]
    cfg_text = (
        f"arm={arm}|backend={backend}|split={split}|seed={seed}|k={top_k_rag}|"
        f"dataset={bundle.dataset_version}|model_provider={model_provider}|model_name={model_name}|"
        f"model_version={model_version}|temperature={temperature}"
    )
    config_hash = sha16(cfg_text)
    prompt_hash = sha16("node_label_classification_prompt_v1")
    rag_hash = sha16(f"topk={top_k_rag}")
    started = utc_now()

    conn.execute(
        """
        INSERT INTO runs(run_id,arm,model_provider,model_name,model_version,dataset_version,seed,config_hash,prompt_hash,rag_hash,started_at,status,notes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            run_id,
            arm,
            model_provider,
            model_name,
            model_version,
            bundle.dataset_version,
            seed,
            config_hash,
            prompt_hash,
            rag_hash,
            started,
            "running",
            "",
        ),
    )
    conn.commit()

    train_label_by_node = {int(r["node_id"]): int(r["gold_label"]) for r in tasks_train}
    priors = _train_priors(tasks_train)
    label_set = sorted(set(int(r["gold_label"]) for r in tasks_train))

    # Precompute only what each arm actually needs to keep stage runtime bounded.
    q_non_trivial = 0
    q_map: Optional[np.ndarray] = None
    boundary_mode = "none"
    if arm == "math_governed":
        if bundle.K.shape[0] <= max_greedy_n:
            q_star, _, _ = greedy_coarse_graining(bundle.K, mu)
            q_map = _block_map(q_star, bundle.K.shape[0])
            q_non_trivial = int(len(q_star) >= 2)
            boundary_mode = "greedy_q_star"
        else:
            # Safety fallback for laptop-scale staged runs: use fast spectral boundary proxy.
            q_star = spectral_partition(bundle.K)
            q_map = _block_map(q_star, bundle.K.shape[0])
            q_non_trivial = int(len(q_star) >= 2)
            boundary_mode = "spectral_fallback_large_n"

    spectral_map: Optional[np.ndarray] = None
    if arm == "sham_complexity":
        spectral = spectral_partition(bundle.K)
        spectral_map = _block_map(spectral, bundle.K.shape[0])

    pred_rows: List[Tuple[str, str, int, float, int, int, float, float, str]] = []
    y_true: List[int] = []
    y_pred: List[int] = []

    for row in tasks_eval:
        node_id = int(row["node_id"])
        gold = int(row["gold_label"])
        scores: Dict[int, float] = {lbl: float(priors.get(lbl, 1.0)) for lbl in label_set}
        context: Dict[str, Any] = {"arm": arm}

        rag_votes, rag_nodes = _neighbor_votes(bundle.K, node_id, train_label_by_node, top_k=top_k_rag)
        graph_votes, graph_nodes = _neighbor_votes(bundle.K, node_id, train_label_by_node, top_k=None)

        if arm == "plain_llm":
            context["strategy"] = "prior_only"
        elif arm == "plain_llm_rag":
            for lbl, w in rag_votes.items():
                scores[lbl] = scores.get(lbl, 0.0) + 2.0 * w
            context["rag_nodes"] = rag_nodes
            context["strategy"] = "prior_plus_topk_rag"
        elif arm == "simple_graph":
            for lbl, w in graph_votes.items():
                scores[lbl] = scores.get(lbl, 0.0) + 1.5 * w
            context["graph_nodes"] = graph_nodes[:16]
            context["strategy"] = "weighted_neighbor_vote"
        elif arm == "sham_complexity":
            # Extra orchestration, intentionally non-math-governed.
            assert spectral_map is not None
            block = int(spectral_map[node_id])
            cluster_nodes = [n for n, lbl in train_label_by_node.items() if int(spectral_map[n]) == block]
            cluster_votes: Dict[int, float] = {}
            for n in cluster_nodes[:12]:
                lbl = int(train_label_by_node[n])
                cluster_votes[lbl] = cluster_votes.get(lbl, 0.0) + 1.0
            for lbl, w in rag_votes.items():
                scores[lbl] = scores.get(lbl, 0.0) + 1.0 * w
            for lbl, w in cluster_votes.items():
                scores[lbl] = scores.get(lbl, 0.0) + 0.4 * w
            context["rag_nodes"] = rag_nodes
            context["cluster_block"] = block
            context["cluster_nodes"] = cluster_nodes[:12]
            context["strategy"] = "extra_orchestration_no_boundary_math"
        elif arm == "math_governed":
            # Governance-oriented context restricted by learned boundary block.
            assert q_map is not None
            block = int(q_map[node_id])
            same_block = [n for n, lbl in train_label_by_node.items() if int(q_map[n]) == block]
            block_votes: Dict[int, float] = {}
            for n in same_block:
                w = float(bundle.K[node_id, n])
                if w <= 0:
                    continue
                lbl = int(train_label_by_node[n])
                block_votes[lbl] = block_votes.get(lbl, 0.0) + w
            for lbl, w in rag_votes.items():
                scores[lbl] = scores.get(lbl, 0.0) + 0.8 * w
            for lbl, w in block_votes.items():
                scores[lbl] = scores.get(lbl, 0.0) + 2.2 * w
            context["rag_nodes"] = rag_nodes
            context["boundary_block"] = block
            context["q_non_trivial"] = q_non_trivial
            context["boundary_mode"] = boundary_mode
            context["strategy"] = "boundary_block_weighted_vote"
        else:
            raise ValueError(arm)

        fallback_pred, fallback_conf = _scores_to_pred(scores)
        pred_label = fallback_pred
        conf = fallback_conf
        pred_meta: Dict[str, Any] = {"backend": backend, "fallback_used": False}
        if backend == "local_heuristic":
            pass
        else:
            llm_prompt = _build_llm_prompt(
                row_prompt=str(row["prompt"]),
                arm=arm,
                allowed_labels=label_set,
                scores=scores,
                context=context,
            )
            try:
                if backend == "openai":
                    pred_label, conf, pred_meta = _predict_openai(
                        prompt=llm_prompt,
                        allowed_labels=label_set,
                        fallback_label=fallback_pred,
                        model_name=model_name,
                        temperature=temperature,
                        openai_base_url=openai_base_url,
                        openai_api_key_env=openai_api_key_env,
                    )
                elif backend == "local_ollama":
                    pred_label, conf, pred_meta = _predict_local_ollama(
                        prompt=llm_prompt,
                        allowed_labels=label_set,
                        fallback_label=fallback_pred,
                        model_name=model_name,
                    )
                elif backend == "anthropic":
                    pred_label, conf, pred_meta = _predict_anthropic(
                        prompt=llm_prompt,
                        allowed_labels=label_set,
                        fallback_label=fallback_pred,
                        model_name=model_name,
                        temperature=temperature,
                        anthropic_base_url=anthropic_base_url,
                        anthropic_api_key_env=anthropic_api_key_env,
                        anthropic_version=anthropic_version,
                    )
                else:
                    raise ValueError(backend)
            except Exception as e:
                if strict_backend:
                    raise
                pred_label = fallback_pred
                conf = fallback_conf
                pred_meta = {
                    "backend": backend,
                    "fallback_used": True,
                    "error": str(e),
                }

        # Telemetry: backend usage if available, else deterministic estimates.
        default_tokens_in = len(str(row["prompt"]).split()) + len(context.get("rag_nodes", [])) + len(context.get("cluster_nodes", []))
        tokens_in = int(pred_meta.get("tokens_in", default_tokens_in))
        tokens_out = int(pred_meta.get("tokens_out", 4))
        latency_ms = float(pred_meta.get("latency_ms", 1.0 + 0.2 * (default_tokens_in / 10.0)))
        cost_est = (tokens_in + tokens_out) * 1e-6
        context["backend"] = backend
        context["model_provider"] = model_provider
        context["model_name"] = model_name
        context["model_version"] = model_version
        context["temperature"] = temperature
        context["prediction_meta"] = pred_meta
        pred_rows.append(
            (
                run_id,
                str(row["task_id"]),
                int(pred_label),
                float(conf),
                int(tokens_in),
                int(tokens_out),
                float(latency_ms),
                float(cost_est),
                json.dumps(context),
            )
        )
        y_true.append(gold)
        y_pred.append(int(pred_label))

    conn.executemany(
        """
        INSERT OR REPLACE INTO predictions(run_id,task_id,pred_label,confidence,tokens_in,tokens_out,latency_ms,cost_estimate,context_json)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        pred_rows,
    )
    conn.execute(
        "UPDATE runs SET ended_at = ?, status = ?, notes = ? WHERE run_id = ?",
        (
            utc_now(),
            "completed",
            f"backend={backend};q_non_trivial={q_non_trivial};n_eval={len(y_true)}",
            run_id,
        ),
    )
    conn.commit()
    conn.close()

    if workspace is not None:
        ensure_dir(workspace / "json")
        pred_path = workspace / "json" / f"predictions_{run_id}.jsonl"
        with pred_path.open("w") as f:
            for (rid, tid, pred, conf, tin, tout, lat, cost, ctx), gold in zip(pred_rows, y_true):
                f.write(
                    json.dumps(
                        {
                            "run_id": rid,
                            "task_id": tid,
                            "pred_label": pred,
                            "gold_label": int(gold),
                            "confidence": conf,
                            "tokens_in": tin,
                            "tokens_out": tout,
                            "latency_ms": lat,
                            "cost_estimate": cost,
                            "context": json.loads(ctx),
                        }
                    )
                    + "\n"
                )
        identity = {
            "run_id": run_id,
            "arm": arm,
            "backend": backend,
            "model_provider": model_provider,
            "model_name": model_name,
            "model_version": model_version,
            "temperature": temperature,
            "seed": seed,
            "config_hash": config_hash,
            "prompt_hash": prompt_hash,
            "rag_hash": rag_hash,
            "dataset_version": bundle.dataset_version,
            "evaluation_timestamp": utc_now(),
        }
        (workspace / "json" / f"run_identity_{run_id}.json").write_text(json.dumps(identity, indent=2))

    return {
        "run_id": run_id,
        "arm": arm,
        "backend": backend,
        "model_provider": model_provider,
        "model_name": model_name,
        "n_eval": len(y_true),
        "accuracy": float(accuracy_score(np.array(y_true), np.array(y_pred))),
    }


def _latest_run_by_arm(conn: sqlite3.Connection) -> Dict[str, str]:
    rows = conn.execute(
        """
        SELECT arm, run_id, started_at
        FROM runs
        WHERE status = 'completed'
        ORDER BY started_at DESC
        """
    ).fetchall()
    out: Dict[str, str] = {}
    for arm, run_id, _ in rows:
        if arm not in out:
            out[str(arm)] = str(run_id)
    return out


def evaluate_latest_runs(
    db_path: Path,
    *,
    split: str = "test",
    n_bootstrap: int = 100,
    seed: int = 42,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    conn = connect_db(db_path)
    conn.row_factory = sqlite3.Row
    latest = _latest_run_by_arm(conn)
    if not latest:
        raise ValueError("No completed runs found. Run at least one arm first.")
    metrics_names = ("accuracy", "macro_f1", "balanced_accuracy")
    summary: Dict[str, Any] = {"created_at": utc_now(), "split": split, "runs": {}}
    for arm, run_id in latest.items():
        rows = conn.execute(
            """
            SELECT p.pred_label, t.gold_label
            FROM predictions p
            JOIN tasks t ON t.task_id = p.task_id
            WHERE p.run_id = ? AND t.split = ?
            ORDER BY p.task_id
            """,
            (run_id, split),
        ).fetchall()
        if not rows:
            continue
        y_true = np.array([int(r["gold_label"]) for r in rows], dtype=np.int64)
        y_pred = np.array([int(r["pred_label"]) for r in rows], dtype=np.int64)
        arm_metrics: Dict[str, Any] = {}
        for metric_name in metrics_names:
            value = _metric(metric_name, y_true, y_pred)
            ci_low, ci_high = _bootstrap_ci(y_true, y_pred, metric_name, n_bootstrap=n_bootstrap, seed=seed)
            arm_metrics[metric_name] = {
                "value": value,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "n": int(len(rows)),
            }
            conn.execute(
                """
                INSERT OR REPLACE INTO metrics(run_id,split,metric_name,metric_value,ci_low,ci_high,n)
                VALUES(?,?,?,?,?,?,?)
                """,
                (run_id, split, metric_name, value, ci_low, ci_high, len(rows)),
            )
        summary["runs"][arm] = {"run_id": run_id, "metrics": arm_metrics}
    conn.commit()
    conn.close()

    if workspace is not None:
        ensure_dir(workspace / "json")
        (workspace / "json" / "evaluation_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def run_null_and_leverage_audit(
    db_path: Path,
    *,
    metric: str = "accuracy",
    n_permutations: int = 200,
    seed: int = 42,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    conn = connect_db(db_path)
    conn.row_factory = sqlite3.Row
    latest = _latest_run_by_arm(conn)
    required = ["plain_llm", "plain_llm_rag", "math_governed", "sham_complexity", "simple_graph"]
    missing = [a for a in required if a not in latest]
    if missing:
        raise ValueError(f"Missing completed arm runs: {missing}")

    per_arm: Dict[str, Dict[str, np.ndarray]] = {}
    for arm in required:
        run_id = latest[arm]
        rows = conn.execute(
            """
            SELECT p.task_id, p.pred_label, t.gold_label, t.degree
            FROM predictions p
            JOIN tasks t ON t.task_id = p.task_id
            WHERE p.run_id = ? AND t.split = 'test'
            ORDER BY p.task_id
            """,
            (run_id,),
        ).fetchall()
        if not rows:
            raise ValueError(f"No test predictions for arm={arm}")
        per_arm[arm] = {
            "task_id": np.array([str(r["task_id"]) for r in rows], dtype=object),
            "y_pred": np.array([int(r["pred_label"]) for r in rows], dtype=np.int64),
            "y_true": np.array([int(r["gold_label"]) for r in rows], dtype=np.int64),
            "degree": np.array([float(r["degree"]) for r in rows], dtype=np.float64),
        }

    # Align by task order.
    base_true = per_arm["math_governed"]["y_true"]
    baseline_arms = ["plain_llm", "plain_llm_rag", "sham_complexity", "simple_graph"]
    metric_math = _metric(metric, base_true, per_arm["math_governed"]["y_pred"])
    baseline_metrics = {
        arm: _metric(metric, base_true, per_arm[arm]["y_pred"]) for arm in baseline_arms
    }
    best_baseline = max(baseline_metrics.values())
    delta = metric_math - best_baseline

    rng = np.random.default_rng(seed)
    perm_stats: List[float] = []
    for _ in range(n_permutations):
        perm_idx = rng.permutation(len(base_true))
        y_perm = base_true[perm_idx]
        m = _metric(metric, y_perm, per_arm["math_governed"]["y_pred"])
        b = max(_metric(metric, y_perm, per_arm[a]["y_pred"]) for a in baseline_arms)
        perm_stats.append(m - b)
    perm_stats_arr = np.array(perm_stats, dtype=np.float64)
    p_value = float(np.mean(perm_stats_arr >= delta))
    null_pass = bool(delta > 0 and p_value <= 0.05)

    deg = per_arm["math_governed"]["degree"]
    cut = float(np.percentile(deg, 90.0))
    keep = deg < cut
    if int(np.sum(keep)) < 5:
        keep = np.ones_like(deg, dtype=bool)
    delta_full = delta
    delta_reduced = _metric(metric, base_true[keep], per_arm["math_governed"]["y_pred"][keep]) - max(
        _metric(metric, base_true[keep], per_arm[a]["y_pred"][keep]) for a in baseline_arms
    )
    leverage_drop = delta_full - delta_reduced
    leverage_pass = bool(delta_reduced > 0 and leverage_drop <= 0.03)

    headline = {
        "metric": metric,
        "math_governed": metric_math,
        "baseline_metrics": baseline_metrics,
        "best_baseline": best_baseline,
        "delta_vs_best_baseline": delta,
    }
    null_result = {
        "n_permutations": n_permutations,
        "p_value": p_value,
        "pass": null_pass,
    }
    leverage_result = {
        "degree_cutoff_90pct": cut,
        "delta_full": delta_full,
        "delta_without_top_degree": delta_reduced,
        "delta_drop": leverage_drop,
        "pass": leverage_pass,
    }
    overall_pass = bool(null_pass and leverage_pass)

    audit_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    conn.execute(
        """
        INSERT INTO audits(audit_id,created_at,headline_json,null_json,leverage_json,pass)
        VALUES(?,?,?,?,?,?)
        """,
        (
            audit_id,
            utc_now(),
            json.dumps(headline),
            json.dumps(null_result),
            json.dumps(leverage_result),
            1 if overall_pass else 0,
        ),
    )
    conn.commit()
    conn.close()

    out = {
        "audit_id": audit_id,
        "headline": headline,
        "null": null_result,
        "leverage": leverage_result,
        "pass": overall_pass,
    }
    if workspace is not None:
        ensure_dir(workspace / "json")
        (workspace / "json" / "audit_gate.json").write_text(json.dumps(out, indent=2))
    return out


def write_headline_table(
    db_path: Path,
    *,
    workspace: Path,
    metric: str = "accuracy",
) -> Dict[str, Any]:
    ensure_dir(workspace / "reports")
    ensure_dir(workspace / "json")
    conn = connect_db(db_path)
    conn.row_factory = sqlite3.Row
    latest = _latest_run_by_arm(conn)
    rows_out: List[Dict[str, Any]] = []
    for arm, run_id in latest.items():
        row = conn.execute(
            """
            SELECT metric_value, ci_low, ci_high, n
            FROM metrics
            WHERE run_id = ? AND split = 'test' AND metric_name = ?
            """,
            (run_id, metric),
        ).fetchone()
        if row is None:
            continue
        rows_out.append(
            {
                "arm": arm,
                "run_id": run_id,
                "metric": metric,
                "value": float(row["metric_value"]),
                "ci_low": float(row["ci_low"]) if row["ci_low"] is not None else None,
                "ci_high": float(row["ci_high"]) if row["ci_high"] is not None else None,
                "n": int(row["n"]),
            }
        )

    audit = conn.execute(
        "SELECT audit_id, pass, headline_json, null_json, leverage_json FROM audits ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    audit_obj = None
    gate_pass = False
    if audit is not None:
        audit_obj = {
            "audit_id": str(audit["audit_id"]),
            "pass": bool(int(audit["pass"])),
            "headline": json.loads(audit["headline_json"]),
            "null": json.loads(audit["null_json"]),
            "leverage": json.loads(audit["leverage_json"]),
        }
        gate_pass = bool(audit_obj["pass"])

    csv_path = workspace / "reports" / "headline_table.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["arm", "run_id", "metric", "value", "ci_low", "ci_high", "n", "gate_pass"])
        writer.writeheader()
        for row in rows_out:
            out_row = dict(row)
            out_row["gate_pass"] = gate_pass
            writer.writerow(out_row)

    report_lines = [
        "# Staged OrgBench Headline Report",
        f"Generated: {utc_now()}",
        "",
        "## Headline Table",
        "",
        "| Arm | Metric | Value | 95% CI | n | Gate pass |",
        "|-----|--------|-------|--------|---|-----------|",
    ]
    for row in sorted(rows_out, key=lambda x: x["arm"]):
        ci = "n/a"
        if row["ci_low"] is not None and row["ci_high"] is not None:
            ci = f"[{row['ci_low']:.4f}, {row['ci_high']:.4f}]"
        report_lines.append(
            f"| {row['arm']} | {row['metric']} | {row['value']:.4f} | {ci} | {row['n']} | {gate_pass} |"
        )
    report_lines.extend(
        [
            "",
            "## Gate Summary",
            f"- Overall null/leverage gate pass: {gate_pass}",
        ]
    )
    if audit_obj is not None:
        report_lines.extend(
            [
                f"- Null audit: {json.dumps(audit_obj['null'])}",
                f"- Leverage audit: {json.dumps(audit_obj['leverage'])}",
                "",
            ]
        )
    report_lines.extend(
        [
            "## What Would Make This Look Good While Still Being Wrong?",
            "- Leakage between train/test nodes or labels.",
            "- Density/degree confounding that mimics governance gains.",
            "- Label contamination from preprocessing choices.",
            "- Extra orchestration gains misattributed to boundary math.",
            "",
            "## Claim Status",
            "PROMOTE" if gate_pass else "DO NOT PROMOTE",
        ]
    )
    md_path = workspace / "reports" / "headline_report.md"
    md_path.write_text("\n".join(report_lines))

    out = {
        "rows": rows_out,
        "gate_pass": gate_pass,
        "audit": audit_obj,
        "headline_csv": str(csv_path),
        "headline_md": str(md_path),
    }
    (workspace / "json" / "headline_report.json").write_text(json.dumps(out, indent=2))
    return out
