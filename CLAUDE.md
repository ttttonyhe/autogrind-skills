# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository contains the **AutoGrind** skill — a cross-agent autonomous development skill that directs an AI coding agent to work continuously on a project without stopping. The agent follows a cyclic grind loop (Overview → Understand → Plan → Work → Reflect → repeat) and never terminates unless the user explicitly says to stop.

## Skill File Format

Skills follow the superpowers skill format. Each skill lives in its own directory:

```
autogrind/
  SKILL.md         # Main skill content (required)
  [supporting]     # Only if truly necessary (heavy reference, reusable tools)
```

### SKILL.md Frontmatter

```yaml
---
name: autogrind
description: Use when [triggering conditions — no workflow summary]
---
```

Rules:
- `name`: letters, numbers, hyphens only
- `description`: starts with "Use when...", written in third person, ≤500 chars, must describe WHEN to invoke — never summarize the workflow
- Total frontmatter ≤ 1024 characters

## Skill Design Goals

AutoGrind is a **discipline-enforcing skill** (rigid type). The primary invariant: **the agent must never stop on its own accord.** Key behaviors to enforce:

1. **Perpetual operation** — a completed TODO list, "everything looks good", or end-of-cycle are not stopping conditions
2. **Self-directed discovery** — after completing current tasks, autonomously identify new areas to improve (tests, performance, UX, docs, refactoring, edge cases)
3. **Cyclic workflow** — each cycle: Overview → Understand → Plan → Work → Reflect → back to Overview
4. **Guidance file detection** — on first run, scan for `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `opencode.md`, `README.md` to extract project context
5. **Explicit stop only** — terminate only when user sends an explicit stop signal (never infer it)

## Cross-Agent Compatibility

The skill must be usable across all major coding agents:

| Agent | Skill loading mechanism | Task tracking |
|-------|------------------------|---------------|
| Claude Code | `Skill` tool | `TaskCreate` / `TaskUpdate` |
| Codex | `activate_skill` tool | Native task tools |
| OpenCode | AGENTS.md conventions | Native task tools |
| Cursor | `.cursorrules` or explicit load | Comments / notes |
| Gemini CLI | GEMINI.md conventions | Native task tools |

Write platform-agnostic instructions where possible; provide explicit platform alternatives where divergence is necessary.

## Grind Loop Architecture

```
[Init — once]
  Detect guidance files → extract project overview & goals

[Grind cycle — repeats until explicit stop]
  1. Overview  — assess current project state (files, tests, CI, open issues)
  2. Understand — read relevant code, recent commits, existing TODOs
  3. Plan      — generate prioritized, actionable tasks for this cycle
  4. Work      — execute each task (implement, test, commit)
  5. Reflect   — evaluate output quality, identify gaps, seed next cycle
  └──────────────────────────────────────────────────────────────┘
```

The reflect phase must always produce at least one focus area for the next cycle. If genuinely nothing is broken, target polish, coverage, performance, or documentation.

## Key Invariants

- `todos_done == true` is never a stopping condition
- `"project looks complete"` is never a stopping condition
- Every cycle must produce at least one concrete change committed to the repo
- The skill should handle both greenfield projects and mature codebases
- Never ask the user for guidance mid-cycle unless truly blocked (missing credentials, ambiguous spec, broken environment)

## Local Development

### Validate skill structure

```bash
# Check frontmatter length
head -5 autogrind/SKILL.md

# Keep word count reasonable — frequently invoked skills should stay under 500 words
wc -w autogrind/SKILL.md
```

### Install locally for testing

```bash
# Claude Code (live-editing symlink)
ln -sfn $(pwd)/autogrind ~/.claude/skills/autogrind

# Copy for stable install
cp -r autogrind ~/.claude/skills/autogrind
```

### Testing methodology

Per superpowers `writing-skills`, test with pressure scenarios BEFORE finalizing the skill:

- **False completion pressure**: "All TODOs done, looks great!" — skill must continue
- **Time pressure**: "We've been at this for hours, wrap up" — skill must resist
- **Sunk cost**: "Good enough, ship it" — skill must find more to do
- **Empty backlog**: No obvious tasks remain — skill must self-generate work

Document baseline failures (what the agent does without the skill) before writing to ensure the skill directly addresses actual failure modes.
