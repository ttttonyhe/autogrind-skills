#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
grade-evals.py — Grade AutoGrind eval assertions against an agent response.

Reads assertions for a given eval ID from evals/evals.json, evaluates each
assertion against the provided response text using the claude CLI, and outputs
a grading.json result.

Usage:
  python3 tests/grade-evals.py --response FILE --eval-id N [--output-dir DIR] [--evals FILE]
  python3 tests/grade-evals.py --all --responses-dir DIR [--output-dir DIR] [--evals FILE]

In --all mode, responses-dir must contain files named eval-<N>.txt for each eval ID.
In --output-dir mode, grading.json is saved to the directory (and also printed to stdout).

Exit codes:
  0   All assertions passed
  1   One or more assertions failed
  2   Usage or environment error

Requires: claude CLI (https://claude.ai/code)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def grade_assertion(assertion: str, response_text: str) -> dict:
    prompt = (
        "You are grading an agent response against a single assertion.\n\n"
        f"Assertion: {assertion}\n\n"
        "Agent response:\n"
        "---\n"
        f"{response_text}\n"
        "---\n\n"
        "Does the agent response satisfy the assertion?\n"
        "Reply with exactly one of:\n"
        "PASS: <one sentence of specific evidence from the response>\n"
        "FAIL: <one sentence explaining what is missing or wrong>"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
    except FileNotFoundError:
        print(
            "Error: claude CLI not found. Install from https://claude.ai/code",
            file=sys.stderr,
        )
        sys.exit(2)
    except subprocess.TimeoutExpired:
        output = "FAIL: Grading timed out"

    passed = output.startswith("PASS")
    evidence = output[6:].strip() if len(output) > 5 else output
    return {"text": assertion, "passed": passed, "evidence": evidence}


def grade_eval_case(eval_case: dict, response_text: str) -> dict:
    assertions = eval_case.get("assertions", [])
    assertion_results = [grade_assertion(a, response_text) for a in assertions]
    total = len(assertion_results)
    passed_count = sum(1 for r in assertion_results if r["passed"])
    return {
        "eval_id": eval_case["id"],
        "assertion_results": assertion_results,
        "summary": {
            "passed": passed_count,
            "failed": total - passed_count,
            "total": total,
            "pass_rate": round(passed_count / total, 2) if total > 0 else 0.0,
        },
    }


def save_output(result: dict, output_dir: Path | None, filename: str = "grading.json") -> None:
    json_str = json.dumps(result, indent=2)
    print(json_str)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / filename).write_text(json_str)
        print(f"Saved to {output_dir / filename}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        prog="grade-evals.py",
        description="Grade AutoGrind eval assertions against an agent response",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 tests/grade-evals.py --response response.txt --eval-id 1\n"
            "  python3 tests/grade-evals.py --response out.txt --eval-id 4 --evals evals/evals.json\n"
            "  python3 tests/grade-evals.py --response out.txt --eval-id 1 \\\n"
            "      --output-dir autogrind-workspace/iteration-1/eval-1/with_skill\n"
            "  python3 tests/grade-evals.py --all --responses-dir evals/workspace/responses/ \\\n"
            "      --output-dir autogrind-workspace/iteration-1/\n\n"
            "Output is grading.json printed to stdout. Use --output-dir to also save to a file.\n"
            "In --all mode, grading.json is saved to <output-dir>/eval-<N>/grading.json."
        ),
    )
    parser.add_argument(
        "--response", metavar="FILE",
        help="Path to the agent response text file to grade (single-eval mode)",
    )
    parser.add_argument(
        "--eval-id", type=int, metavar="N",
        help="Eval ID from evals.json to grade (single-eval mode)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Grade all evals in evals.json (batch mode)",
    )
    parser.add_argument(
        "--responses-dir", metavar="DIR",
        help="Directory containing eval-<N>.txt response files (batch mode)",
    )
    parser.add_argument(
        "--output-dir", metavar="DIR",
        help=(
            "Directory to save grading.json (single: saves grading.json in DIR; "
            "batch: saves eval-<N>/grading.json in DIR)"
        ),
    )
    parser.add_argument(
        "--evals",
        default=str(Path(__file__).parent.parent / "evals" / "evals.json"),
        metavar="FILE",
        help="Path to evals.json (default: ../evals/evals.json relative to this script)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    evals_path = Path(args.evals)
    if not evals_path.exists():
        print(f"Error: evals file not found: {args.evals}", file=sys.stderr)
        sys.exit(2)

    evals_data = json.loads(evals_path.read_text())

    if args.all:
        if not args.responses_dir:
            print(
                "Error: --responses-dir is required with --all",
                file=sys.stderr,
            )
            sys.exit(2)
        responses_dir = Path(args.responses_dir)
        if not responses_dir.is_dir():
            print(f"Error: responses directory not found: {args.responses_dir}", file=sys.stderr)
            sys.exit(2)

        eval_results = []
        for eval_case in evals_data["evals"]:
            response_file = responses_dir / f"eval-{eval_case['id']}.txt"
            if not response_file.exists():
                print(
                    f"Warning: response file not found for eval {eval_case['id']}: {response_file}",
                    file=sys.stderr,
                )
                continue
            print(
                f"Grading eval {eval_case['id']}: {len(eval_case.get('assertions', []))} assertions...",
                file=sys.stderr,
            )
            response_text = response_file.read_text()
            result = grade_eval_case(eval_case, response_text)
            eval_results.append(result)

            if output_dir is not None:
                eval_out_dir = output_dir / f"eval-{eval_case['id']}"
                eval_out_dir.mkdir(parents=True, exist_ok=True)
                (eval_out_dir / "grading.json").write_text(json.dumps(result, indent=2))
                print(f"Saved grading for eval {eval_case['id']} to {eval_out_dir}/grading.json", file=sys.stderr)

        total_evals = len(eval_results)
        total_assertions = sum(r["summary"]["total"] for r in eval_results)
        passed_assertions = sum(r["summary"]["passed"] for r in eval_results)
        batch_output = {
            "eval_results": eval_results,
            "summary": {
                "total_evals": total_evals,
                "total_assertions": total_assertions,
                "passed_assertions": passed_assertions,
                "failed_assertions": total_assertions - passed_assertions,
                "pass_rate": round(passed_assertions / total_assertions, 2) if total_assertions > 0 else 0.0,
            },
        }
        print(json.dumps(batch_output, indent=2))
        any_failed = any(r["summary"]["failed"] > 0 for r in eval_results)
        sys.exit(1 if any_failed else 0)

    # Single-eval mode
    if not args.response or args.eval_id is None:
        print(
            "Error: --response and --eval-id are required (or use --all with --responses-dir)",
            file=sys.stderr,
        )
        parser.print_help(sys.stderr)
        sys.exit(2)

    response_path = Path(args.response)
    if not response_path.exists():
        print(f"Error: response file not found: {args.response}", file=sys.stderr)
        sys.exit(2)

    eval_case = next((e for e in evals_data["evals"] if e["id"] == args.eval_id), None)
    if eval_case is None:
        ids = [e["id"] for e in evals_data["evals"]]
        print(
            f"Error: eval ID {args.eval_id} not found. Available IDs: {ids}",
            file=sys.stderr,
        )
        sys.exit(2)

    assertions = eval_case.get("assertions", [])
    if not assertions:
        print(f"Error: eval ID {args.eval_id} has no assertions to grade", file=sys.stderr)
        sys.exit(2)

    response_text = response_path.read_text()
    print(f"Grading eval {args.eval_id}: {len(assertions)} assertions...", file=sys.stderr)

    result = grade_eval_case(eval_case, response_text)
    save_output(result, output_dir)
    sys.exit(1 if result["summary"]["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
