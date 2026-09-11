#!/usr/bin/env python3
"""Rank Scandal Radar investigation candidates.

Scores investigative expected value, not likelihood of misconduct.
Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "data" / "candidates.csv"

WEIGHTS: Dict[str, int] = {
    "scale": 12,
    "privilege": 14,
    "incentive_conflict": 16,
    "claim_specificity": 14,
    "testability": 16,
    "potential_harm": 10,
    "reproducibility": 10,
    "novelty": 8,
}


def calculate_score(row: Dict[str, str]) -> float:
    total = 0.0
    for factor, weight in WEIGHTS.items():
        value = float(row[factor])
        if not 0 <= value <= 5:
            raise ValueError(f"{row.get('name', '<unknown>')}: {factor} must be 0..5, got {value}")
        total += (value / 5.0) * weight
    return round(total, 1)


def load_candidates(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    required = {"name", "category", "installs", "extension_id", "priority_score", "lead", "source"} | set(WEIGHTS)
    if not rows:
        raise ValueError("candidate registry is empty")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"candidate registry missing columns: {sorted(missing)}")

    for row in rows:
        row["computed_score"] = f"{calculate_score(row):.1f}"
    return rows


def validate_scores(rows: Iterable[Dict[str, str]]) -> List[str]:
    errors: List[str] = []
    seen_ids = set()
    for row in rows:
        recorded = float(row["priority_score"])
        computed = float(row["computed_score"])
        if recorded != computed:
            errors.append(f"{row['name']}: recorded={recorded:.1f}, computed={computed:.1f}")
        ext_id = row["extension_id"]
        if ext_id in seen_ids:
            errors.append(f"duplicate extension_id: {ext_id}")
        seen_ids.add(ext_id)
        if len(ext_id) != 32:
            errors.append(f"{row['name']}: extension_id should be 32 chars, got {len(ext_id)}")
    return errors


def render_markdown(rows: List[Dict[str, str]]) -> str:
    lines = [
        "| Rank | Score | Target | Users | Category | Lead |",
        "|---:|---:|---|---:|---|---|",
    ]
    for i, row in enumerate(rows, 1):
        lines.append(
            f"| {i} | {float(row['computed_score']):.1f} | {row['name']} | "
            f"{int(row['installs']):,} | {row['category']} | {row['lead']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--category", help="case-insensitive substring filter")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument("--check", action="store_true", help="validate recorded scores and IDs")
    args = parser.parse_args()

    rows = load_candidates(args.csv)
    errors = validate_scores(rows)
    if args.check and errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if args.category:
        needle = args.category.casefold()
        rows = [r for r in rows if needle in r["category"].casefold()]

    rows.sort(key=lambda r: (-float(r["computed_score"]), -int(r["installs"]), r["name"].casefold()))
    rows = rows[: max(args.top, 0)]

    if args.json:
        output = []
        for rank, row in enumerate(rows, 1):
            item = dict(row)
            item["rank"] = rank
            item["installs"] = int(item["installs"])
            item["priority_score"] = float(item["computed_score"])
            item.pop("computed_score", None)
            output.append(item)
        print(json.dumps(output, indent=2))
    else:
        print(render_markdown(rows))

    if args.check:
        print("\nRegistry check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
