#!/usr/bin/env python3
"""
PRD XVI (extendedPRD.md): Validate that a findings document contains the 9 required sections.

Required per extendedPRD.md: (1) hypotheses tested, (2) design, (3) datasets,
(4) controls and baselines, (5) nulls and outlier checks, (6) results,
(7) falsification status, (8) limitations, (9) next empirical step.

Accepts equivalent section headers (e.g. Objectives, Methods, Public data used).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Map required concept -> list of header substrings (case-insensitive)
REQUIRED = {
    "hypotheses": ["hypotheses tested", "objectives", "claims under test", "hypothesis"],
    "design": ["design", "methods", "what we did", "method"],
    "datasets": ["datasets", "public data", "data used"],
    "controls_and_baselines": ["controls and baselines", "baseline", "baselines"],
    "nulls_and_outlier": ["nulls", "outlier", "leverage", "falsification", "analysis"],
    "results": ["results", "outcomes"],
    "falsification_status": ["falsification status", "falsification", "analysis"],
    "limitations": ["limitations"],
    "next_step": ["next empirical step", "next step", "conclusions", "conclusion"],
}


def _headings(path: Path) -> list[str]:
    """Extract ## or ### heading text (strip # and whitespace)."""
    text = path.read_text()
    lines = []
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(.+)", line)
        if m:
            lines.append(m.group(1).strip().lower())
    return lines


def validate(path: Path) -> tuple[bool, list[str]]:
    """
    Check that path (markdown) has at least one heading matching each required concept.
    Returns (all_ok, list of missing concept names).
    """
    headings = _headings(path)
    missing = []
    for concept, substrings in REQUIRED.items():
        found = any(
            any(s in h for s in substrings)
            for h in headings
        )
        if not found:
            missing.append(concept)
    return (len(missing) == 0, missing)


def main() -> int:
    ap = argparse.ArgumentParser(description="PRD XVI: Validate findings doc has 9 required sections.")
    ap.add_argument("path", type=Path, nargs="?", default=None, help="Findings .md file (default: docs/findings/*.md)")
    ap.add_argument("--list", action="store_true", help="List required section concepts and exit")
    args = ap.parse_args()

    if args.list:
        for k, v in REQUIRED.items():
            print(f"  {k}: {v}")
        return 0

    root = Path(__file__).resolve().parents[1]
    if args.path is not None:
        paths = [Path(args.path).resolve()]
        if not paths[0].exists():
            print(f"File not found: {paths[0]}", file=sys.stderr)
            return 2
    else:
        findings_dir = root / "docs" / "findings"
        paths = list(findings_dir.glob("*.md")) if findings_dir.exists() else []
        paths = [p for p in paths if p.name != "FINDINGS_TEMPLATE.md"]

    if not paths:
        print("No findings files to validate.", file=sys.stderr)
        return 1

    all_ok = True
    for path in sorted(paths):
        ok, missing = validate(path)
        if ok:
            print(f"OK {path.relative_to(root)}")
        else:
            print(f"MISSING {path.relative_to(root)}: {', '.join(missing)}", file=sys.stderr)
            all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
