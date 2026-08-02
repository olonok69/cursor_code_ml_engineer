# Ejemplos adaptados a Cursor

Misma estructura que los [`ejemplos/`](https://github.com/olonok69/claude_code_ml_engineer/tree/HEAD/ejemplos)
del curso hermano de Claude Code, reescrita para **Cursor**.
La metodología y los roles de tools (CodeGraph, Serena, Playwright, graphify) se mantienen;
cambia la *superficie* del producto (rules, skills, MCP, hooks, SDK).

Guía de adaptación completa: [`../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md`](../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md).

## Índice (mapeo a la Parte 1 del curso)

| Carpeta | Tema Claude Code | Equivalente Cursor |
|---|---|---|
| [`agents-md/`](./agents-md/) | `CLAUDE.md` dos niveles | `AGENTS.md` + `.cursor/rules/` lean |
| [`context/`](./context/) | Context window / `/compact` | Higiene de contexto + límites honestos |
| [`prompt-caching/`](./prompt-caching/) | Caching en Claude Code | Demo API Anthropic + qué controlas en Cursor |
| [`mcp/`](./mcp/) | `.mcp.json` + `claude mcp add` | `.cursor/mcp.json` |
| [`skills-plugins/`](./skills-plugins/) | Slash commands + skills + plugins | Skills en `.cursor/skills/` (sin marketplace Claude) |
| [`subagents/`](./subagents/) | Task + Agent Teams | Task/subagents Cursor (**sin** Agent Teams) |
| [`hooks/`](./hooks/) | Hooks Claude (`exit 2`) | `.cursor/hooks.json` + permission JSON |
| [`automation/`](./automation/) | `claude -p` + Agent SDK | Cursor SDK (`@cursor/sdk`) + Automations |
| [`codegraph/`](./codegraph/) · [`serena/`](./serena/) | MCP en Claude | Mismos servers vía MCP de Cursor |
| [`gsd/`](./gsd/) | Plugin GSD | **No hay port oficial** — ver nota |
| [`metodologia/`](./metodologia/) | Flujo 11 etapas | Mismo flujo + superficie Cursor |

## Qué NO está (o es distinto) — léelo antes de copiar a ciegas

| Capacidad Claude Code | En Cursor |
|---|---|
| `CLAUDE.md` + `@import` + auto-memory `MEMORY.md` | `AGENTS.md` / `.cursor/rules/`; memories de Cursor **no** son el mismo sistema |
| `/context`, `/compact`, `/clear`, `/rewind` | UI/sesión distintas; no hay esos slash commands 1:1 |
| Allowlist `settings.local.json` (`mcp__*`) | Permisos/approvals de Cursor + hooks |
| Plugins / marketplaces (`/plugin install`) | **No equivalente**; installs = rules/skills/MCP a mano o pack del repo |
| Agent Teams (lead + teammates + inbox) | **No disponible**; usa Task en paralelo |
| GSD como plugin | **Solo Claude Code** hoy; en Cursor usa Plan mode + skills de metodología |
| `claude -p` Unix pipe | Cursor SDK / Automations (API key), no el mismo CLI |
| Skills en `~/.claude/skills/` | `.cursor/skills/` (proyecto) o `~/.cursor/skills/` (usuario) |
| Hooks `PreToolUse` + `exit 2` | Eventos Cursor (`preToolUse`, `afterFileEdit`, …) + JSON `permission` |
| `codegraph install --target=claude` | Configura `.cursor/mcp.json` a mano (o bootstrap del pack) |

Lo que **sí** viaja casi igual: MCP (CodeGraph/Serena/Playwright/Context7), disciplina de 11 etapas,
ledgers `data/changes/`, oráculos `_diag_*.py`, Playwright para contrato, Docker para outbound.
