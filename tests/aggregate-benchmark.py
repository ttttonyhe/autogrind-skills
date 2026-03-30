#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
aggregate-benchmark.py — Aggregate grading.json and timing.json files from a
workspace iteration directory into a benchmark.json summary.

Reads eval-<N>/{with_skill,without_skill}/grading.json and timing.json files
from an iteration directory and produces benchmark.json with pass rate, token,
and timing statistics per the agentskills.io benchmark format.

Usage:
  python3 tests/aggregate-benchmark.py --iteration-dir DIR [--output FILE]

The iteration directory should follow the workspace structure:
  iteration-1/
  ├── eval-1/
  │   ├── with_skill/grading.json
  │   ├── with_skill/timing.json
  │   ├── without_skill/grading.json
  │   └── without_skill/timing.json
  └── eval-2/
      └── ...

Exit codes:
  0   benchmark.json produced successfully
  2   Usage or I/O error
"""

import argparse
import json
import math
import sys
from pathlib import Path


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def load_json(path: Path) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as e:
            print(f"Warning: could not parse {path}: {e}", file=sys.stderr)
    return None


def collect_stats(iteration_dir: Path, config: str) -> dict:
    """Collect pass_rate, token, and timing stats across all evals for a given config."""
    pass_rates, tokens, durations = [], [], []

    for eval_dir in sorted(iteration_dir.glob("eval-*")):
        config_dir = eval_dir / config
        grading = load_json(config_dir / "grading.json")
        timing = load_json(config_dir / "timing.json")

        if grading:
            summary = grading.get("summary", {})
            if "pass_rate" in summary:
                pass_rates.append(summary["pass_rate"])

        if timing:
            if "total_tokens" in timing:
                tokens.append(timing["total_tokens"])
            if "duration_ms" in timing:
                durations.append(timing["duration_ms"] / 1000.0)

    result = {}
    if pass_rates:
        result["pass_rate"] = {"mean": round(mean(pass_rates), 3), "stddev": round(stddev(pass_rates), 3)}
    if tokens:
        result["tokens"] = {"mean": round(mean(tokens)), "stddev": round(stddev(tokens))}
    if durations:
        result["time_seconds"] = {"mean": round(mean(durations), 1), "stddev": round(stddev(durations), 1)}

    return result


def main():
    parser = argparse.ArgumentParser(
        prog="aggregate-benchmark.py",
        description="Aggregate grading/timing results from a workspace iteration into benchmark.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 tests/aggregate-benchmark.py --iteration-dir autogrind-workspace/iteration-1/\n"
            "  python3 tests/aggregate-benchmark.py \\\n"
            "      --iteration-dir autogrind-workspace/iteration-1/ \\\n"
            "      --output autogrind-workspace/iteration-1/benchmark.json\n\n"
            "Output is benchmark.json printed to stdout. Use --output to also save to a file."
        ),
    )
    parser.add_argument(
        "--iteration-dir", required=True, metavar="DIR",
        help="Path to the iteration directory (e.g., autogrind-workspace/iteration-1/)",
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Path to save benchmark.json (also printed to stdout)",
    )
    args = parser.parse_args()

    iteration_dir = Path(args.iteration_dir)
    if not iteration_dir.is_dir():
        print(f"Error: iteration directory not found: {args.iteration_dir}", file=sys.stderr)
        sys.exit(2)

    with_skill = collect_stats(iteration_dir, "with_skill")
    without_skill = collect_stats(iteration_dir, "without_skill")

    delta = {}
    if "pass_rate" in with_skill and "pass_rate" in without_skill:
        delta["pass_rate"] = round(
            with_skill["pass_rate"]["mean"] - without_skill["pass_rate"]["mean"], 3
        )
    if "tokens" in with_skill and "tokens" in without_skill:
        delta["tokens"] = round(
            with_skill["tokens"]["mean"] - without_skill["tokens"]["mean"]
        )
    if "time_seconds" in with_skill and "time_seconds" in without_skill:
        delta["time_seconds"] = round(
            with_skill["time_seconds"]["mean"] - without_skill["time_seconds"]["mean"], 1
        )

    benchmark = {
        "run_summary": {
            "with_skill": with_skill,
            "without_skill": without_skill,
            "delta": delta,
        }
    }

    json_str = json.dumps(benchmark, indent=2)
    print(json_str)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str)
        print(f"Saved benchmark to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
