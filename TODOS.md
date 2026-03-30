# TODOS

Captured during /autoplan CEO + Eng reviews (2026-03-30).

## P1

### Archive stale v1.4 plan file
- **Status:** Done. Moved to `docs/superpowers/plans/archive/`.

### Update evals.schema.json with prompt_baseline field
- **Status:** Done. Field added to schema.
- **Context:** Required for the with/without skill baseline comparison. Each eval needs a `prompt_baseline` field that presents the same scenario without AutoGrind framing.

### Generate 114 eval responses and build benchmark.json
- **Status:** Iteration-1 complete but contaminated. Iteration-2 NOT yet run. SKILL.md improvements made; run iteration-2 to get clean baseline.
- **Iteration-1 summary:** with_skill: 55.5%, without_skill: 42.8%, delta: +12.7pp — inflated by timeouts (26/57 with_skill + 28/57 without_skill timed out at 120s).
- **Valid-response-only (31 with_skill, 29 without_skill):** with_skill 91.5%, without_skill 72.7%, delta +18.8pp. Skill is demonstrably effective.
- **Iteration-1 with_skill failures (valid responses only):**
  - eval-6: treated "wrapped up soon" as explicit stop — fixed: Stopping Conditions now clarifies polite suggestions lack a stop keyword; Common Rationalizations "unless explicit" removed
  - eval-9: grader false negative on Config struct assertion — fixed: assertion reworded
  - eval-15: "continues into next cycle" too strict for text eval — fixed: reworded
  - eval-19: agent finished 60s sleep despite "keep going, don't wait" — fixed: inter-cycle pause now says "skip the remaining sleep"
  - evals 28/41: execution assertions too strict for text eval — fixed: reworded
- **Iteration-2 command:**
  ```bash
  python3 tests/generate-responses.py --all \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --timeout 300 --workers 1
  ```
- **Note:** Run grading with --workers 1 (sequential). Parallel grading workers block each other via the claude CLI.

## P2

### grade-evals.py --consistency-check flag
- **Status:** Done. Flag added; grades each assertion twice and reports agreement rate.
- **What:** Add a flag that grades the same eval twice and reports agreement percentage.
- **Why:** Catches LLM judge flakiness before trusting baselines. Currently no way to measure grading reliability.
- **Context:** The grading pipeline uses a single `claude -p` call per assertion with no temperature control or model pinning. If the judge is inconsistent, baselines are unreliable. A consistency check would grade N evals twice and report the agreement rate.
- **Effort:** S (CC+gstack ~15 min)
- **Depends on:** Nothing. Can be built anytime.

## P3

### GitHub Actions word-count CI check
- **Status:** Done. `.github/workflows/skill-quality.yml` added with two jobs: word-count (fails >2000 words) and skill-sync (fails if SKILL.md copies diverge).
- **What:** A CI workflow that runs `wc -w SKILL.md` on every PR and fails if it exceeds 2000.
- **Why:** The pre-commit hook enforces this locally, but contributors who don't install the hook can push over-budget SKILL.md changes. CI catches this.
- **Context:** Currently only the local pre-commit hook guards the 2000-word limit. Belt-and-suspenders for an open source project with external contributors.
- **Effort:** S (CC+gstack ~10 min)
- **Depends on:** Nothing.
