#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
generate-responses.py — Generate agent responses for AutoGrind eval runs.

Spawns claude CLI sessions for each eval in with_skill and without_skill configs.
Saves responses and timing data to the workspace directory structure. For each eval,
also writes a flat copy to {iteration_dir}/{config}_responses/eval-{id}.txt so that
grade-evals.py --all --responses-dir can consume the results directly.

Usage:
  python3 tests/generate-responses.py --eval-ids 1,7,12,20,40 \
      --iteration-dir autogrind-workspace/iteration-1/
  python3 tests/generate-responses.py --all \
      --iteration-dir autogrind-workspace/iteration-1/
  python3 tests/generate-responses.py --all \
      --iteration-dir autogrind-workspace/iteration-2/ \
      --timeout 300 --workers 1
  python3 tests/generate-responses.py \
      --eval-ids 18,27,31,34 \
      --iteration-dir autogrind-workspace/iteration-2/ \
      --config with_skill --skip-existing --timeout 300 --workers 1

Options:
  --config {both,with_skill,without_skill}
                Run only one configuration instead of both (default: both).
  --skip-existing
                Skip any eval whose response file already contains a valid
                (non-timeout) response. Useful for resuming interrupted runs.
  --timeout SECONDS
                Per-eval timeout for the claude CLI call (default: 120s).
                Use 300+ for large skill prompts or slow network.
  --workers N   Parallel workers for response generation (default: 1).
                WARNING: parallel grading via grade-evals.py blocks the claude
                CLI internally — use --workers 1 for grading. Response generation
                can use higher values if rate limits allow.

Exit codes:
  0   All responses generated successfully (timeouts write sentinel and continue)
  2   Usage or environment error
"""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def load_skill() -> str:
    skill_path = Path(__file__).parent.parent / "SKILL.md"
    if not skill_path.exists():
        print(f"Error: SKILL.md not found at {skill_path}", file=sys.stderr)
        sys.exit(2)
    return skill_path.read_text()


def generate_response(prompt: str, skill_content: str | None, timeout: int) -> tuple[str, float]:
    """Run claude -p with the given prompt. Returns (response_text, duration_seconds)."""
    if skill_content:
        full_prompt = (
            "You are an AI coding agent with the following skill loaded. "
            "Follow the skill's instructions exactly.\n\n"
            f"<skill>\n{skill_content}\n</skill>\n\n"
            "Now respond to this scenario:\n\n"
            f"{prompt}"
        )
    else:
        full_prompt = (
            "You are an AI coding agent working on a software project. "
            "Respond to this scenario:\n\n"
            f"{prompt}"
        )

    start = time.time()
    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.time() - start
        if result.returncode != 0:
            stderr = result.stderr.strip()
            print(
                f"Warning: claude CLI returned exit code {result.returncode}"
                + (f": {stderr[:200]}" if stderr else ""),
                file=sys.stderr,
            )
        return result.stdout.strip(), duration
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return f"[TIMEOUT after {timeout}s]", duration
    except FileNotFoundError:
        print("Error: claude CLI not found", file=sys.stderr)
        sys.exit(2)


def run_eval(
    eval_case: dict,
    skill_content: str,
    iteration_dir: Path,
    timeout: int,
    configs: list[str] | None = None,
    skip_existing: bool = False,
) -> dict:
    """Generate with_skill and/or without_skill responses for a single eval."""
    eval_id = eval_case["id"]
    prompt = eval_case["prompt"]
    prompt_baseline = eval_case.get("prompt_baseline", prompt)

    all_configs = [
        ("with_skill", prompt, skill_content),
        ("without_skill", prompt_baseline, None),
    ]
    active_configs = [(c, p, s) for c, p, s in all_configs if configs is None or c in configs]

    results = {}

    for config, p, skill in active_configs:
        out_dir = iteration_dir / f"eval-{eval_id}" / config / "outputs"
        response_file = out_dir / "response.txt"

        if skip_existing and response_file.exists():
            existing = response_file.read_text()
            if not existing.startswith("[TIMEOUT"):
                print(f"  Eval {eval_id} [{config}]: skipping (valid response exists)", file=sys.stderr)
                results[config] = {"chars": len(existing), "skipped": True}
                continue

        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"  Eval {eval_id} [{config}]...", file=sys.stderr)
        response, duration = generate_response(p, skill, timeout)

        response_file.write_text(response)

        # Also write a flat copy for use with grade-evals.py --all --responses-dir
        flat_dir = iteration_dir / f"{config}_responses"
        flat_dir.mkdir(parents=True, exist_ok=True)
        (flat_dir / f"eval-{eval_id}.txt").write_text(response)

        timing = {"duration_s": round(duration, 1)}
        timing_path = iteration_dir / f"eval-{eval_id}" / config / "timing.json"
        timing_path.write_text(json.dumps(timing, indent=2))

        results[config] = {"chars": len(response), "duration_s": round(duration, 1)}

    return {"eval_id": eval_id, **results}


def main():
    parser = argparse.ArgumentParser(description="Generate agent responses for eval runs")
    parser.add_argument("--eval-ids", help="Comma-separated eval IDs (e.g., 1,7,12)")
    parser.add_argument("--all", action="store_true", help="Run all evals")
    parser.add_argument("--iteration-dir", required=True, help="Workspace iteration directory")
    parser.add_argument("--evals", default=str(Path(__file__).parent.parent / "evals" / "evals.json"))
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per response (default: 120s)")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers (default: 1)")
    parser.add_argument("--config", choices=["both", "with_skill", "without_skill"], default="both",
                        help="Which config to run (default: both)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip evals where a valid (non-timeout) response already exists")
    args = parser.parse_args()

    evals_data = json.loads(Path(args.evals).read_text())
    skill_content = load_skill()
    iteration_dir = Path(args.iteration_dir)

    if args.all:
        eval_cases = evals_data["evals"]
    elif args.eval_ids:
        ids = [int(x) for x in args.eval_ids.split(",")]
        eval_cases = [e for e in evals_data["evals"] if e["id"] in ids]
        missing = set(ids) - {e["id"] for e in eval_cases}
        if missing:
            print(f"Warning: eval IDs not found: {missing}", file=sys.stderr)
    else:
        print("Error: specify --all or --eval-ids", file=sys.stderr)
        sys.exit(2)

    configs = None if args.config == "both" else [args.config]
    skip = args.skip_existing
    print(f"Generating responses for {len(eval_cases)} evals (workers={args.workers}, config={args.config})...", file=sys.stderr)

    if args.workers > 1:
        all_results = []
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    run_eval, ec, skill_content, iteration_dir, args.timeout, configs, skip
                ): ec
                for ec in eval_cases
            }
            for future in as_completed(futures):
                all_results.append(future.result())
        all_results.sort(key=lambda r: r["eval_id"])
    else:
        all_results = []
        for ec in eval_cases:
            all_results.append(
                run_eval(ec, skill_content, iteration_dir, args.timeout, configs, skip)
            )

    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
