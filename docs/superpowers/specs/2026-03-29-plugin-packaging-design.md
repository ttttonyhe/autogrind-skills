# Plugin Packaging Design

**Date:** 2026-03-29
**Status:** Approved

## Goal

Package the AutoGrind skill as an officially supported plugin for Claude Code and OpenAI Codex, publishable to their respective plugin registries, while preserving full agentskills.io compatibility for the 15+ other supported agents.

## Approach

Restructure `autogrind/` to satisfy three distribution formats simultaneously from one directory:

| Format | Mechanism | Install path |
|--------|-----------|--------------|
| agentskills.io skill | `SKILL.md` at directory root | `~/.agents/skills/autogrind/` |
| Claude Code plugin | `.claude-plugin/plugin.json` + `skills/autogrind/SKILL.md` | `~/.claude/plugins/cache/` |
| Codex plugin | `.codex-plugin/plugin.json` + `skills/autogrind/SKILL.md` | `~/.codex/plugins/cache/` |

The agentskills.io spec explicitly permits "any additional files or directories" alongside `SKILL.md`, so `.claude-plugin/`, `.codex-plugin/`, and `skills/` coexist without conflict.

## Repository structure

```
autogrind-skills/
├── autogrind/                            modified
│   ├── SKILL.md                          existing (agentskills.io root)
│   ├── .claude-plugin/                   new
│   │   └── plugin.json
│   ├── .codex-plugin/                    new
│   │   └── plugin.json
│   ├── skills/                           new
│   │   └── autogrind/
│   │       └── SKILL.md                  new (same content as root SKILL.md)
│   ├── assets/                           new
│   │   ├── icon.png
│   │   └── logo.png
│   ├── agents/openai.yaml                existing
│   ├── evals/evals.json                  existing
│   └── README.md                         existing
│
├── .claude-plugin/                       new
│   └── marketplace.json                  Claude Code marketplace catalog
│
├── .agents/                              new
│   └── plugins/
│       └── marketplace.json              Codex marketplace catalog
│
├── docs/plugin/                          new
│   └── README.md                         plugin install guide
│
├── README.md                             modified (add plugin link)
└── CLAUDE.md                             modified (add sync note)
```

## File contents

### `autogrind/.claude-plugin/plugin.json`

```json
{
  "name": "autogrind",
  "version": "1.4.0",
  "description": "Continuous autonomous grind loop — works until you say stop",
  "author": {
    "name": "ttttonyhe",
    "url": "https://github.com/ttttonyhe"
  },
  "homepage": "https://github.com/ttttonyhe/autogrind-skills",
  "repository": "https://github.com/ttttonyhe/autogrind-skills",
  "license": "MIT",
  "keywords": ["autogrind", "autonomous", "continuous", "grind", "productivity"],
  "skills": "./skills/"
}
```

### `autogrind/.codex-plugin/plugin.json`

```json
{
  "name": "autogrind",
  "version": "1.4.0",
  "description": "Continuous autonomous grind loop — works until you say stop",
  "author": { "name": "ttttonyhe", "url": "https://github.com/ttttonyhe" },
  "homepage": "https://github.com/ttttonyhe/autogrind-skills",
  "repository": "https://github.com/ttttonyhe/autogrind-skills",
  "license": "MIT",
  "keywords": ["autogrind", "autonomous", "continuous", "grind", "productivity"],
  "skills": "./skills/",
  "interface": {
    "displayName": "AutoGrind",
    "shortDescription": "Continuous autonomous grind loop — works until you say stop",
    "longDescription": "AutoGrind keeps the agent continuously working through a five-phase cycle: Overview → Understand → Plan → Work → Reflect → 60s pause → repeat. The agent never decides the project is done enough. Only the user decides when to stop.",
    "developerName": "ttttonyhe",
    "category": "Productivity",
    "capabilities": ["Read", "Write", "Execute"],
    "defaultPrompt": ["/autogrind", "keep working, don't stop", "autogrind this project"],
    "composerIcon": "./assets/icon.png",
    "logo": "./assets/logo.png"
  }
}
```

### `.claude-plugin/marketplace.json` (repo root)

```json
{
  "name": "autogrind",
  "owner": { "name": "ttttonyhe" },
  "metadata": {
    "description": "AutoGrind skill — continuous autonomous agent grind loop"
  },
  "plugins": [
    {
      "name": "autogrind",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/ttttonyhe/autogrind-skills.git",
        "path": "autogrind"
      },
      "description": "Continuous autonomous grind loop — works until you say stop",
      "license": "MIT",
      "homepage": "https://github.com/ttttonyhe/autogrind-skills",
      "repository": "https://github.com/ttttonyhe/autogrind-skills",
      "category": "productivity",
      "keywords": ["autogrind", "autonomous", "grind"]
    }
  ]
}
```

### `.agents/plugins/marketplace.json` (repo root)

```json
{
  "name": "autogrind",
  "interface": { "displayName": "AutoGrind" },
  "plugins": [
    {
      "name": "autogrind",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/ttttonyhe/autogrind-skills.git",
        "path": "autogrind"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

## SKILL.md sync

`autogrind/SKILL.md` and `autogrind/skills/autogrind/SKILL.md` must remain byte-for-byte identical. A pre-commit hook enforces this:

```bash
#!/bin/sh
diff autogrind/SKILL.md autogrind/skills/autogrind/SKILL.md > /dev/null 2>&1 || {
  echo "Error: autogrind/SKILL.md and autogrind/skills/autogrind/SKILL.md are out of sync."
  echo "Update both files before committing."
  exit 1
}
```

## Distribution flow

### Claude Code

1. Validate: `claude plugin validate ./autogrind`
2. Test locally: `claude --plugin-dir ./autogrind`
3. Users install from this repo's marketplace:
   ```
   /plugin marketplace add ttttonyhe/autogrind-skills
   /plugin install autogrind@autogrind
   ```
4. Submit to official Anthropic marketplace: `claude.ai/settings/plugins/submit`

### Codex

1. Users add the marketplace from this repo (`~/.agents/plugins/marketplace.json`)
2. Official Plugin Directory submission when Codex self-serve publishing launches

## New files summary

| File | Purpose |
|------|---------|
| `autogrind/.claude-plugin/plugin.json` | Claude Code plugin manifest |
| `autogrind/.codex-plugin/plugin.json` | Codex plugin manifest |
| `autogrind/skills/autogrind/SKILL.md` | Plugin-format skill (mirrors root SKILL.md) |
| `autogrind/assets/icon.png` | Codex marketplace composer icon |
| `autogrind/assets/logo.png` | Codex marketplace logo |
| `.claude-plugin/marketplace.json` | Claude Code marketplace catalog |
| `.agents/plugins/marketplace.json` | Codex marketplace catalog |
| `docs/plugin/README.md` | Plugin installation guide |
| `.git/hooks/pre-commit` | SKILL.md sync enforcement |
