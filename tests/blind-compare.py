#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
blind-compare.py — Blind holistic quality comparison between two agent responses.

Presents two responses to an LLM judge without revealing which came from which
configuration (with_skill vs without_skill). The judge scores holistic output
qualities — organization, completeness, correctness, and usability — and
declares a winner. Complements assertion grading (grade-evals.py) with
subjective quality measurement.

Usage:
  python3 tests/blind-compare.py --response-a FILE --response-b FILE [--eval-id N] [--output FILE]
  python3 tests/blind-compare.py --all --iteration-dir DIR [--output FILE]

In --all mode, compares with_skill vs without_skill for every eval in the iteration
directory (A=with_skill, B=without_skill). Skips evals missing either response.

The assignment of A/B to with_skill/without_skill is intentionally opaque to
the judge. Record the mapping externally so you can interpret the result.

Exit codes:
  0   Comparison completed successfully
  2   Usage or environment error

Requires: claude CLI (https://claude.ai/code)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


JUDGE_PROMPT_TEMPLATE = """\
You are an impartial judge comparing two agent responses to the same task.

Task prompt:
{task_prompt}

---
Response A:
{response_a}

---
Response B:
{response_b}

---

Score each response on these four dimensions (1–5 each):
- **Correctness**: Does the response address the core of the task correctly?
- **Completeness**: Does it cover all relevant aspects without omissions?
- **Organization**: Is it clear, well-structured, and easy to follow?
- **Usability**: Would the response be practically useful if acted on?

Then declare an overall winner (A, B, or TIE) with one sentence explaining why.

Reply with exactly this JSON format:
{{
  "scores": {{
    "A": {{"correctness": N, "completeness": N, "organization": N, "usability": N}},
    "B": {{"correctness": N, "completeness": N, "organization": N, "usability": N}}
  }},
  "winner": "A" | "B" | "TIE",
  "reasoning": "one sentence"
}}
"""


def run_blind_comparison(
    response_a: str,
    response_b: str,
    task_prompt: str,
    timeout: int = 120,
) -> dict:
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        task_prompt=task_prompt,
        response_a=response_a,
        response_b=response_b,
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            print(
                f"Warning: claude CLI returned exit code {result.returncode}"
                + (f": {stderr[:120]}" if stderr else ""),
                file=sys.stderr,
            )
            return {"parse_error": f"judge call failed (exit {result.returncode})"}
        output = result.stdout.strip()
    except FileNotFoundError:
        print(
            "Error: claude CLI not found. Install from https://claude.ai/code",
            file=sys.stderr,
        )
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print(f"Error: comparison timed out after {timeout}s", file=sys.stderr)
        sys.exit(2)

    # Extract JSON from the response
    start = output.find("{")
    end = output.rfind("}") + 1
    if start == -1 or end == 0:
        return {"raw_output": output, "parse_error": "could not extract JSON"}

    try:
        parsed = json.loads(output[start:end])
        scores_a = parsed.get("scores", {}).get("A", {})
        scores_b = parsed.get("scores", {}).get("B", {})
        total_a = sum(scores_a.values()) if scores_a else 0
        total_b = sum(scores_b.values()) if scores_b else 0
        parsed["totals"] = {"A": total_a, "B": total_b}
        return parsed
    except json.JSONDecodeError:
        return {"raw_output": output[start:end], "parse_error": "invalid JSON from judge"}


def main():
    parser = argparse.ArgumentParser(
        prog="blind-compare.py",
        description="Blind holistic quality comparison between two agent responses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 tests/blind-compare.py \\\n"
            "      --response-a iteration-1/eval-1/with_skill/outputs/response.txt \\\n"
            "      --response-b iteration-1/eval-1/without_skill/outputs/response.txt \\\n"
            "      --eval-id 1\n"
            "  python3 tests/blind-compare.py --all \\\n"
            "      --iteration-dir autogrind-workspace/iteration-1/ \\\n"
            "      --output autogrind-workspace/iteration-1/blind_compare.json\n\n"
            "The judge does not know which response is A or B. In --all mode,\n"
            "A=with_skill and B=without_skill for every eval.\n\n"
            "Output is JSON printed to stdout. Use --output to also save to a file."
        ),
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Compare with_skill vs without_skill for all evals in --iteration-dir (A=with_skill, B=without_skill)",
    )
    parser.add_argument(
        "--iteration-dir", metavar="DIR",
        help="Iteration directory for --all mode (e.g., autogrind-workspace/iteration-1/)",
    )
    parser.add_argument(
        "--response-a", metavar="FILE",
        help="Path to the first response file (single-eval mode)",
    )
    parser.add_argument(
        "--response-b", metavar="FILE",
        help="Path to the second response file (single-eval mode)",
    )
    parser.add_argument(
        "--eval-id", type=int, metavar="N",
        help="Eval ID to use as the task prompt (looks up prompt from evals/evals.json)",
    )
    parser.add_argument(
        "--task-prompt", metavar="TEXT",
        help="Task prompt text (alternative to --eval-id)",
    )
    parser.add_argument(
        "--evals",
        default=str(Path(__file__).parent.parent / "evals" / "evals.json"),
        metavar="FILE",
        help="Path to evals.json (default: ../evals/evals.json relative to this script)",
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Path to save the comparison result JSON (also printed to stdout)",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, metavar="SECONDS",
        help="Timeout in seconds for the judge call (default: 120)",
    )
    args = parser.parse_args()

    evals_path = Path(args.evals)
    evals_data = json.loads(evals_path.read_text()) if evals_path.exists() else None

    if args.all:
        if not args.iteration_dir:
            print("Error: --iteration-dir is required with --all", file=sys.stderr)
            sys.exit(2)
        iteration_dir = Path(args.iteration_dir)
        if not iteration_dir.is_dir():
            print(f"Error: iteration directory not found: {args.iteration_dir}", file=sys.stderr)
            sys.exit(2)

        eval_dirs = sorted(iteration_dir.glob("eval-*"), key=lambda p: int(p.name.split("-")[1]))
        results = []
        for eval_dir in eval_dirs:
            path_a = eval_dir / "with_skill" / "outputs" / "response.txt"
            path_b = eval_dir / "without_skill" / "outputs" / "response.txt"
            if not path_a.exists() or not path_b.exists():
                print(f"Skipping {eval_dir.name}: missing response file(s)", file=sys.stderr)
                continue
            eval_id = int(eval_dir.name.split("-")[1])
            task_prompt = None
            if evals_data:
                eval_case = next((e for e in evals_data["evals"] if e["id"] == eval_id), None)
                if eval_case:
                    task_prompt = eval_case["prompt"]
            if not task_prompt:
                print(f"Skipping {eval_dir.name}: eval ID {eval_id} not in evals.json", file=sys.stderr)
                continue
            print(f"Comparing eval-{eval_id}...", file=sys.stderr)
            result = run_blind_comparison(path_a.read_text(), path_b.read_text(), task_prompt, timeout=args.timeout)
            result["eval_id"] = eval_id
            result["mapping"] = {"A": "with_skill", "B": "without_skill"}
            results.append(result)

        winners = [r.get("winner") for r in results if "winner" in r]
        summary = {
            "total": len(results),
            "A_wins": winners.count("A"),
            "B_wins": winners.count("B"),
            "ties": winners.count("TIE"),
            "errors": len(results) - len(winners),
            "mapping": {"A": "with_skill", "B": "without_skill"},
        }
        batch_result = {"results": results, "summary": summary}
        json_str = json.dumps(batch_result, indent=2)
        print(json_str)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_str)
            print(f"Saved to {args.output}", file=sys.stderr)
        return

    # Single-eval mode
    if not args.response_a or not args.response_b:
        print("Error: --response-a and --response-b are required (or use --all with --iteration-dir)", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(2)

    if not args.eval_id and not args.task_prompt:
        print("Error: either --eval-id or --task-prompt is required", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(2)

    path_a = Path(args.response_a)
    path_b = Path(args.response_b)
    for path, label in [(path_a, "--response-a"), (path_b, "--response-b")]:
        if not path.exists():
            print(f"Error: response file not found ({label}): {path}", file=sys.stderr)
            sys.exit(2)

    task_prompt = args.task_prompt
    if args.eval_id:
        if not evals_path.exists():
            print(f"Error: evals file not found: {args.evals}", file=sys.stderr)
            sys.exit(2)
        if evals_data is None:
            evals_data = json.loads(evals_path.read_text())
        eval_case = next((e for e in evals_data["evals"] if e["id"] == args.eval_id), None)
        if eval_case is None:
            ids = [e["id"] for e in evals_data["evals"]]
            print(f"Error: eval ID {args.eval_id} not found. Available: {ids}", file=sys.stderr)
            sys.exit(2)
        task_prompt = eval_case["prompt"]

    response_a = path_a.read_text()
    response_b = path_b.read_text()

    print(f"Running blind comparison (A={args.response_a}, B={args.response_b})...", file=sys.stderr)
    result = run_blind_comparison(response_a, response_b, task_prompt, timeout=args.timeout)
    result["mapping"] = {"A": str(path_a), "B": str(path_b)}

    json_str = json.dumps(result, indent=2)
    print(json_str)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_str)
        print(f"Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
