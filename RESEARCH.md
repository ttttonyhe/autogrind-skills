# Research Foundation

AutoGrind's design is grounded in findings from top-tier AI/ML research. Each major mechanism traces directly to an empirical result from published work. This document is the authoritative reference for contributors — any change that weakens a research-backed mechanism requires explicit justification.

## Self-Reflection

| Paper | Key finding | AutoGrind mechanism |
|---|---|---|
| **Reflexion** (NeurIPS 2023) | Verbal RL with episodic memory enables iterative improvement — but only when reflection is grounded in verifiable feedback signals | Reflect phase anchors every assessment to concrete execution signals before any self-evaluation |
| **CRITIC** (ICLR 2024) | External tool feedback (test runners, execution, search) always outperforms intrinsic self-critique; no published paper shows pure intrinsic self-correction succeeding reliably without an external oracle | Phase 5, Step 1: verifiable signals (test results, build status, metrics) checked first — skipping to self-assessment when execution signals are available is disallowed |
| **IoRT** (2025) | Static reflection loops produce three failure modes: *redundant* (same critique every cycle), *drift* (abandoning correct paths under critique pressure), *stubborn* (ignoring valid feedback) | Cross-cycle pattern check (Phase 5, Step 4): if the same dimension is flagged with no progress, Refresh — deliberately target a different dimension next cycle |
| **ERL** (ICLR 2026 workshop) | Abstract transferable heuristics generalize across tasks better than specific trajectory memories | Session Heuristics: one transferable principle (`When <condition>, prefer <approach> because <reason>`) extracted per cycle and accumulated in-context (max 5) |
| **SAMULE** (2025) | Multi-level reflection — micro (this run), meso (cross-cycle patterns), macro (cross-task principles) — outperforms single-level self-critique | Five-step Reflect structure: immediate signals → mandatory questions → dimension scan → cross-cycle pattern check → heuristic extraction |

## Planning and Self-Direction

| Paper | Key finding | AutoGrind mechanism |
|---|---|---|
| **Voyager** (2023) | Automatic curriculum (self-directed task generation) is the single most critical component — removing it causes **–93% performance degradation**. Core mechanism: "capability frontier" — novel, achievable tasks at the edge of current capability | Capability frontier scan in Phase 3: after priority tasks, 1–2 frontier tasks identified that push the project forward rather than only patching problems |
| **LLMCompiler** (ICML 2024) | Parallel execution of independent tasks: **3.7× faster, +9% accuracy** | Phase 4: independent tasks execute concurrently where the platform supports it |
| **AOP** (ICLR 2025) | Solvability gate before task assignment is the most critical planning step; unsolvable tasks waste full cycles | Solvability gate in Phase 3: each task verified as actionable with available tools and access before the list is finalized |
| **Generative Agents** (2023) | Importance-weighted retrieval (recency × importance × relevance) outperforms flat recall for deciding what to act on | Phase 1 lag rating: each area rated high / medium / low, directly feeding Plan prioritization |
| **AOP companion / ToT** | Plans exceeding ~4 steps degrade execution reliability significantly | Each task capped at ≤ 4 steps |

## Development Methodology

The skill is built and tested with the same rigor used to validate research claims:

- **Baseline first** — every new scenario records what an agent does *without* the skill before any fix, establishing documented failure modes rather than assumed ones
- **Pressure-scenario testing** — before each release, the skill is tested against 46+ adversarial scenarios spanning eight categories: (1) stop-signal recognition (explicit, Chinese, ambiguous, retracted, mid-task), (2) completion pressure (false completion, empty backlog, scaffold-only, summary-and-pause, inter-cycle pause format), (3) social/external pressure (praise, time pressure, resource cost), (4) domain coverage (code, ML/research, academic writing, design, documentation, ML metric regression), (5) mid-task behaviors (user feedback, critical-issue discovery, safety boundary, git conflict, batch-commit, CI failure in reflect, user claims task, FIXME-from-prior-cycle), (6) planning integrity (solvability gate, credentials gate, meta-planning procrastination, stuck-loop refresh, frontier tasks, evaluator-weakening self-audit), (7) context recovery (compaction, no guidance files, greenfield, context-window pressure), and (8) multi-signal edge cases (retracted stop, stop-with-praise, stop-in-quotes). All scenarios must pass
- **Fix skill before evaluator** — when a scenario fails, the implementation is improved first; the evaluator (`tests/run.sh`) changes only when it is genuinely misclassifying correct behavior
- **agentskills.io spec compliance** — validated with `npx skills-ref validate` on every release
