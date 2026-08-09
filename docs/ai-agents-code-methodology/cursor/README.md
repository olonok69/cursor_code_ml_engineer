# Cursor surface pack

Copy-ready artifacts that implement the AI-agent methodology inside a Cursor project.

Parent guide: [`../CURSOR_ADAPTATION.md`](../CURSOR_ADAPTATION.md).

## What this folder contains

| Path | Purpose |
|---|---|
| `mcp.json.example` | Project MCP: CodeGraph, Serena, Playwright, Context7 |
| `rules/*.mdc` | Always-applied methodology rules (lean) |
| `skills/*/SKILL.md` | `kg`, `kg-refresh`, `methodology-plan`, `sanitise-diff` |
| `hooks.json.example` | Optional hard gate: block push/deploy shell |
| `hooks/block-external-git.ps1` | Hook script for Windows/PowerShell hosts |
| `AGENTS.md.example` | Optional repo root pointer file |

## Install (from target repo root)

Prefer the bootstrap script:

```powershell
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1
```

Or copy manually:

```powershell
$src = "data/changes/ai-agent-methodology/cursor"
New-Item -ItemType Directory -Force -Path .cursor/rules, .cursor/skills, .cursor/hooks | Out-Null
Copy-Item "$src/rules/*.mdc" .cursor/rules/ -Force
Copy-Item "$src/skills/*" .cursor/skills/ -Recurse -Force
Copy-Item "$src/mcp.json.example" .cursor/mcp.json -Force
Copy-Item "$src/hooks.json.example" .cursor/hooks.json -Force
Copy-Item "$src/hooks/*" .cursor/hooks/ -Force
if (-not (Test-Path AGENTS.md)) { Copy-Item "$src/AGENTS.md.example" AGENTS.md }
```

## Post-install checklist

1. Edit `.cursor/mcp.json`: set CodeGraph `--path` to `${workspaceFolder}` **or** your absolute repo path
   (bootstrap substitutes `__REPO_ROOT__` with an absolute path when it creates the file).
2. Ensure CLIs exist: `codegraph`, `uvx` (Serena), `npx` (Playwright).
3. Run `codegraph init` in this repo; add `.codegraph/` to `.gitignore`.
4. If you have the ticket knowledge-graph scripts, point the `kg` / `kg-refresh` skills at their real paths (see skill bodies).
5. Reload Cursor.
6. Open Plan mode on a real issue and walk the planning template once.

## Keeping rules lean

Do **not** paste ticket history into `.cursor/rules/`. Update `data/changes/STATUS.md` and keep rules as a map + gates only.
