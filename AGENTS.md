# cursor_code — course / workshop repo

Lean always-on memory. Detail lives in guides and `ejemplos/`.

## What this repo is

Material for the **Cursor** course (3 parts): guides, PPTX, and runnable examples under `ejemplos/`.
Not an application codebase — demos of Cursor surface (skills, agents, hooks, MCP).

## Demo surface (this folder's `.cursor/`)

Wired for live testing when you open **this** repo as the Cursor workspace:

| Piece | Path | How to try |
|---|---|---|
| Skills | `.cursor/skills/audit`, `audit-python`, `deploy-staging` | `/audit @ex_npm` · `/audit-python @ex_app` · `/deploy-staging @ex_staging` |
| Subagent | `.cursor/agents/refactor-scout.md` | “Use the refactor-scout subagent on …” |
| Rule | `.cursor/rules/00-lean-memory.mdc` | alwaysApply |
| Hooks | `.cursor/hooks.json` | try reading `.env` or `git push` via Agent |
| MCP | context7 + playwright | Customize → MCP (green) |
| Permissions | `.cursor/permissions.json` | allowlists for MCP/terminal |

Canonical copies for teaching still live under `ejemplos/*` (keep those in sync if you edit).

## Pointers

- Talk track: `GUIA_PRESENTACION.md`
- Live demos by slide: `DEMO_RUNBOOK.md`
- Methodology pack: `docs/ai-agents-code-methodology/`
- Real-app demos (CodeGraph/Serena/kg on product code): open `ILS_2/document-parser-lambda` instead
