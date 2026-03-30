# TODOS

Captured during /autoplan CEO + Eng reviews (2026-03-30).

## P1

### Archive stale v1.4 plan file
- **Status:** Done. Moved to `docs/superpowers/plans/archive/`.

### Update evals.schema.json with prompt_baseline field
- **Status:** Done. Field added to schema.
- **Context:** Required for the with/without skill baseline comparison. Each eval needs a `prompt_baseline` field that presents the same scenario without AutoGrind framing.

### Generate 114 eval responses and build benchmark.json
- **Status:** In progress. 113/114 responses generated (eval 57 with_skill timed out due to daily API token limit). Grading and aggregation pending API limit reset.
- **Context:** Run `python3 tests/generate-responses.py --eval-ids 57 --iteration-dir autogrind-workspace/iteration-1/` to fill the gap, then grade with `python3 tests/grade-evals.py --all --workers 10` for both configs, then `python3 tests/aggregate-benchmark.py` to produce benchmark.json.
- **Depends on:** Daily API token limit reset.

## P2

### grade-evals.py --consistency-check flag
- **What:** Add a flag that grades the same eval twice and reports agreement percentage.
- **Why:** Catches LLM judge flakiness before trusting baselines. Currently no way to measure grading reliability.
- **Context:** The grading pipeline uses a single `claude -p` call per assertion with no temperature control or model pinning. If the judge is inconsistent, baselines are unreliable. A consistency check would grade N evals twice and report the agreement rate.
- **Effort:** S (CC+gstack ~15 min)
- **Depends on:** Nothing. Can be built anytime.

## P3

### GitHub Actions word-count CI check
- **What:** A CI workflow that runs `wc -w SKILL.md` on every PR and fails if it exceeds 2000.
- **Why:** The pre-commit hook enforces this locally, but contributors who don't install the hook can push over-budget SKILL.md changes. CI catches this.
- **Context:** Currently only the local pre-commit hook guards the 2000-word limit. Belt-and-suspenders for an open source project with external contributors.
- **Effort:** S (CC+gstack ~10 min)
- **Depends on:** Nothing.
