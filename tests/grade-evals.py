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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


_timeout: int = 60


def grade_assertion(assertion: str, response_text: str) -> dict:
    prompt = (
        "You are grading an agent response against a single assertion.\n\n"
        f"Assertion: {assertion}\n\n"
        "Agent response:\n"
        "---\n"
        f"{response_text}\n"
        "---\n\n"
        "Does the agent response satisfy the assertion?\n\n"
        "Grading rules:\n"
        "- Require concrete evidence for PASS. Quote or specifically reference what in the response satisfies the assertion.\n"
        "- Do not give the benefit of the doubt. If the assertion says the response should do X and X is only vaguely implied, that is a FAIL.\n"
        "- The label alone is not evidence. If the assertion says 'includes a summary' and the response has a 'Summary' heading with one vague sentence, that is a FAIL.\n\n"
        "Reply with exactly one of:\n"
        "PASS: <one sentence quoting or referencing specific evidence from the response>\n"
        "FAIL: <one sentence explaining what is missing or why the response does not satisfy the assertion>"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=_timeout,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            print(
                f"Warning: claude CLI returned exit code {result.returncode}"
                + (f": {stderr[:120]}" if stderr else ""),
                file=sys.stderr,
            )
            output = f"FAIL: Grader call failed (exit {result.returncode})"
        else:
            output = result.stdout.strip()
    except FileNotFoundError:
        print(
            "Error: claude CLI not found. Install from https://claude.ai/code",
            file=sys.stderr,
        )
        sys.exit(2)
    except subprocess.TimeoutExpired:
        output = f"FAIL: Grading timed out after {_timeout}s"

    # Parse PASS/FAIL verdict: case-insensitive, skip any preamble before the verdict
    first_line = output.strip().split("\n")[0].strip() if output.strip() else ""
    upper = first_line.upper()
    if upper.startswith("PASS"):
        passed = True
        evidence = first_line[5:].strip().lstrip(":").strip() if len(first_line) > 4 else first_line
    elif upper.startswith("FAIL"):
        passed = False
        evidence = first_line[5:].strip().lstrip(":").strip() if len(first_line) > 4 else first_line
    else:
        passed = False
        evidence = f"Unparseable grader output: {first_line[:120]}"
    return {"text": assertion, "passed": passed, "evidence": evidence}


def grade_eval_case(eval_case: dict, response_text: str, workers: int = 1) -> dict:
    assertions = eval_case.get("assertions", [])
    if workers > 1 and len(assertions) > 1:
        with ThreadPoolExecutor(max_workers=min(workers, len(assertions))) as executor:
            futures = {executor.submit(grade_assertion, a, response_text): i for i, a in enumerate(assertions)}
            results_by_index = {}
            for future in as_completed(futures):
                idx = futures[future]
                results_by_index[idx] = future.result()
            assertion_results = [results_by_index[i] for i in range(len(assertions))]
    else:
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
            "      --output-dir autogrind-workspace/iteration-1/ --workers 8\n\n"
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
    parser.add_argument(
        "--timeout", type=int, default=60, metavar="SECONDS",
        help="Timeout in seconds for each grader call (default: 60)",
    )
    parser.add_argument(
        "--workers", type=int, default=1, metavar="N",
        help="Number of parallel grader workers (default: 1; use 5-10 to speed up batch grading)",
    )
    args = parser.parse_args()

    global _timeout
    _timeout = args.timeout

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

        def grade_one(eval_case: dict) -> dict | None:
            response_file = responses_dir / f"eval-{eval_case['id']}.txt"
            if not response_file.exists():
                print(
                    f"Warning: response file not found for eval {eval_case['id']}: {response_file}",
                    file=sys.stderr,
                )
                return None
            print(
                f"Grading eval {eval_case['id']}: {len(eval_case.get('assertions', []))} assertions...",
                file=sys.stderr,
            )
            # In --all mode, parallelism is at the eval level; assertions run sequentially
            # to avoid nested thread pools with unpredictable concurrency under rate limits.
            return grade_eval_case(eval_case, response_file.read_text(), workers=1)

        eval_results = []
        if args.workers > 1:
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                future_to_case = {executor.submit(grade_one, ec): ec for ec in evals_data["evals"]}
                for future in as_completed(future_to_case):
                    result = future.result()
                    if result is not None:
                        eval_results.append(result)
            eval_results.sort(key=lambda r: r["eval_id"])
        else:
            for eval_case in evals_data["evals"]:
                result = grade_one(eval_case)
                if result is not None:
                    eval_results.append(result)
                    if output_dir is not None:
                        eval_out_dir = output_dir / f"eval-{eval_case['id']}"
                        eval_out_dir.mkdir(parents=True, exist_ok=True)
                        (eval_out_dir / "grading.json").write_text(json.dumps(result, indent=2))
                        print(f"Saved grading for eval {eval_case['id']} to {eval_out_dir}/grading.json", file=sys.stderr)

        if args.workers > 1 and output_dir is not None:
            for result in eval_results:
                eval_out_dir = output_dir / f"eval-{result['eval_id']}"
                eval_out_dir.mkdir(parents=True, exist_ok=True)
                (eval_out_dir / "grading.json").write_text(json.dumps(result, indent=2))
                print(f"Saved grading for eval {result['eval_id']} to {eval_out_dir}/grading.json", file=sys.stderr)

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

    result = grade_eval_case(eval_case, response_text, workers=args.workers)
    save_output(result, output_dir)
    sys.exit(1 if result["summary"]["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
