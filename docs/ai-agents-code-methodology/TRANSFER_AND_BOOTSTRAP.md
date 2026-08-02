# Transfer And Bootstrap Guide

This guide helps you move the methodology package to another machine and start configuration in a different repository.

## A) Package this folder on source machine

From repo root in PowerShell:

```powershell
$source = "data/changes/ai-agent-methodology"
$target = "data/changes/ai-agent-methodology-package.zip"
if (Test-Path $target) { Remove-Item $target -Force }
Compress-Archive -Path $source -DestinationPath $target -Force
Write-Host "Created: $target"
```

Send `data/changes/ai-agent-methodology-package.zip` to the other machine.

## B) Unpack on target machine

In the target repository root:

```powershell
$zip = "data/changes/ai-agent-methodology-package.zip"
Expand-Archive -Path $zip -DestinationPath "data/changes" -Force
```

Expected location after extract:

- `data/changes/ai-agent-methodology`

## C) Bootstrap in the target repo

### C1) Shared ledgers (Cursor or Copilot)

Rename and run:

```powershell
Rename-Item data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1.txt bootstrap-new-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1
```

This creates starter docs if missing:

1. `data/changes/STATUS.md`
2. `data/changes/FOLLOWUPS.md`
3. `data/changes/SHARP_EDGES.md`
4. `data/changes/_handover_template.md`
5. `data/changes/_qa_acceptance_template.md`
6. Working-agreement templates (Copilot + Cursor) and orientation template

Note: scripts are shipped as `.ps1.txt` specifically to reduce active-content blocking by mail scanners.

### C2) Cursor surface (optional but recommended for Cursor)

```powershell
Rename-Item data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1.txt bootstrap-cursor-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1
# optional: pin CodeGraph path explicitly
# pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1 -CodegraphPath "D:/path/to/repo"
```

This creates if missing:

1. `.cursor/rules/*.mdc` — methodology gates + tool prevalence
2. `.cursor/skills/{kg,kg-refresh,methodology-plan,sanitise-diff}/`
3. `.cursor/mcp.json` from example (substitutes `__REPO_ROOT__`)
4. `.cursor/hooks.json` + `hooks/block-external-git.ps1`
5. `AGENTS.md` at repo root
6. Appends `.codegraph/` to `.gitignore` when present

Then: edit MCP if needed → `codegraph init` → reload Cursor.
See `CURSOR_ADAPTATION.md` and `cursor/README.md`.

## D) First-day setup checklist

1. Fill `STATUS.md` with current in-flight work.
2. Add 3-5 initial invariants in `SHARP_EDGES.md`.
3. Confirm output contract definition for your system (also in `AGENTS.md` if using Cursor).
4. Define scoped test commands by subsystem.
5. (Cursor) Verify MCP tools respond; (Copilot) confirm agent can see orientation docs.
6. Run one issue fully with RED -> GREEN + contract verification.

## E) If knowledge graph is not available

Use this fallback process:

1. Maintain `STATUS.md` and per-ticket folders as your source of truth.
2. Search by contract fields, symptom terms, and key symbols.
3. Use git history overlap (files touched) to find related prior fixes.
4. Keep `SHARP_EDGES.md` short and current.

The Cursor `kg` skill documents this fallback explicitly.
