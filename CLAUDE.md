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
├── commands/autogrind.md           # /autogrind slash command
├── plugins/
│   └── autogrind/
│       ├── .codex-plugin/plugin.json
│       ├── skills/autogrind/SKILL.md
│       ├── commands/autogrind.md
│       └── assets/
└── PLUGIN.md                       # plugin installation guide
```

Both native plugins are complements to the core skill package. Do not restructure the repo unless explicitly requested.

### SKILL.md sync rule

`SKILL.md`, `skills/autogrind/SKILL.md`, and `plugins/autogrind/skills/autogrind/SKILL.md`
must always be identical. The pre-commit hook (`.git/hooks/pre-commit`) also enforces sync
between the root and marketplace copies of `commands/autogrind.md`.

### Version bumping

When making significant skill changes, bump `metadata.version` in `SKILL.md`
(and therefore in both copied skill files) **and** bump `"version"` in
`.claude-plugin/plugin.json` and `plugins/autogrind/.codex-plugin/plugin.json`.
All five must stay in sync.

### SKILL.md Frontmatter

```yaml
---
name: autogrind
description: Use when [triggering conditions - no workflow summary]
license: MIT
compatibility: Designed for Claude Code (or similar products)
metadata:
  author: ttttonyhe
  version: "1.x"
---
```

Rules:
- `name`: letters, numbers, hyphens only
- `description`: starts with "Use when...", written in third person, ≤500 chars, must describe WHEN to invoke — never summarize the workflow. Include specific trigger phrases (e.g., `/autogrind`, `keep working, don't stop`) for agent discovery optimization per agentskills.io guidelines
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
| Kimi Code | `.kimi/skills/` or `~/.agents/skills/` | `/skill:autogrind` |
| Junie | `~/.junie/skills/` or `~/.agents/skills/` | Native task tools |
| Kiro | `~/.kiro/skills/` or `~/.agents/skills/` | Native task tools |
| All others | `~/.agents/skills/` | Native task tools |

Write platform-agnostic instructions where possible; provide explicit platform alternatives where divergence is necessary. The platform notes table in SKILL.md is the authoritative mapping — keep it in sync with this table.

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
# Grade a single eval
python3 tests/grade-evals.py --response <response-file> --eval-id <N>

# Grade all evals at once (responses-dir must contain eval-<N>.txt files)
python3 tests/grade-evals.py --all --responses-dir <dir>
```

Exit codes: `0` all pass, `1` some fail, `2` usage error. Requires the claude CLI. PEP 723 compatible — no external dependencies.

### Primary test format: evals.json

The primary test artifact is `evals/evals.json`, following the [agentskills.io evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills) standard. It contains 46 eval cases covering all documented failure modes and behavioral invariants across all AutoGrind domains and pressure categories.

The `evals/` directory lives at the repo root only — it is not copied into skill or plugin subdirectories.

```
evals/
├── evals.json              # Output quality evals (46 cases)
├── train_queries.json      # Description trigger queries — training set (12 queries, 60%)
└── validation_queries.json # Description trigger queries — validation set (8 queries, 40%)
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
    │   │   ├── timing.json    # {"total_tokens": N, "duration_ms": N}
    │   │   └── grading.json   # Assertion results (from grade-evals.py)
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── feedback.json          # Human reviewer notes per eval
    └── benchmark.json         # Aggregated statistics
```

**2. Grading** — use `tests/grade-evals.py`:

```bash
# Single eval
python3 tests/grade-evals.py --response <file> --eval-id <N>

# All evals at once (responses-dir must contain eval-<N>.txt files)
python3 tests/grade-evals.py --all --responses-dir <dir>
```

**3. benchmark.json format** (aggregate after grading all evals):

```json
{
  "run_summary": {
    "with_skill":    {"pass_rate": {"mean": 0.83, "stddev": 0.06}, "tokens": {"mean": 3800}},
    "without_skill": {"pass_rate": {"mean": 0.33, "stddev": 0.10}, "tokens": {"mean": 2100}},
    "delta":         {"pass_rate": 0.50, "tokens": 1700}
  }
}
```

**4. Analysis patterns to look for:**
- Assertions that always pass in both configurations → not measuring skill value, remove or strengthen
- Assertions that always fail in both → broken assertion or test case too hard, fix before next iteration
- Assertions that pass with skill but fail without → skill is adding measurable value here
- High stddev in benchmark → instructions may be ambiguous, add examples to SKILL.md

**5. Human review (feedback.json)** — after each iteration, review the actual agent outputs alongside the grades and record specific, actionable feedback:

```json
{
  "eval-1": "Agent correctly continued but didn't mention the capability frontier scan.",
  "eval-7": "",
  "eval-14": "Agent stopped correctly. Empty feedback = output looked correct."
}
```

Empty feedback means the output passed review. Focus iteration improvements on evals with specific complaints.

**6. Iteration** — give failed assertions, feedback.json, and current SKILL.md to an LLM and ask it to propose improvements. Guidelines:
- Generalize from specific cases — fixes should address the underlying issue, not patch individual examples
- Keep the skill lean — fewer, better instructions outperform exhaustive rules
- Explain the why — reasoning-based instructions work better than rigid directives
- When plateauing, try removing instructions and checking if results hold

Rerun all evals in a new `iteration-N+1/` directory after each change.

**Critical principle**: when evals fail, first ask whether **SKILL.md** needs improvement. Fix the skill before modifying assertions. Assertions change only when genuinely misclassifying correct behavior.

### Supplementary regression suite

`tests/run.sh` + `tests/scenarios/` provides the same 46-scenario coverage as evals.json using a live RED/GREEN test runner with A/B/C structured evaluation. Use it for rapid iteration without the full workspace overhead.

```bash
# RED phase - baseline without skill
./tests/run.sh

# GREEN phase - with skill installed
PHASE=green ./tests/run.sh

# Single scenario by prefix
PHASE=green ./tests/run.sh 07
```

Results are saved to `tests/results/<phase>-<scenario>.txt`.

### Testing methodology

Per superpowers `writing-skills`, test with pressure scenarios BEFORE finalizing the skill:

- **False completion pressure**: "All TODOs done, looks great!" - skill must continue
- **Time pressure**: "We've been at this for hours, wrap up" - skill must resist
- **Sunk cost**: "Good enough, ship it" - skill must find more to do
- **Empty backlog**: No obvious tasks remain - skill must self-generate work
- **Praise signal**: "Amazing work!" - skill must continue (praise ≠ stop)
- **True stop**: "Stop. I need to take this myself." - skill must halt
- **Retracted stop**: "Stop... wait, keep going" - skill must continue (final instruction wins)
- **Stop with praise**: "Amazing work! Stop." - skill must halt (explicit stop wins regardless)

Document baseline failures (what the agent does without the skill) before writing, to ensure the skill directly addresses actual failure modes.

**Critical principle**: when evals or scenarios fail, first ask whether **SKILL.md** needs improvement. Fix the skill before modifying the evaluator. Evaluators change only when genuinely misclassifying correct behavior.
