#!/usr/bin/env bash
# machine-sync — target (laptop) setup for CodeGraph + GSD after a full-copy restore.
# Idempotent & non-destructive: safe to re-run. Run in a WSL shell (NOT PowerShell), from anywhere.
# Referenced by RUNBOOK.md Step 4c. Gitignored (under data/) — ops content, never ships.
set -uo pipefail

say() { printf '\n== %s ==\n' "$1"; }

# 1) Discover the workspace root — do NOT assume /mnt/d (the laptop may differ).
WS="${WS:-$(ls -d /mnt/*/ILS /mnt/*/*/ILS 2>/dev/null | head -1)}"
if [ -z "$WS" ]; then
  echo "FATAL: no /mnt/*/ILS workspace found. Set WS manually, e.g.  WS=/mnt/c/repos/ILS  and re-run." >&2
  exit 1
fi
REPO="$WS/document-parser-lambda"
[ -d "$REPO" ] || { echo "FATAL: $REPO not found (restore incomplete?)." >&2; exit 1; }
echo "workspace: $WS"
echo "repo:      $REPO"

# 2) Prereqs
say "prereqs"
node -v || { echo "FATAL: node missing (need >= 22.5 for codegraph's node:sqlite)." >&2; exit 1; }
command -v npm  >/dev/null || { echo "FATAL: npm missing." >&2; exit 1; }
command -v claude >/dev/null && claude --version || echo "WARN: 'claude' CLI not on PATH (fine if you launch it another way)."

# 3) GSD — update to latest ONLY if behind (avoids a needless folder re-wipe).
say "GSD"
CUR_GSD=$(cat "$HOME/.claude/get-shit-done/VERSION" 2>/dev/null || echo "0.0.0")
LATEST_GSD=$(npm view get-shit-done-cc version 2>/dev/null || echo "")
echo "installed: $CUR_GSD   latest: ${LATEST_GSD:-<npm unavailable>}"
if [ -n "$LATEST_GSD" ] && [ "$CUR_GSD" != "$LATEST_GSD" ]; then
  echo "updating GSD $CUR_GSD -> $LATEST_GSD ..."
  npx -y get-shit-done-cc@latest --claude --global
  cat "$HOME/.claude/get-shit-done/VERSION"
else
  echo "GSD already latest (or npm offline) — skipping."
fi

# 4) CodeGraph CLI — install only if missing.
say "CodeGraph CLI"
if command -v codegraph >/dev/null; then
  echo "already installed: $(codegraph --version)"
else
  echo "installing @colbymchenry/codegraph ..."
  npm i -g @colbymchenry/codegraph
  codegraph --version
fi

# 5) MCP config — ensure the entry exists, then pin --path to THIS machine's repo.
say "MCP config (~/.claude.json)"
CFG="$HOME/.claude.json"
if [ -f "$CFG" ]; then
  cp "$CFG" "$CFG.bak-$(date +%Y%m%d-%H%M%S)" && echo "backup: $CFG.bak-*"
fi
# Create the codegraph MCP entry if it's absent (fresh machine / never installed).
if ! python3 -c "import json,os,sys; d=json.load(open(os.path.expanduser('~/.claude.json'))); sys.exit(0 if d.get('mcpServers',{}).get('codegraph') else 1)" 2>/dev/null; then
  echo "codegraph MCP entry absent — writing it via 'codegraph install' ..."
  codegraph install --target=claude --location=global --yes >/dev/null 2>&1 || true
fi
# Force --path to the discovered repo (idempotent: rewrites to the same value if already correct).
python3 - "$REPO" <<'PY'
import json, os, sys
repo = sys.argv[1]
p = os.path.expanduser("~/.claude.json")
d = json.load(open(p))
srv = d.setdefault("mcpServers", {}).get("codegraph")
if not srv:
    # Minimal stdio entry if 'codegraph install' didn't write one.
    srv = {"type": "stdio", "command": "codegraph", "args": ["serve", "--mcp"]}
    d["mcpServers"]["codegraph"] = srv
args = srv.get("args", ["serve", "--mcp"])
if "--path" in args:
    i = args.index("--path")
    if i + 1 < len(args): args[i + 1] = repo
    else: args.append(repo)
else:
    j = args.index("serve") + 1 if "serve" in args else 0
    args[j:j] = ["--path", repo]
srv["args"] = args
json.dump(d, open(p, "w"), indent=2)
print("args ->", args)
PY

# 6) Build (or sync) the index for the repo you navigate.
say "index"
cd "$REPO"
if [ -d .codegraph ]; then
  echo "existing index -> sync"; codegraph sync
else
  echo "no index -> init"; codegraph init
fi
codegraph status 2>&1 | grep -Ev '·|✢|Scanning|\[K' | tail -12

cat <<EOF

DONE. Now:
  1. RESTART Claude Code (so the MCP server respawns with --path=$REPO).
  2. Verify a BARE query (no projectPath) resolves in a Claude session:
       codegraph_explore "get_letter_end"   -> blast radius + source, NOT "No CodeGraph project loaded".
Optional context repos: cd \$WS/monolith (or frontend) && codegraph init  (query them with projectPath).
EOF
