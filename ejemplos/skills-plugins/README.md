# Skills (y qué pasó con plugins / slash commands)

En Claude Code había tres capas: **tools**, **slash commands** (`.claude/commands/`), **skills**
(`.claude/skills/`), más **plugins/marketplaces**. En Cursor la superficie útil es distinta — y ya no
es “todo falta”: Skills y Marketplace existen.

## 1. Tools

Lo que el agente puede *hacer*: Read/Edit/Write, Shell, Grep, Glob, WebFetch, **Task** (subagentes),
más tools MCP. Control fino: **`permissions.json`** (`mcpAllowlist` / `terminalAllowlist`), **approvals
de Cursor**, **rules** y **hooks**.

## 2. Skills (el mecanismo principal)

Una skill es una carpeta con `SKILL.md` + frontmatter (`name`, `description`). La `description` guía
la **auto-selección**. También se invocan con `/nombre` en Agent chat.

| Scope | Ruta |
|---|---|
| Proyecto (versionable) | `.cursor/skills/<nombre>/SKILL.md` |
| Usuario (todos tus repos) | `~/.cursor/skills/<nombre>/SKILL.md` |
| Interop Claude / Codex | `.claude/skills/`, `.codex/skills/` (Cursor las carga también) |

Ejemplos en esta carpeta:

- [`audit/SKILL.md`](./.cursor/skills/audit/SKILL.md) — sustituye al antiguo slash `/audit`
- [`deploy-staging/SKILL.md`](./.cursor/skills/deploy-staging/SKILL.md) — skill de flujo

Pack de metodología: `kg`, `kg-refresh`, `methodology-plan`, `sanitise-diff` en
[`../../docs/ai-agents-code-methodology/cursor/skills/`](../../docs/ai-agents-code-methodology/cursor/skills/).

## 3. Slash commands de Claude — no hay copia 1:1

`.claude/commands/<nombre>.md` → `/nombre` **no existe** igual en Cursor.
**Adaptación:** conviértelo en skill (como `audit`). El usuario puede pedir “corre el skill audit”,
tipear `/audit`, o dejar que el agente lo auto-seleccione por `description`.

## 4. Marketplace — sí en Cursor (distinto del de Claude)

```text
/plugin marketplace add …   # Claude Code only — no copies este comando
```

Cursor tiene **`cursor.com/marketplace`**: paquetes instalables de skills + subagents + MCP + hooks +
rules desde la UI del producto. No hay `/plugin install`. Para setups de equipo también sirve:

1. Carpeta versionada `.cursor/` (rules + skills + mcp + hooks + agents), o
2. El starter-kit [`ai-agents-code-methodology`](../../docs/ai-agents-code-methodology/) + bootstrap.

## 5. Subagents

Ver [`../subagents/`](../subagents/) — built-ins + **`.cursor/agents/*.md`** para roles custom.
