#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/ttttonyhe/autogrind-skills.git}"
PLUGIN_DIR="${PLUGIN_DIR:-$HOME/plugins/autogrind}"
MARKETPLACE_PATH="${MARKETPLACE_PATH:-$HOME/.agents/plugins/marketplace.json}"

mkdir -p "$(dirname "$PLUGIN_DIR")" "$(dirname "$MARKETPLACE_PATH")"

if [[ -d "$PLUGIN_DIR/.git" ]]; then
  git -C "$PLUGIN_DIR" pull --ff-only
elif [[ -e "$PLUGIN_DIR" ]]; then
  echo "Refusing to overwrite existing path: $PLUGIN_DIR" >&2
  echo "Move it aside or set PLUGIN_DIR to another location, then rerun." >&2
  exit 1
else
  git clone --depth 1 "$REPO_URL" "$PLUGIN_DIR"
fi

python3 - "$MARKETPLACE_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
path.parent.mkdir(parents=True, exist_ok=True)

data = {
    "name": "personal",
    "interface": {"displayName": "Personal Plugins"},
    "plugins": [],
}

if path.exists():
    data = json.loads(path.read_text())

data.setdefault("name", "personal")
data.setdefault("interface", {}).setdefault("displayName", "Personal Plugins")
plugins = data.setdefault("plugins", [])

entry = {
    "name": "autogrind",
    "source": {
        "source": "local",
        "path": "./plugins/autogrind",
    },
    "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    },
    "category": "Productivity",
}

for i, plugin in enumerate(plugins):
    if plugin.get("name") == "autogrind":
        plugins[i] = entry
        break
else:
    plugins.append(entry)

path.write_text(json.dumps(data, indent=2) + "\n")
print(f"Wrote {path}")
PY

echo "AutoGrind is ready in $PLUGIN_DIR"
echo "Next: open 'plugins' in Codex and install 'autogrind' from your personal marketplace."
