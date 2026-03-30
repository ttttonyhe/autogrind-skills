#!/usr/bin/env python3
"""
grade-evals.py — Grade AutoGrind eval assertions against an agent response.

Reads assertions for a given eval ID from evals/evals.json, evaluates each
assertion against the provided response text using the claude CLI, and outputs
a grading.json result to stdout.

Usage:
  python3 scripts/grade-evals.py --response FILE --eval-id N [--evals FILE]

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


def main():
    parser = argparse.ArgumentParser(
        prog="grade-evals.py",
        description="Grade AutoGrind eval assertions against an agent response",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/grade-evals.py --response response.txt --eval-id 1\n"
            "  python3 scripts/grade-evals.py --response out.txt --eval-id 4 --evals evals/evals.json\n\n"
            "Output is grading.json written to stdout. Pipe to a file to save:\n"
            "  python3 scripts/grade-evals.py --response out.txt --eval-id 1 > grading.json"
        ),
    )
    parser.add_argument(
        "--response", required=True, metavar="FILE",
        help="Path to the agent response text file to grade",
    )
    parser.add_argument(
        "--eval-id", required=True, type=int, metavar="N",
        help="Eval ID from evals.json to grade",
    )
    parser.add_argument(
        "--evals",
        default=str(Path(__file__).parent.parent / "evals" / "evals.json"),
        metavar="FILE",
        help="Path to evals.json (default: ../evals/evals.json)",
    )
    args = parser.parse_args()

    response_path = Path(args.response)
    evals_path = Path(args.evals)

    if not response_path.exists():
        print(f"Error: response file not found: {args.response}", file=sys.stderr)
        sys.exit(2)
    if not evals_path.exists():
        print(f"Error: evals file not found: {args.evals}", file=sys.stderr)
        sys.exit(2)

    evals_data = json.loads(evals_path.read_text())
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

    assertion_results = [grade_assertion(a, response_text) for a in assertions]

    total = len(assertion_results)
    passed_count = sum(1 for r in assertion_results if r["passed"])
    failed_count = total - passed_count

    output = {
        "assertion_results": assertion_results,
        "summary": {
            "passed": passed_count,
            "failed": failed_count,
            "total": total,
            "pass_rate": round(passed_count / total, 2) if total > 0 else 0.0,
        },
    }
    print(json.dumps(output, indent=2))
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
