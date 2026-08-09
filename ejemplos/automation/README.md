# Automatización (Cursor)

Cuatro niveles, del más ligero al más autónomo — adaptados desde el material Claude Code.

## 1. Hooks (determinista, dentro de la sesión)

Ver [`../hooks/`](../hooks/). Formato, type-check, seguridad, handoff — sin depender de que el modelo
“se acuerde”.

## 2. Headless / scripting — `agent -p` y Cursor SDK

Claude Code: `tail -200 app.log | claude -p "…"`.

Cursor CLI print mode (documentado):

```bash
agent -p --trust "resume los cambios de esta rama"
agent -p --trust --output-format text "revisa por seguridad los ficheros tocados vs main"
# Edits en scripts: agent -p --trust --force "…"
# Preferible a asumir que stdin piped se convierte en prompt (no documentado 1:1):
agent -p --trust "Lee app.log (últimas ~200 líneas) y avísame si ves anomalías"
```

Equivalente programático: **Cursor SDK** ([`sdk.ts`](./sdk.ts)):

```bash
export CURSOR_API_KEY=…   # o configuración del SDK
cd ejemplos/automation && npm i && npx tsx sdk.ts
```

Patrones:

| Necesidad | Cursor |
|---|---|
| One-shot CLI | `agent -p "…"` |
| One-shot SDK | `Agent.prompt(...)` |
| Multi-turn / stream | `Agent.create` + `agent.send` + `run.stream()` |
| Cloud vs local | `local: { cwd }` vs cloud runtime (docs SDK) |

También existen **Cursor Automations** / Cloud Agents en el producto.

## 3. CI/CD (GitHub Actions)

Ver [`github-action-cursor.yml`](./github-action-cursor.yml) — revisión vía `@cursor/sdk`.

> El workflow original instalaba Claude Code y usaba `claude -p`. Eso **sigue siendo válido solo si
> quieres Claude en CI**. Para Cursor, usa API key del SDK (`CURSOR_API_KEY`) o el CLI `agent` autenticado,
> no `ANTHROPIC_API_KEY` del CLI de Claude (salvo que tu review sea deliberadamente Claude).

## 4. Tareas programadas

| Claude Code | Cursor |
|---|---|
| Routines `/schedule`, Desktop scheduled tasks, `/loop` | **Automations** / scheduling del producto Cursor + skill `/loop` — no copies `/schedule` literal |
| Loop en sesión CLI | Skill `loop` del entorno Cursor o Automations |

Comprueba la docs actual de Cursor Automations; no asumas parity con Anthropic Routines.

## 5. Agent SDK

[`sdk.ts`](./sdk.ts) — `Agent.prompt` / `Agent.create` (el modelo de permisos del SDK no es idéntico a
`allowedTools: ["Edit"]` de Claude; revisa la docs `@cursor/sdk` al cablear).

El `query_hook.js` de hooks es “IA revisando IA” con este mismo SDK.
