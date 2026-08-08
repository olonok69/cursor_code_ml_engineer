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
| [`context/`](./context/) | Context window / `/compact` | Higiene de contexto + `/summarize` / nueva sesión |
| [`prompt-caching/`](./prompt-caching/) | Caching en Claude Code | Demo API Anthropic + qué controlas en Cursor |
| [`mcp/`](./mcp/) | `.mcp.json` + `claude mcp add` | `.cursor/mcp.json` |
| [`skills-plugins/`](./skills-plugins/) | Slash commands + skills + plugins | Skills en `.cursor/skills/` + Marketplace Cursor |
| [`subagents/`](./subagents/) | Task + Agent Teams | `.cursor/agents/` + built-ins (**sin** Agent Teams) |
| [`hooks/`](./hooks/) | Hooks Claude (`exit 2`) | `.cursor/hooks.json` + permission JSON |
| [`automation/`](./automation/) | `claude -p` + Agent SDK | `agent -p` + Cursor SDK (`@cursor/sdk`) + Automations |
| [`codegraph/`](./codegraph/) · [`serena/`](./serena/) | MCP en Claude | Mismos servers vía MCP de Cursor |
| [`gsd/`](./gsd/) | Plugin GSD | **No hay port oficial** — ver nota |
| [`metodologia/`](./metodologia/) | Flujo 11 etapas | Mismo flujo + superficie Cursor |

## Qué NO está (o es distinto) — léelo antes de copiar a ciegas

| Capacidad Claude Code | En Cursor |
|---|---|
| `CLAUDE.md` + `@import` + auto-memory `MEMORY.md` | `AGENTS.md` / `.cursor/rules/`; Memories de Cursor **no** son el mismo sistema |
| `/context`, `/compact` | Anillo de contexto en UI; `/summarize` (alias `/compress`); resumen automático distinto |
| Allowlist `settings.local.json` (`mcp__*`) | `permissions.json` con `mcpAllowlist` / `terminalAllowlist` (`server:tool`) + hooks |
| Plugins Claude (`/plugin install`) | **Marketplace Cursor** (`cursor.com/marketplace`) — distinto producto; no copies `/plugin` |
| Agent Teams (lead + teammates + inbox) | **No disponible**; usa subagents / Background Agents en paralelo |
| GSD como plugin | **Solo Claude Code** hoy; en Cursor usa Plan mode + skills de metodología |
| `claude -p` Unix pipe (stdin→prompt) | `agent -p` print mode (prompt en argumento; stdout out). No asumas el mismo pipe stdin |
| Skills en `~/.claude/skills/` | `.cursor/skills/` (+ lee `.claude/skills/` por interop) |
| Hooks `PreToolUse` + `exit 2` | Eventos Cursor (`preToolUse`, `afterFileEdit`, …) + JSON `permission` |
| `codegraph install --target=claude` | Configura `.cursor/mcp.json` a mano (o bootstrap del pack) |
| `.claude/agents/*.md` | **Sí hay equivalente:** `.cursor/agents/*.md` (también lee `.claude/agents/`) |

Lo que **sí** viaja casi igual: MCP (CodeGraph/Serena/Playwright/Context7), disciplina de 11 etapas,
ledgers `data/changes/`, oráculos `_diag_*.py`, Playwright para contrato, Docker para outbound.
