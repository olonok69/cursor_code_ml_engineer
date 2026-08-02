# Skills (y qué pasó con plugins / slash commands)

En Claude Code había tres capas: **tools**, **slash commands** (`.claude/commands/`), **skills**
(`.claude/skills/`), más **plugins/marketplaces**. En Cursor la superficie útil es más corta.

## 1. Tools

Lo que el agente puede *hacer*: Read/Edit/Write, Shell, Grep, Glob, WebFetch, **Task** (subagentes),
más tools MCP. El control fino no es el allowlist `allow`/`deny`/`ask` de Claude: son **approvals de
Cursor**, **rules** y **hooks**.

## 2. Skills (el mecanismo principal)

Una skill es una carpeta con `SKILL.md` + frontmatter (`name`, `description`). La `description` guía
la **auto-selección**.

| Scope | Ruta |
|---|---|
| Proyecto (versionable) | `.cursor/skills/<nombre>/SKILL.md` |
| Usuario (todos tus repos) | `~/.cursor/skills/<nombre>/SKILL.md` |

Ejemplos en esta carpeta:

- [`audit/SKILL.md`](./.cursor/skills/audit/SKILL.md) — sustituye al antiguo slash `/audit`
- [`deploy-staging/SKILL.md`](./.cursor/skills/deploy-staging/SKILL.md) — skill de flujo

Pack de metodología: `kg`, `kg-refresh`, `methodology-plan`, `sanitise-diff` en
[`../../docs/ai-agents-code-methodology/cursor/skills/`](../../docs/ai-agents-code-methodology/cursor/skills/).

## 3. Slash commands de Claude — no hay copia 1:1

`.claude/commands/<nombre>.md` → `/nombre` **no existe** igual en Cursor.
**Adaptación:** conviértelo en skill (como `audit`). El usuario puede pedir “corre el skill audit” o
dejar que el agente lo auto-seleccione por `description`.

## 4. Plugins y marketplaces — no disponibles

```text
/plugin marketplace add …   # Claude Code only
/plugin install gsd …
```

Cursor **no** tiene el marketplace de plugins de Claude Code. Distribuye setups como:

1. Carpeta versionada `.cursor/` (rules + skills + mcp + hooks), o
2. El starter-kit [`ai-agents-code-methodology`](../../docs/ai-agents-code-methodology/) + bootstrap.

## 5. Subagents

Ver [`../subagents/`](../subagents/) — tool **Task** con tipos `explore`, `generalPurpose`, etc.
