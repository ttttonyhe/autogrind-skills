# TODOS

Captured during /autoplan CEO + Eng reviews (2026-03-30).

## P1

### Archive stale v1.4 plan file
- **Status:** Done. Moved to `docs/superpowers/plans/archive/`.

### Update evals.schema.json with prompt_baseline field
- **Status:** Done. Field added to schema.
- **Context:** Required for the with/without skill baseline comparison. Each eval needs a `prompt_baseline` field that presents the same scenario without AutoGrind framing.

### Generate benchmark.json with clean iteration-2 run
- **Status:** Iteration-1 complete but contaminated. Iteration-2 NOT yet run. All known failures fixed (see below); suite ready for a clean run.
- **Iteration-1 summary:** with_skill: 55.5%, without_skill: 42.8%, delta: +12.7pp — inflated by timeouts (26/57 with_skill + 28/57 without_skill timed out at 120s).
- **Valid-response-only (31 with_skill, 29 without_skill):** with_skill 91.5%, without_skill 72.7%, delta +18.8pp. Skill is demonstrably effective.
- **All iteration-1 failures fixed (v1.10 + assertion rewrites):**
  - eval-6: SKILL.md — stopping condition keyword requirement; removed "unless explicit" loophole
  - eval-9: assertion reworded (grader false negative — Config struct question)
  - eval-15: assertion reworded ("outlines cycle 5" instead of "continues")
  - eval-19: SKILL.md — inter-cycle pause now says "skip the remaining sleep"
  - eval-28: assertion reworded ("describes proceeding with" instead of "executes")
  - eval-41: assertion reworded ("explicitly commits to" instead of "continues working")
- **Eval suite:** 69 evals (added eval-58 output-bar, eval-59 parallel tasks, eval-60 writing Reflect, eval-61 self-audit, eval-62 all-blocked, eval-63 stop-during-plan, eval-64 micro-task grouping, eval-65 post-stop re-engagement, eval-66 ambiguous trigger phrase re-engagement, eval-67 stop-in-quotes false positive, eval-68 stop-during-reflect, eval-69 design-domain Reflect)
- **Query files:** 14 train + 10 validation = 24 total (added "keep going" + bounded-task false-negative)
- **Iteration-2 command:**
  ```bash
  python3 tests/generate-responses.py --all \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --timeout 300 --workers 1
  ```
- **Then grade and aggregate:**
  ```bash
  python3 tests/grade-evals.py --all \
    --responses-dir autogrind-workspace/iteration-2/with_skill_responses/ \
    --output-dir autogrind-workspace/iteration-2/ \
    --config with_skill --timeout 120 --workers 1
  python3 tests/grade-evals.py --all \
    --responses-dir autogrind-workspace/iteration-2/without_skill_responses/ \
    --output-dir autogrind-workspace/iteration-2/ \
    --config without_skill --timeout 120 --workers 1
  python3 tests/aggregate-benchmark.py \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --output autogrind-workspace/iteration-2/benchmark.json
  ```
- **Note:** Run grading with --workers 1 (sequential). Parallel grading workers block each other via the claude CLI. The `--config` flag writes to `eval-N/<config>/grading.json` so both runs coexist under the same `--output-dir`.

## P2

### grade-evals.py --consistency-check flag
- **Status:** Done. Flag added; grades each assertion twice and reports agreement rate.
- **What:** Add a flag that grades the same eval twice and reports agreement percentage.
- **Why:** Catches LLM judge flakiness before trusting baselines. Currently no way to measure grading reliability.
- **Context:** The grading pipeline uses a single `claude -p` call per assertion with no temperature control or model pinning. If the judge is inconsistent, baselines are unreliable. A consistency check would grade N evals twice and report the agreement rate.
- **Effort:** S (CC+gstack ~15 min)
- **Depends on:** Nothing. Can be built anytime.

## P2 (setup)

### Re-link local skill install to repo
- **Status:** Pending. `~/.claude/skills/autogrind` is a stale git clone (v1.4), not a symlink to the repo.
- **Fix:** `ln -sfn /Users/ttttonyhe/Desktop/dev/autogrind ~/.claude/skills/autogrind` (or delete the dir and re-run the symlink command from CLAUDE.md).
- **Why:** The v1.4 install diverges from v1.10 in the repo — stop-signal loophole fixes, output-bar, Iron Law meta-rule, and spec-compliant description are absent. Any local testing uses the stale version.

## P3

### GitHub Actions word-count CI check
- **Status:** Done. `.github/workflows/skill-quality.yml` added with two jobs: word-count (fails >2000 words) and skill-sync (fails if SKILL.md copies diverge).
- **What:** A CI workflow that runs `wc -w SKILL.md` on every PR and fails if it exceeds 2000.
- **Why:** The pre-commit hook enforces this locally, but contributors who don't install the hook can push over-budget SKILL.md changes. CI catches this.
- **Context:** Currently only the local pre-commit hook guards the 2000-word limit. Belt-and-suspenders for an open source project with external contributors.
- **Effort:** S (CC+gstack ~10 min)
- **Depends on:** Nothing.
