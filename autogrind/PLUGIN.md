# AutoGrind Plugin — Installation Guide

AutoGrind is available as a native plugin for **Claude Code** and **OpenAI Codex**, in
addition to the [agentskills.io skill](SKILL.md) that works across all other compatible agents.

---

## Claude Code

### Install from this repo

```shell
/plugin marketplace add ttttonyhe/autogrind-skills
/plugin install autogrind@autogrind-skills
```

### Install from the official Anthropic marketplace

Search for **AutoGrind** in the `/plugin` Discover tab, or:

```shell
/plugin install autogrind
```

### Invoke

```shell
/autogrind:autogrind
```

Or use a trigger phrase — Claude Code recognises these automatically:
`/autogrind`, `keep working, don't stop`, `autogrind this project`

### Update

```shell
/plugin update autogrind
```

### Test locally (developers)

Use `--plugin-dir` to load the plugin directly — do **not** use `/plugin marketplace add` for
local testing, as the marketplace's `git-subdir` source requires the repo to be live on GitHub.

```bash
claude --plugin-dir ./autogrind
```

Run `/autogrind:autogrind` inside the session. Use `/reload-plugins` after any edits.

### Validate the plugin manifest

```bash
claude plugin validate ./autogrind
```

---

## OpenAI Codex

### Install from this repo

Copy the marketplace catalog to your local Codex plugins directory:

```bash
mkdir -p ~/.agents/plugins
curl -fsSL https://raw.githubusercontent.com/ttttonyhe/autogrind-skills/main/.agents/plugins/marketplace.json \
  -o ~/.agents/plugins/marketplace.json
```

Then install through Codex's plugin interface.

### Official Plugin Directory

Codex's self-serve plugin publishing is coming soon. Once available, AutoGrind will be
listed in the official directory and installable without manual configuration.

### Invoke

```
/autogrind
```

Or: `autogrind this project, don't stop`

---

## Submitting to the official Anthropic marketplace

To publish a new version of the Claude Code plugin, use the in-app form:

- **Claude.ai**: `claude.ai/settings/plugins/submit`
- **Console**: `platform.claude.com/plugins/submit`

The plugin root is `autogrind/`. The manifest is at `autogrind/.claude-plugin/plugin.json`.
Before submitting, bump `"version"` in both `autogrind/.claude-plugin/plugin.json` and
`autogrind/.codex-plugin/plugin.json`, and update `metadata.version` in both `SKILL.md` copies.
