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

### Invoke

```shell
/autogrind
```

Or use a trigger phrase — Claude Code recognises these automatically:
`keep working, don't stop`, `autogrind this project`

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

Codex uses `local` source paths, so you need the plugin files on disk alongside the marketplace catalog:

```bash
mkdir -p ~/.agents/plugins
# Copy the plugin
git clone --depth 1 https://github.com/ttttonyhe/autogrind-skills.git /tmp/autogrind-skills
cp -r /tmp/autogrind-skills/autogrind ~/.agents/plugins/autogrind
# Install the marketplace catalog (points to ./autogrind relative to ~/.agents/plugins/)
cp /tmp/autogrind-skills/.agents/plugins/marketplace.json ~/.agents/plugins/marketplace.json
```

Restart Codex. The AutoGrind plugin will appear in the plugin directory, ready to install.

### Invoke

```
/autogrind
```

Or: `autogrind this project, don't stop`
