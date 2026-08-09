# Ejemplos de hooks (Cursor)

Un **hook** en Cursor es un comando (o prompt) que se ejecuta en eventos del agente
(`preToolUse`, `afterFileEdit`, `beforeShellExecution`, …). Es la forma determinista de
controlar al agente: no le *pides* que formatee o que no lea secretos, lo **fuerzas**.

> Los scripts de esta carpeta están adaptados desde los ejemplos del curso Claude Code
> (`PreToolUse` / `PostToolUse` + `exit 2`). El contrato de Cursor es distinto (ver abajo).

## El contrato Cursor (lo esencial)

| Concepto | Detalle |
|---|---|
| **Config** | `.cursor/hooks.json` (proyecto) o `~/.cursor/hooks.json` (usuario) |
| **Entrada** | Payload JSON por **STDIN** |
| **Salida** | JSON en stdout (`permission`, `user_message`, `agent_message`, …) **o** `exit 2` = deny |
| **Eventos útiles** | `preToolUse`, `postToolUse`, `beforeReadFile`, `afterFileEdit`, `beforeShellExecution`, `beforeMCPExecution`, … |
| **Matcher** | Regex JS sobre tipo de tool / comando (no el mismo matcher Claude `Read\|Grep`) |
| **`failClosed`** | Si el hook crashea, bloquear en vez de fail-open |

Docs de producto: skill interna `create-hook` / docs Cursor Hooks.

## Mapa Claude → Cursor

| Ejemplo Claude | Evento Cursor recomendado | Script |
|---|---|---|
| PreToolUse Read\|Grep → bloquear `.env` | `beforeReadFile` / `preToolUse` | [`read_hook.js`](./read_hook.js) |
| Pre+Post log payload | `preToolUse` + `postToolUse` | [`log_hook.js`](./log_hook.js) |
| PostToolUse format prettier | `afterFileEdit` | [`format_hook.js`](./format_hook.js) |
| PostToolUse tsc bloqueante | `afterFileEdit` | [`tsc.js`](./tsc.js) |
| PreToolUse “IA revisa IA” (SDK) | `preToolUse` | [`query_hook.js`](./query_hook.js) — **usa Cursor SDK**; ver nota |
| (metodología) bloquear push/deploy | `beforeShellExecution` | pack: `block-external-git.ps1` |

## Cómo enganchar todo

1. Copia los scripts a `.cursor/hooks/` en tu repo (o deja rutas relativas desde la raíz).
2. Copia [`hooks.json.example`](./hooks.json.example) → `.cursor/hooks.json` y ajusta paths.
3. Recarga Cursor; verifica en **Hooks** settings / output channel.

## Diferencias que importan

1. **Payload:** Cursor no garantiza `tool_input.file_path` / `tool_response.filePath` de Claude. Los scripts prueban varios campos (`path`, `filePath`, `file_path`, `uri`).
2. **Bloqueo:** para demos y gates de handoff usa **`permission: "deny"`** (fiable). `"ask"` existe en la API pero a menudo se ignora — no lo uses si el demo es “el hook para el push”. `exit 2` también deniega.
3. **ESM:** los hooks con top-level `await` necesitan `import` (o `.mjs`) para que Node los trate como módulo — ver `block_external.js` / `read_hook.js`.
4. **`query_hook.js`:** el original llamaba `@anthropic-ai/claude-agent-sdk`. Aquí usa `@cursor/sdk` (`Agent.prompt`). Necesitas `CURSOR_API_KEY` y el paquete instalado — es el ejemplo avanzado; desactívalo si no lo quieres en el curso.
5. **`tsc.js`:** necesita `typescript` en el PATH del proyecto (`npx tsc` / deps locales). Sin `package.json` en esta carpeta de ejemplos, es demo de patrón, no CI listo.
6. No copies `.claude/settings.json` hooks a Cursor sin reescribir eventos.
