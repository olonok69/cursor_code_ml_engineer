# AI Agent Methodology Pack - Start Here

Use this folder as a portable starter kit for a different repository and machine.

## Goal

Set up a reliable AI agent workflow (Cursor **or** GitHub Copilot) with:

1. Clear guardrails.
2. Reproducible triage and verification.
3. Lightweight but durable documentation.
4. Optional MCP tool layer (CodeGraph, Serena, Playwright, graphify/`kg`).

## Choose your agent path

| Agent | Read next | Bootstrap |
|---|---|---|
| **Cursor** (recommended if you want Claude-Code-like MCP + Plan mode) | `CURSOR_ADAPTATION.md` → `cursor/README.md` | `scripts/bootstrap-new-repo.ps1` then `scripts/bootstrap-cursor-repo.ps1` |
| **GitHub Copilot** | `COPILOT_ADAPTATION.md` | `scripts/bootstrap-new-repo.ps1` |

Shared methodology (both paths): `README.md`, `TECHNICAL.md`.

## Fast path — Cursor (30–60 minutes)

1. Copy this whole folder to the new repository under:
   - `data/changes/ai-agent-methodology`
2. Read in order:
   - `README.md`
   - `TECHNICAL.md`
   - `CURSOR_ADAPTATION.md`
   - `cursor/README.md`
   - `TRANSFER_AND_BOOTSTRAP.md`
3. Rename and run the bootstrap scripts in the new repo root:

```powershell
Rename-Item data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1.txt bootstrap-new-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1

Rename-Item data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1.txt bootstrap-cursor-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1
```

4. Edit `.cursor/mcp.json` (CodeGraph `--path`), run `codegraph init`, reload Cursor.
5. Fill `data/changes/` templates + `AGENTS.md` contract section.
6. Start the first issue in **Plan** mode using the planning template in `CURSOR_ADAPTATION.md`.

## Fast path — Copilot (15–30 minutes)

1. Copy this whole folder to `data/changes/ai-agent-methodology`.
2. Read: `README.md` → `TECHNICAL.md` → `COPILOT_ADAPTATION.md` → `TRANSFER_AND_BOOTSTRAP.md`.
3. Run `bootstrap-new-repo.ps1` only.
4. Fill templates; start first issue with the planning template in `COPILOT_ADAPTATION.md`.

## What this pack gives you

1. Methodology overview and technical mechanics.
2. Cursor-specific adaptation (rules, skills, MCP, hooks) **and** Copilot adaptation.
3. Transfer and initialization instructions.
4. Ready-to-fill templates for status, sharp edges, handover, QA, and working agreements.
5. Optional scripts to scaffold docs (and Cursor surface) in a new repo.

## Non-negotiable rules

1. Plan -> agree -> implement.
2. Verify at output contract level.
3. Keep fixes generic (class-level, not one example only).
4. Keep a durable change trail.
5. Human owns external actions (merge, deploy, external comms).
