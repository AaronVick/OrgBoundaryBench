#!/usr/bin/env python3
"""
Update docs/prds/claim_registry.yaml from test results (PRD-06).

Usage:
  pytest tests/ && python scripts/update_claim_registry.py --result pass
  python scripts/update_claim_registry.py --result fail  # if tests failed

MVP claims updated: T3.1, T3.2, T3.3, T3.4, E6.1.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "docs" / "prds" / "claim_registry.yaml"
MVP_IDS = {"T3.1", "T3.2", "T3.3", "T3.4", "E6.1"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Update claim registry last_result and last_run.")
    ap.add_argument("--result", choices=("pass", "fail"), default="pass", help="Result of MVP test run")
    ap.add_argument("--registry", type=Path, default=REGISTRY_PATH, help="Path to claim_registry.yaml")
    args = ap.parse_args()
    path = args.registry
    if not path.exists():
        raise SystemExit(f"Registry not found: {path}")
    lines = path.read_text().splitlines()
    out = []
    current_id = None
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for line in lines:
        stripped = line.strip()
        if "id:" in stripped and stripped.startswith("- "):
            # Line is "- id: T3.1"
            val = stripped.split("id:", 1)[1].strip()
            current_id = val if val in MVP_IDS else None
        elif stripped.startswith("id:"):
            val = stripped[4:].strip()
            current_id = val if val in MVP_IDS else None
        if current_id and ("last_result:" in line and "null" in line):
            out.append(f"    last_result: {args.result}")
            out.append(f'    last_run: "{now}"')
            current_id = None
            continue
        out.append(line)
    path.write_text("\n".join(out) + "\n")
    print(f"Updated MVP claims to last_result={args.result}, last_run={now}")


if __name__ == "__main__":
    main()
