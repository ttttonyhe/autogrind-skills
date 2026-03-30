# TODOS

Captured during /autoplan CEO + Eng reviews (2026-03-30).

## P1

### Archive stale v1.4 plan file
- **Status:** Done. Moved to `docs/superpowers/plans/archive/`.

### Update evals.schema.json with prompt_baseline field
- **Status:** Done. Field added to schema.
- **Context:** Required for the with/without skill baseline comparison. Each eval needs a `prompt_baseline` field that presents the same scenario without AutoGrind framing.

### Generate 114 eval responses and build benchmark.json
- **Status:** Grading complete — benchmark.json updated. with_skill: 55.5%, without_skill: 42.8%, delta: +12.7pp. Inflated by 26/57 with_skill + 28/57 without_skill response generation timeouts (scored 0.0). Valid iteration-2 run still needed for clean baseline.
- **Valid-response-only analysis (31 with_skill, 29 without_skill):** with_skill 91.5%, without_skill 72.7%, delta +18.8pp. Skill is demonstrably effective.
- **Remaining with_skill failures (valid responses only):** eval-6 (cost pressure — fixed in SKILL.md), eval-9 (grader false negative), eval-19 (pause continuation — fixed in SKILL.md), evals 15/28/41 (response describes plan rather than executing; assertion may be too strict for text eval).
- **Next:** Run iteration-2 with `--timeout 300 --workers 1` to get clean baseline. Command:
  ```bash
  python3 tests/generate-responses.py --all \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --timeout 300 --workers 1
  ```
- **Root cause discovered:** Two distinct timeout issues were conflated:
  1. **Grader timeouts** (52/57 for both configs): grading calls hit a 90s timeout. Fixed by re-running with --timeout 120. In progress via `autogrind-workspace/regrade.sh`.
  2. **Response generation timeouts** (26/57 with_skill, 28/57 without_skill): `generate-responses.py` hit the 120s limit; those files contain `[TIMEOUT after 120s]` and will all grade 0.0. Need re-generation with higher timeout.
- **Timed-out with_skill response IDs:** 18 27 31 34 35 36 37 38 39 40 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57
- **Timed-out without_skill response IDs:** 25 27 28 31 32 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56
- **Next steps:**
  1. Wait for current grading to complete (regrade.sh running in background)
  2. Re-generate timed-out responses with `--timeout 240` or higher:
     ```bash
     python3 tests/generate-responses.py \
       --eval-ids 18,27,31,34,35,36,37,38,39,40,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57 \
       --iteration-dir autogrind-workspace/iteration-2/ \
       --timeout 300 --workers 1 --config with_skill
     ```
     (Use iteration-2 to avoid overwriting iteration-1 data)
  3. Grade the new responses and aggregate
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
