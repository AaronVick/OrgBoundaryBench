#!/usr/bin/env python3
"""
Run remote compute via Claude API (bootstrap null dominance, permutation p-values).

Reads a payload from prepare_remote_compute_payload.py, sends it with explicit
math instructions to Claude Opus 4.6, parses the structured JSON result, and
writes artifacts to outputs/remote_compute_claude/<run_id>/.

Requires ANTHROPIC_API_KEY. See docs/REMOTE_COMPUTE_PROTOCOL.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv_if_present() -> None:
    """Load KEY=VALUE from ROOT/.env into os.environ (no extra dependency). Skip if SKIP_DOTENV=1 (e.g. tests)."""
    if os.environ.get("SKIP_DOTENV", "").strip() == "1":
        return
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key:
                os.environ.setdefault(key, value)


REMOTE_COMPUTE_INSTRUCTIONS = r"""
You must reply with ONLY a single JSON object. No explanations, no step-by-step, no other text. Your first character must be { and your last character must be }.

Perform the two statistical procedures below on the provided payload. Put the result in the JSON format at the end.

Definitions:
- NMI: Normalized Mutual Information between two label vectors (use arithmetic mean method). If both vectors have fewer than 2 distinct values, NMI = 1.0 if they are identical else 0.0.
- ARI: Adjusted Rand Index between two label vectors.
- macro-F1: Macro-averaged F1 over classes (zero_division=0).

Labeled indices: indices i where payload.labels[i] >= 0. Let m = number of labeled indices, true_lab = list of payload.labels at those indices (length m). For each partition (q_star or rival), produce pred = length-m list of block IDs for those same indices (block ID = index of the block containing that node, 0..k-1).

Procedure 1 — Bootstrap null dominance (if task is bootstrap_null_dominance or combined):
1. star_nmi_full = NMI(true_lab, pred_star); for each rival r, rival_nmi[r] = NMI(true_lab, pred_rivals[r]). best_rival = argmax rival_nmi; best_rival_nmi_full = rival_nmi[best_rival].
2. For b = 0..n_bootstrap-1: use deterministic resample from seed+b (resample m indices from 0..m-1 with replacement). D_b = NMI(true_lab[draw], pred_star[draw]) - max over r of NMI(true_lab[draw], pred_rivals[r][draw]). Collect D_samples.
3. mean_D = mean(D_samples), std_D = std(D_samples), ci_lower = 2.5th percentile, ci_upper = 97.5th percentile. pass = (ci_lower > 0 and (star_nmi_full - best_rival_nmi_full) > 0).

Procedure 2 — Permutation external p-values (if task is permutation_external_pvals or combined):
1. nmi_star = NMI(true_lab, pred_star), ari_star = ARI(true_lab, pred_star), f1_star = macro-F1(true_lab, pred_star).
2. For p = 0..n_perm-1: use deterministic permutation of true_lab from seed+p. Compute nmi_null, ari_null, f1_null. nmi_p_value = (count of null_nmi >= nmi_star) / n_perm; similarly ari_p_value, f1_p_value.

Output format: Return exactly one JSON object, no markdown fences, with these keys (use null for optional spot_check if omitted):
- run_id: string (ISO8601 UTC, e.g. 2026-03-08T12:00:00Z)
- model_id: "claude-opus-4-6"
- confirmation: "REMOTE_COMPUTE_v1"
- bootstrap: { mean_D, std_D, ci_lower, ci_upper, n_bootstrap, best_rival_name_full, best_rival_nmi_full, star_nmi_full, pass } (if task requested it)
- permutation: { nmi_star, ari_star, f1_star, nmi_p_value, ari_p_value, f1_p_value } (if task requested it)
- spot_check: optional object with e.g. one bootstrap sample index and D value for verification

Again: reply with ONLY that JSON object. First character { , last character }. Nothing else.
"""


def _payload_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Try raw JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try code block ```json ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Find all complete { ... } objects (balanced braces), prefer last one (model often outputs reasoning then JSON)
    candidates = []
    i = 0
    while i < len(text):
        start = text.find("{", i)
        if start < 0:
            break
        depth = 0
        for j in range(start, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        candidates.append(json.loads(text[start : j + 1]))
                    except json.JSONDecodeError:
                        pass
                    i = j + 1
                    break
        else:
            i = start + 1
    if candidates:
        # Prefer object that has expected keys (run_id, confirmation, bootstrap or permutation)
        for c in reversed(candidates):
            if isinstance(c, dict) and (c.get("confirmation") or c.get("bootstrap") or c.get("permutation")):
                return c
        return candidates[-1]
    raise ValueError("No valid JSON object found in response")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run remote compute via Claude API.")
    ap.add_argument("--payload", type=Path, default=ROOT / "outputs" / "remote_compute_payloads" / "payload.json")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "remote_compute_claude")
    ap.add_argument("--model", type=str, default="claude-opus-4-6")
    ap.add_argument("--anthropic-api-key-env", type=str, default="ANTHROPIC_API_KEY")
    ap.add_argument("--anthropic-version", type=str, default="2023-06-01")
    args = ap.parse_args()

    _load_dotenv_if_present()
    api_key = os.environ.get(args.anthropic_api_key_env, "").strip()
    # Also check common typo / alternate name so .env works out of the box
    if not api_key:
        api_key = os.environ.get("anthroptic_API_KEY", "").strip()
    if not api_key:
        print(f"Set {args.anthropic_api_key_env} (or add it to {ROOT / '.env'})", file=__import__("sys").stderr)
        return 1

    payload_path = args.payload.resolve()
    if not payload_path.exists():
        print(f"Payload not found: {payload_path}", file=__import__("sys").stderr)
        return 1

    with payload_path.open() as f:
        payload = json.load(f)

    payload_hash_val = _payload_hash(payload)
    user_content = (
        REMOTE_COMPUTE_INSTRUCTIONS
        + "\n\n---\nPayload:\n"
        + json.dumps(payload, indent=2)
    )

    import urllib.request
    import urllib.error
    import time

    url = "https://api.anthropic.com/v1/messages"
    body = {
        "model": args.model,
        "max_tokens": 8192,
        "system": "You respond only with a single JSON object. No explanations, no step-by-step reasoning, no markdown or code fences. Your entire response must be valid JSON starting with { and ending with }.",
        "messages": [{"role": "user", "content": user_content}],
    }
    req = urllib.request.Request(
        url=url,
        method="POST",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": args.anthropic_version,
        },
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")
        print(f"API HTTP {e.code}: {body_err}", file=__import__("sys").stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"API error: {e.reason}", file=__import__("sys").stderr)
        return 1
    elapsed = time.perf_counter() - t0

    parsed = json.loads(raw)
    content = parsed.get("content", [])
    text = ""
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text += item.get("text", "")
    try:
        result = _extract_json_from_text(text)
    except ValueError as e:
        print(f"Parse error: {e}. Response snippet: {text[:500]}", file=__import__("sys").stderr)
        return 1

    run_id = result.get("run_id") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    result["run_id"] = run_id
    result["model_id"] = result.get("model_id") or args.model
    result["payload_hash"] = payload_hash_val

    out_run = args.out_dir.resolve() / run_id.replace(":", "-").replace(" ", "T")
    out_run.mkdir(parents=True, exist_ok=True)
    with (out_run / "payload.json").open("w") as f:
        json.dump(payload, f, indent=2)
    with (out_run / "result.json").open("w") as f:
        json.dump(result, f, indent=2)
    run_metadata = {
        "run_id": run_id,
        "model_id": args.model,
        "payload_hash": payload_hash_val,
        "payload_path": str(payload_path),
        "elapsed_seconds": round(elapsed, 2),
        "confirmation": result.get("confirmation"),
    }
    with (out_run / "run_metadata.json").open("w") as f:
        json.dump(run_metadata, f, indent=2)
    with (out_run / "prompt_preview.txt").open("w") as f:
        f.write(user_content[:8000] + "\n... [truncated]\n" if len(user_content) > 8000 else user_content)
    print(f"Wrote {out_run}")
    return 0


if __name__ == "__main__":
    __import__("sys").exit(main())
