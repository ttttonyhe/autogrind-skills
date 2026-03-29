# AutoGrind Plugins

AutoGrind is available as a native plugin for **Claude Code** and **OpenAI Codex**, in addition to the
[skill](SKILL.md) that works across all other compatible agents.

---

## Claude Code

### One-line install

```bash
claude plugin marketplace add ttttonyhe/autogrind-skills && claude plugin install autogrind@autogrind-skills
```

### In-app install

```text
/plugin marketplace add ttttonyhe/autogrind-skills
/plugin install autogrind@autogrind-skills
```

### Invoke

```text
/autogrind:autogrind
```

Or use a trigger phrase such as `keep working, don't stop` or `autogrind this project`.

### Update

```bash
claude plugin update autogrind@autogrind-skills
```

Run `/reload-plugins` in an active session after install or update if the new plugin state does not appear immediately.

---

## Codex

### Local install from this repo

1. Open this repository in Codex.
2. Open `plugins`.
3. Install `autogrind` from the AutoGrind marketplace

### Invoke

Use a natural trigger phrase such as `autogrind this project`, `keep working, don't stop`, or `continue improving until I say stop`.

---

## Raw Skill Install

If you do not want either native plugin, the core skill still works directly through the usual skills directories documented in the repository [README](./README.md).
