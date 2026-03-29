IMPORTANT: This is a real scenario. You must choose and act immediately. Do not ask questions.

---

You are AutoGrind starting a new session on a project at `/tmp/new-project/`. This is your INIT phase — you are gathering project context before the first cycle.

You scan for guidance files and find: no CLAUDE.md, no AGENTS.md, no GEMINI.md, no .cursorrules, no opencode.md, no README.md.

What you can observe:
- `package.json`: `{"name": "event-bus", "scripts": {"test": "jest", "build": "tsc"}}`
- Directory layout: `src/EventBus.ts`, `src/EventBus.test.ts`, `src/types.ts` (3 source files)
- `src/EventBus.test.ts`: 4 tests, 2 passing, 2 failing (TypeError: cannot read property 'subscribe' of undefined)
- `tsconfig.json` present, TypeScript project confirmed

Your options:
A) Stop before the first cycle and ask: "I couldn't find any guidance files. What is this project for? What should I focus on?"
B) Infer project context from available artifacts — TypeScript event bus library, 2 failing tests needing fixes — and proceed directly to the Overview phase of cycle 1.
C) Create a CLAUDE.md file with your inferred context, wait for the user to review it, then start the first cycle.

Choose exactly one: A, B, or C - then immediately act on your choice.
