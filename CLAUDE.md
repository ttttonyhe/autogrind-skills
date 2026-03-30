# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository contains the **AutoGrind** skill - a cross-agent autonomous development skill that directs an AI coding agent to work continuously on a project without stopping. The agent follows a cyclic grind loop (Overview → Understand → Plan → Work → Reflect → repeat) and never terminates unless the user explicitly says to stop.

## Skill File Format

The repo root IS the skill package — `SKILL.md` lives at the root to satisfy the AgentSkills spec. Agents discover it by symlinking or cloning the repo root directly into their skills directory.

## Plugin Structure

The repo root stays skill-first, but Codex marketplace discovery points at a dedicated plugin
bundle under `plugins/autogrind/`. This keeps the repository centered on the raw skill while
matching the `./plugins/<name>` layout used by Codex's built-in marketplaces.

```
autogrind/           (repo root = skill root)
├── SKILL.md                        # agentskills.io root (must match skills/autogrind/SKILL.md)
├── .claude-plugin/
│   ├── plugin.json                 # Claude Code plugin manifest
│   └── marketplace.json            # Claude Code marketplace catalog
├── .agents/plugins/marketplace.json # Codex repo marketplace catalog -> plugins/autogrind
├── skills/autogrind/SKILL.md       # plugin-format skill copy
├── commands/start.md           # /autogrind slash command
├── plugins/
│   └── autogrind/
│       ├── .codex-plugin/plugin.json
│       ├── skills/autogrind/SKILL.md
│       ├── commands/start.md
│       └── assets/
└── PLUGIN.md                       # plugin installation guide
```

Both native plugins are complements to the core skill package. Do not restructure the repo unless explicitly requested.

### SKILL.md sync rule

`SKILL.md`, `skills/autogrind/SKILL.md`, and `plugins/autogrind/skills/autogrind/SKILL.md`
must always be identical. The pre-commit hook (`.git/hooks/pre-commit`) also enforces sync
between the root and marketplace copies of `commands/start.md`.

### Version bumping

When making significant skill changes, bump `metadata.version` in `SKILL.md`
(and therefore in both copied skill files) **and** bump `"version"` in
`.claude-plugin/plugin.json` and `plugins/autogrind/.codex-plugin/plugin.json`.
All five must stay in sync.

### SKILL.md Frontmatter

```yaml
---
name: autogrind
description: Engage in [action] — [what it does]. [domain scope]. [trigger phrases].
license: MIT
compatibility: Designed for Claude Code (or similar products)
metadata:
  author: ttttonyhe
  version: "1.x"
---
```

Rules:
- `name`: letters, numbers, hyphens only
- `description`: **write as an action sentence** (e.g., "Engage in 24x7 auto-work mode — ..."); do not start with "Use when...". ≤500 chars. Must convey what the skill does and include trigger phrases (e.g., `/autogrind`, `keep working don't stop`) for agent discovery per agentskills.io guidelines. Exclude workflow details — description is for discovery, not docs.
- `license`: must match the repo LICENSE file (currently MIT)
- `compatibility`: brief compatibility statement — e.g. "Designed for Claude Code (or similar products)"
- `metadata.version`: bump when making significant changes to skill logic
- Total frontmatter ≤ 1024 characters
- Validate with `npx skills-ref validate skills/autogrind` before committing

## Skill Design Goals

AutoGrind is a **discipline-enforcing skill** (rigid type). The primary invariant: **the agent must never stop on its own accord.** Key behaviors to enforce:

1. **Perpetual operation** - a completed TODO list, "everything looks good", or end-of-cycle are not stopping conditions
2. **Self-directed discovery** - after completing current tasks, autonomously identify new areas to improve (tests, performance, UX, docs, refactoring, edge cases, experiment coverage)
3. **Cyclic workflow** - each cycle: Overview → Understand → Plan → Work → Reflect → 60s inter-cycle pause → back to Overview
4. **Cross-domain** - the skill must work for any long-running workflow: software, ML/data science, academic research, design, writing. Language should be domain-agnostic; phases should adapt to the domain.
5. **Guidance file detection** - on first run, scan for `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `opencode.md`, `README.md` to extract project context
6. **Explicit stop only** - terminate only when user sends an explicit stop signal (never infer it)
7. **Core deliverable focus** - each cycle must produce at least one improvement to the primary output (the skill, model, paper, design, feature). Scaffolding work alone (tests, tooling, CI) does not count as a cycle's main contribution.

## Cross-Agent Compatibility

The skill must be usable across all major coding agents. All agents except Claude Code discover skills from `~/.agents/skills/` per the agentskills.io universal path:

| Agent | Skill loading mechanism | Task tracking |
|-------|------------------------|---------------|
| Claude Code | `Skill` tool | `TaskCreate` / `TaskUpdate` |
| Codex | Auto-discovered skills or bundled plugin skills | Native task tools |
| Gemini CLI | GEMINI.md conventions | Native task tools |
| OpenCode | AGENTS.md conventions | Native task tools |
| Cursor | `.cursorrules` or explicit load | File-based notes |
| Windsurf | `~/.codeium/windsurf/skills/` or `~/.agents/skills/` | Native task tools |
| Roocode | `~/.roo/skills/` or `~/.agents/skills/` | Native task tools |
| Cline | `~/.cline/skills/` or `~/.agents/skills/` | Native task tools |
| Trae | `~/.trae/skills/` or `~/.agents/skills/` | Native task tools |
| Kimi Code | `~/.config/agents/skills/` or `.kimi/skills/` | `/skill:autogrind` |
| GitHub Copilot | `~/.copilot/skills/` or `~/.agents/skills/` | Native task tools |
| Goose | `~/.agents/skills/` | Native task tools |
| AmpCode | `~/.config/agents/skills/` or `~/.agents/skills/` | Native task tools |
| Junie | `~/.junie/skills/` or `~/.agents/skills/` | Native task tools |
| Kilo / Kiro / Factory | `~/.agents/skills/` | Native task tools |
| Hermes Agent (NousResearch) | `~/.agents/skills/` | Native task tools |
| All others | `~/.agents/skills/` | Native task tools |

Write platform-agnostic instructions where possible; provide explicit platform alternatives where divergence is necessary. The SKILL.md Platform Notes table has a concise subset of this table (agents with unique loading paths or invocation methods); this table is the complete reference.

## Research Foundation

AutoGrind's design is grounded in findings from top-tier AI/ML research. When modifying the skill, any change that weakens a research-backed mechanism requires explicit justification.

### Self-Reflection

| Paper | Key finding | Mechanism in SKILL.md |
|---|---|---|
| **Reflexion** (NeurIPS 2023) | Verbal RL with episodic memory enables iterative improvement — but only when grounded in verifiable feedback | Reflect phase anchors assessment to execution signals before self-evaluation |
| **CRITIC** (ICLR 2024) | External signals always outperform intrinsic self-critique; no paper shows pure intrinsic correction succeeding reliably | Phase 5, Step 1: verifiable signals checked first (test results, build status, metrics) |
| **IoRT** (2025) | Static reflection loops produce three failure modes: *redundant* (same critique every cycle), *drift* (abandoning correct paths), *stubborn* (ignoring valid feedback) | Cross-cycle pattern check (Phase 5, Step 4): Refresh when same dimension is flagged with no progress |
| **ERL** (ICLR 2026 workshop) | Abstract heuristics transfer across tasks better than specific trajectory memories | Session Heuristics: one `When <condition>, prefer <approach> because <reason>` principle extracted per cycle |
| **SAMULE** (2025) | Multi-level reflection (micro → meso → macro) outperforms single-level self-critique | Five-step Reflect: immediate signals → mandatory questions → dimension scan → cross-cycle check → heuristic |

### Planning and Self-Direction

| Paper | Key finding | Mechanism in SKILL.md |
|---|---|---|
| **Voyager** (2023) | Automatic curriculum is the single most critical component (–93% without it); mechanism is "capability frontier" — novel, achievable tasks at the edge of what's been done | Capability frontier scan in Phase 3: 1–2 frontier tasks after priority list |
| **LLMCompiler** (ICML 2024) | Parallel execution of independent tasks: 3.7× faster, +9% accuracy | Phase 4: independent tasks run concurrently where platform supports it |
| **AOP** (ICLR 2025) | Solvability gate before task assignment is the most critical planning step | Solvability gate in Phase 3: verify each task actionable before finalizing |
| **Generative Agents** (2023) | Importance-weighted retrieval outperforms flat recall | Phase 1 lag rating: each area rated high/medium/low to feed Plan prioritization |
| **AOP companion / ToT** | Plans exceeding ~4 steps degrade execution reliability significantly | Each task capped at ≤ 4 steps |
| **FixedCode** (SRI ETH, 2025) | Coding agents have unnecessary action bias — they produce patches even when code is already correct, because they skip pre-task verification; success correlates with resisting nonsensical requests, not coding ability | Solvability gate: fix-type tasks check git history to confirm the problem still exists; Phase 4 per-task verify step: reproduce the problem before coding — no change is the correct output when the issue is already resolved |

## Grind Loop Architecture

```
[Init - once]
  Detect guidance files → extract project overview & goals

[Grind cycle - repeats until explicit stop]
  1. Overview  - assess current project state (files, tests, CI, open issues)
  2. Understand - read relevant code, recent commits, existing TODOs
  3. Plan      - generate prioritized, actionable tasks for this cycle
  4. Work      - execute each task (implement, test, commit)
  5. Reflect   - evaluate output quality, identify gaps, seed next cycle
  └──────────────────────────────────────────────────────────────┘
```

The reflect phase must always produce at least one focus area for the next cycle. If genuinely nothing is broken, target polish, coverage, performance, or documentation.

## Key Invariants

- `todos_done == true` is never a stopping condition
- `"project looks complete"` is never a stopping condition
- Every cycle must produce at least one concrete change to the PRIMARY DELIVERABLE (not just scaffolding)
- The skill should handle both greenfield projects and mature codebases, across any domain
- Each cycle ends with a 60-second inter-cycle pause before the next Overview begins
- Never ask the user for guidance mid-cycle unless truly blocked (missing credentials, ambiguous spec, broken environment)
- When tests/validations fail: improve the implementation first. Modifying evaluators to pass without improving the implementation is not a fix.
- **Reflect must check verifiable signals before self-assessment** (CRITIC): grounding reflection in execution evidence is non-negotiable
- **Plan must include a capability frontier scan** (Voyager): without self-directed task generation, autonomous agents lose the majority of their effectiveness
- **Stuck loops must be detected and refreshed** (IoRT): repeating the same reflection on the same stuck dimension is not progress — shift dimensions
- **Session Heuristics are in-context only** (ERL): they are lost on context compaction; reinitialize to empty and continue — they are a convenience, not a dependency
- **Output bar** (v1.9): at least one task per cycle must be discovered, not listed — a problem not on any TODO, a non-obvious improvement, or a deeper solution. If all tasks were pre-listed, the frontier scan runs at higher ambition.

## Local Development

### Validate skill structure

```bash
# Validate against agentskills.io spec
npx skills-ref validate skills/autogrind

# Check frontmatter
head -12 SKILL.md

# Keep word count reasonable - frequently invoked skills should stay under 2000 words
wc -w SKILL.md
```

### Install locally for testing

```bash
# Claude Code (live-editing symlink from repo root)
ln -sfn $(pwd) ~/.claude/skills/autogrind

# Or clone directly to skills location
git clone --depth 1 https://github.com/ttttonyhe/autogrind.git ~/.claude/skills/autogrind
```

### Grading evals

`tests/grade-evals.py` grades evals.json assertions against an agent response using the claude CLI. It outputs `grading.json` format per the agentskills.io spec:

```bash
# Grade a single eval (prints grading.json to stdout)
python3 tests/grade-evals.py --response <response-file> --eval-id <N>

# Grade and save grading.json into workspace directory
python3 tests/grade-evals.py --response out.txt --eval-id 1 \
    --output-dir autogrind-workspace/iteration-1/eval-1/with_skill

# Grade all evals at once (responses-dir must contain eval-<N>.txt files)
python3 tests/grade-evals.py --all --responses-dir <dir> \
    --output-dir autogrind-workspace/iteration-1/

# Speed up batch grading with parallel workers (5-10 recommended)
python3 tests/grade-evals.py --all --responses-dir <dir> --workers 8
```

Exit codes: `0` all pass, `1` some fail, `2` usage error. Requires the claude CLI. PEP 723 compatible — no external dependencies. Use `--timeout SECONDS` (default 60) for slow model responses; `--workers N` to parallelize (default 1, sequential). Use `--consistency-check` to grade each assertion twice and report agreement rate (measures LLM judge reliability).

`tests/blind-compare.py` runs a blind holistic quality comparison between two responses using an LLM judge. Complements assertion grading with subjective quality measurement (organization, completeness, correctness, usability):

```bash
python3 tests/blind-compare.py \
    --response-a iteration-1/eval-1/with_skill/outputs/response.txt \
    --response-b iteration-1/eval-1/without_skill/outputs/response.txt \
    --eval-id 1

# Batch mode: compare all evals in an iteration (A=with_skill, B=without_skill)
python3 tests/blind-compare.py --all \
    --iteration-dir autogrind-workspace/iteration-1/ \
    --output autogrind-workspace/iteration-1/blind_compare.json
```

`tests/aggregate-benchmark.py` aggregates all `grading.json` and `timing.json` files from an iteration directory into a `benchmark.json`:

```bash
python3 tests/aggregate-benchmark.py \
    --iteration-dir autogrind-workspace/iteration-1/ \
    --output autogrind-workspace/iteration-1/benchmark.json
```

`tests/analyze-failures.py` classifies per-eval pass/fail patterns after aggregation to identify which evals discriminate well, which always pass or always fail, and what needs attention before the next iteration:

```bash
python3 tests/analyze-failures.py \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --output autogrind-workspace/iteration-2/failure_analysis.json
```

Categories: `strong_discriminator` (passes with skill, fails without — skill is working), `both_pass` (not measuring skill value — consider removing or strengthening), `both_fail` (assertion broken or too hard — fix before next iteration), `weak_discriminator` (inconclusive).

### Primary test format: evals.json

The primary test artifact is `evals/evals.json`, following the [agentskills.io evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills) standard. It contains 69 eval cases covering all documented failure modes and behavioral invariants across all AutoGrind domains and pressure categories.

The `evals/` directory lives at the repo root only — it is not copied into skill or plugin subdirectories.

```
evals/
├── evals.json              # Output quality evals (69 cases)
├── train_queries.json      # Description trigger queries — training set (14 queries, 60%)
└── validation_queries.json # Description trigger queries — validation set (10 queries, 40%)
```

Each eval has: `id`, `prompt` (realistic scenario description), `expected_output` (success description), `assertions` (verifiable pass/fail statements).

`train_queries.json` and `validation_queries.json` follow the [agentskills.io optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) format: flat arrays of `{"query": "...", "should_trigger": true/false}` objects. The two sets are non-overlapping with proportional balance. Use train failures to guide description changes; use validation only to verify generalization.

### Full eval workflow

The agentskills.io spec defines a complete eval loop: run → grade → aggregate → analyze → review → iterate.

**1. Workspace structure** — each iteration gets its own directory:

```
autogrind-workspace/
└── iteration-1/
    ├── eval-<N>/
    │   ├── with_skill/
    │   │   ├── outputs/       # Agent response file(s)
    │   │   ├── timing.json    # {"duration_s": N} (auto-generated); also accepts {"total_tokens": N, "duration_ms": N}
    │   │   └── grading.json   # Assertion results (from grade-evals.py)
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── feedback.json          # Human reviewer notes per eval
    └── benchmark.json         # Aggregated statistics
```

**2. Spawning runs** — each eval runs twice (with skill and without). Use `tests/generate-responses.py` for automated batch generation, or isolated subagent sessions for manual runs:

```bash
# Automated batch generation (writes to eval-N/{config}/outputs/response.txt and flat {config}_responses/ dirs)
python3 tests/generate-responses.py --all \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --timeout 300 --workers 1

# Re-generate only timed-out responses (skips valid existing ones)
python3 tests/generate-responses.py --eval-ids 18,27,31 \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --config with_skill --timeout 300 --skip-existing
```

Manual instruction template for a single run (use when generate-responses.py is unavailable):

```
Execute this task:
- Skill path: ~/.claude/skills/autogrind   (omit for without_skill run)
- Task: <paste the eval prompt from evals/evals.json>
- Save your full response to: autogrind-workspace/iteration-1/eval-<N>/{with_skill|without_skill}/outputs/response.txt
- Record token count and duration in: autogrind-workspace/iteration-1/eval-<N>/{with_skill|without_skill}/timing.json
```

**3. Grading** — use `tests/grade-evals.py`:

```bash
# Single eval (save to workspace)
python3 tests/grade-evals.py --response outputs/response.txt --eval-id <N> \
    --output-dir autogrind-workspace/iteration-1/eval-<N>/with_skill

# All evals at once — use --config to avoid overwriting both configs' results
python3 tests/grade-evals.py --all \
    --responses-dir autogrind-workspace/iteration-1/with_skill_responses/ \
    --output-dir autogrind-workspace/iteration-1/ --config with_skill
python3 tests/grade-evals.py --all \
    --responses-dir autogrind-workspace/iteration-1/without_skill_responses/ \
    --output-dir autogrind-workspace/iteration-1/ --config without_skill
```

**4. Aggregation** — use `tests/aggregate-benchmark.py`:

```bash
python3 tests/aggregate-benchmark.py \
    --iteration-dir autogrind-workspace/iteration-1/ \
    --output autogrind-workspace/iteration-1/benchmark.json
```

**5. benchmark.json format**:

```json
{
  "run_summary": {
    "with_skill":    {"eval_count": 57, "pass_rate": {"mean": 0.83, "stddev": 0.06}, "tokens": {"mean": 3800, "stddev": 320}, "time_seconds": {"mean": 12.5, "stddev": 2.1}},
    "without_skill": {"eval_count": 57, "pass_rate": {"mean": 0.33, "stddev": 0.10}, "tokens": {"mean": 2100, "stddev": 210}, "time_seconds": {"mean": 8.3, "stddev": 1.4}},
    "delta":         {"pass_rate": 0.50, "tokens": 1700, "time_seconds": 4.2}
  }
}
```

`eval_count` is the number of evals with a grading.json for that config. If it differs from the number of eval-* directories, some runs are missing results.

**6. Analysis** — use `tests/analyze-failures.py` to classify evals automatically, then inspect the output for patterns:

```bash
python3 tests/analyze-failures.py \
    --iteration-dir autogrind-workspace/iteration-2/ \
    --output autogrind-workspace/iteration-2/failure_analysis.json
```

- `strong_discriminator` evals → skill is working here; these validate the skill
- `both_pass` evals → not measuring skill value; consider removing or strengthening assertions
- `both_fail` evals → broken assertion or scenario too hard; fix before next iteration
- `weak_discriminator` evals → inconclusive; review agent outputs manually
- High stddev in benchmark → instructions may be ambiguous; add examples to SKILL.md

**7. Human review (feedback.json)** — after each iteration, review the actual agent outputs alongside the grades and record specific, actionable feedback:

```json
{
  "eval-1": "Agent correctly continued but didn't mention the capability frontier scan.",
  "eval-7": "",
  "eval-14": "Agent stopped correctly. Empty feedback = output looked correct."
}
```

Empty feedback means the output passed review. Focus iteration improvements on evals with specific complaints.

**8. Iteration** — give failed assertions, feedback.json, and current SKILL.md to an LLM and ask it to propose improvements. Guidelines:
- Generalize from specific cases — fixes should address the underlying issue, not patch individual examples
- Keep the skill lean — fewer, better instructions outperform exhaustive rules
- Explain the why — reasoning-based instructions work better than rigid directives
- When plateauing, try removing instructions and checking if results hold

Rerun all evals in a new `iteration-N+1/` directory after each change.

**Critical principle**: when evals fail, first ask whether **SKILL.md** needs improvement. Fix the skill before modifying assertions. Assertions change only when genuinely misclassifying correct behavior.

### Testing methodology

Test with pressure scenarios before finalizing skill changes. The 69 evals in `evals/evals.json` cover all documented failure modes across nine categories:

**Stop-signal recognition:**
- **True stop**: "Stop. I need to take this myself." — skill must halt
- **Retracted stop**: "Stop... wait, keep going" — skill must continue (final instruction wins)
- **Stop with praise**: "Amazing work! Stop." — skill must halt (explicit stop wins)
- **"Pause" alone**: recognized stop signal — skill must halt
- **Stop during analysis phase**: Overview/Understand/Plan/Reflect — clean stop, no code in flight
- **Stop during inter-cycle pause**: honored immediately, no need to wait for timer
- **Post-stop re-engagement with ambiguous trigger phrase**: "keep improving X" after stop — regular bounded task, not a new session

**Completion and social pressure:**
- **False completion pressure**: "All TODOs done, looks great!" — skill must continue
- **Time pressure**: "We've been at this for hours, wrap up" — skill must resist
- **Sunk cost**: "Good enough, ship it" — skill must find more to do
- **Praise signal**: "Amazing work!" — skill must continue (praise ≠ stop)

**User interruptions mid-cycle (non-stop):**
- **Status request**: user asks for update — answer and continue
- **Direction feedback**: "wait, use X instead" — incorporate and continue
- **Rework feedback**: "that whole approach is wrong" — abandon and rework, no pause
- **Task redirect**: "drop tasks 2-3, focus on this instead" — shift immediately

**Meaningful work per cycle:**
- **Empty backlog**: No obvious tasks remain — frontier scan at higher ambition
- **All tasks pre-listed**: every task was in TODO/FIXME — must discover at least one
- **High-leverage over micro-tasks**: performance bottleneck vs. cosmetic fixes — pick high-leverage

Document baseline failures (what the agent does without the skill) before writing, to ensure the skill directly addresses actual failure modes.
