#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
analyze-failures.py — Classify eval results from an iteration directory.

Reads eval-<N>/with_skill/grading.json and eval-<N>/without_skill/grading.json
files and classifies each eval into one of four categories:

  strong_discriminator   — passes with skill, fails without (skill is adding value)
  both_pass              — passes in both configs (not measuring skill value; consider
                           removing or strengthening)
  both_fail              — fails in both configs (assertion may be broken or too hard;
                           fix before next iteration)
  weak_discriminator     — with_skill pass rate slightly higher but not a strong signal

Usage:
  python3 tests/analyze-failures.py --iteration-dir DIR [--output FILE]
  python3 tests/analyze-failures.py --iteration-dir DIR --threshold 0.5

Options:
  --iteration-dir DIR   Workspace iteration directory containing eval-<N>/ subdirs
  --output FILE         Path to save the analysis JSON (also printed to stdout)
  --threshold FLOAT     Min delta to classify as strong_discriminator (default: 0.5)

Exit codes:
  0   Analysis produced (may still contain both_fail or non-discriminating evals)
  2   Usage or I/O error
"""

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as e:
            print(f"Warning: could not parse {path}: {e}", file=sys.stderr)
    return None


def classify_eval(with_rate: float | None, without_rate: float | None, threshold: float) -> str:
    if with_rate is None or without_rate is None:
        return "missing_data"
    delta = with_rate - without_rate
    if delta >= threshold:
        return "strong_discriminator"
    if with_rate >= 0.67 and without_rate >= 0.67:
        return "both_pass"
    if with_rate <= 0.33 and without_rate <= 0.33:
        return "both_fail"
    return "weak_discriminator"


def main():
    parser = argparse.ArgumentParser(
        prog="analyze-failures.py",
        description="Classify per-eval pass/fail patterns from a benchmark iteration directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 tests/analyze-failures.py \\\n"
            "      --iteration-dir autogrind-workspace/iteration-2/\n"
            "  python3 tests/analyze-failures.py \\\n"
            "      --iteration-dir autogrind-workspace/iteration-2/ \\\n"
            "      --output autogrind-workspace/iteration-2/failure_analysis.json\n\n"
            "Categories:\n"
            "  strong_discriminator  passes with_skill, fails without — skill is working\n"
            "  both_pass             passes in both — may not measure skill value\n"
            "  both_fail             fails in both — assertion may be broken or too hard\n"
            "  weak_discriminator    small delta — inconclusive\n"
            "  missing_data          grading.json absent for one or both configs\n"
        ),
    )
    parser.add_argument(
        "--iteration-dir", required=True, metavar="DIR",
        help="Path to the iteration directory (e.g., autogrind-workspace/iteration-2/)",
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Path to save failure_analysis.json (also printed to stdout)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.5, metavar="FLOAT",
        help="Minimum delta (with_skill - without_skill pass rate) to classify as strong_discriminator (default: 0.5)",
    )
    args = parser.parse_args()

    iteration_dir = Path(args.iteration_dir)
    if not iteration_dir.is_dir():
        print(f"Error: iteration directory not found: {args.iteration_dir}", file=sys.stderr)
        sys.exit(2)

    eval_dirs = sorted(iteration_dir.glob("eval-*"), key=lambda p: int(p.name.split("-")[1]))

    categories: dict[str, list] = {
        "strong_discriminator": [],
        "both_pass": [],
        "both_fail": [],
        "weak_discriminator": [],
        "missing_data": [],
    }

    for eval_dir in eval_dirs:
        try:
            eval_id = int(eval_dir.name.split("-")[1])
        except (IndexError, ValueError):
            continue

        with_grading = load_json(eval_dir / "with_skill" / "grading.json")
        without_grading = load_json(eval_dir / "without_skill" / "grading.json")

        with_rate = with_grading["summary"]["pass_rate"] if with_grading else None
        without_rate = without_grading["summary"]["pass_rate"] if without_grading else None

        category = classify_eval(with_rate, without_rate, args.threshold)

        entry = {
            "eval_id": eval_id,
            "with_skill_pass_rate": with_rate,
            "without_skill_pass_rate": without_rate,
            "delta": round(with_rate - without_rate, 2) if with_rate is not None and without_rate is not None else None,
        }

        if with_grading and without_grading:
            with_failures = [
                r["text"] for r in with_grading.get("assertion_results", []) if not r["passed"]
            ]
            without_failures = [
                r["text"] for r in without_grading.get("assertion_results", []) if not r["passed"]
            ]
            if with_failures:
                entry["with_skill_failures"] = with_failures
            if without_failures:
                entry["without_skill_failures"] = without_failures

        categories[category].append(entry)

    total = sum(len(v) for v in categories.values())
    analysis = {
        "iteration_dir": str(iteration_dir),
        "threshold": args.threshold,
        "total_evals": total,
        "summary": {cat: len(entries) for cat, entries in categories.items() if entries},
        "action_needed": {
            "strengthen_or_remove": [e["eval_id"] for e in categories["both_pass"]],
            "fix_assertion": [e["eval_id"] for e in categories["both_fail"]],
        },
        "classifications": {cat: entries for cat, entries in categories.items() if entries},
    }

    json_str = json.dumps(analysis, indent=2)
    print(json_str)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str)
        print(f"Saved analysis to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
