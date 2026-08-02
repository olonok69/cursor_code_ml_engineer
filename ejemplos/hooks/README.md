# Ejemplos de hooks

Hooks reales adaptados del curso de Claude Code de Anthropic. Un **hook** es un comando de shell que
Claude Code ejecuta automáticamente **antes o después** de una acción. Es la forma determinista de
controlar al agente: no le *pides* que formatee o que no lea secretos, lo **fuerzas**.

## El contrato de un hook (lo esencial)

| Concepto | Detalle |
|---|---|
| **Entrada** | El payload JSON del evento llega por **STDIN**. |
| **Evento** | `PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`, `UserPromptSubmit`, `Notification`, … |
| **Matcher** | **Regex sobre el nombre de la tool**: `Read\|Grep`, `Write\|Edit\|MultiEdit`, `*` (todas). |
| **Varios hooks** | Por matcher se ejecutan **en secuencia** (p. ej. formatear y luego type-check). |
| **`timeout`** | En segundos. Súbelo si el hook llama a un modelo (ver `query_hook.js`, 300s). |
| **Salida** | `exit 0` = permite · **`exit 2` = BLOQUEA** y devuelve `stderr` a Claude como feedback. |

## Pre vs Post — qué datos recibes

- **`PreToolUse`** te da `tool_input` (la *intención*, antes de ejecutar) → puedes **bloquear**.
- **`PostToolUse`** añade `tool_response` (el *resultado* real, con `structuredPatch`) → reaccionas/formateas/verificas.

Por eso los scripts leen `tool_response?.filePath` después de editar, pero `tool_input?.file_path` antes.
Ver [`pre-log.json`](./pre-log.json) y [`post-log.json`](./post-log.json) capturados con `log_hook.js`.

## Los scripts

| Script | Evento / matcher | Qué hace | ¿Bloquea? |
|---|---|---|---|
| [`read_hook.js`](./read_hook.js) | PreToolUse · `Read\|Grep` | Seguridad: impide leer `.env`. | Sí (exit 2) |
| [`log_hook.js`](./log_hook.js) | Pre + Post · `*` | Observabilidad: vuelca el payload a un JSON. | No |
| [`format_hook.js`](./format_hook.js) | PostToolUse · edits | Calidad: `prettier --write` sobre el fichero editado. | No (a propósito) |
| [`tsc.js`](./tsc.js) | PostToolUse · edits | Calidad: type-check; corta si no compila. | Sí (exit 2) |
| [`query_hook.js`](./query_hook.js) | PreToolUse · edits | "IA revisando IA": llama al Agent SDK para detectar queries duplicadas. | Sí (exit 2) |

## Cómo enganchar todo

Copia [`settings.json`](./settings.json) a `.claude/settings.json` (compartido en el repo) o a
`.claude/settings.local.json` (personal, no versionado) y ajusta las rutas de los scripts.

> **Truco de distribución** (del curso): si tus hooks necesitan rutas absolutas, guarda un
> `settings.example.json` con un token `$PWD` y un pequeño `scripts/init-claude.js` que lo sustituya por
> `process.cwd()` al hacer `npm run setup`. Así el config es portable entre máquinas.
