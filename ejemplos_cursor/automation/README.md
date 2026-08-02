# Automatización (Cursor)

Cuatro niveles, del más ligero al más autónomo — adaptados desde el material Claude Code.

## 1. Hooks (determinista, dentro de la sesión)

Ver [`../hooks/`](../hooks/). Formato, type-check, seguridad, handoff — sin depender de que el modelo
“se acuerde”.

## 2. Headless / scripting — Cursor SDK (no `claude -p`)

Claude Code: `tail -200 app.log | claude -p "…"`.

Cursor: **no hay ese CLI pipe**. El equivalente programático es el **Cursor SDK**
([`sdk.ts`](./sdk.ts)):

```bash
export CURSOR_API_KEY=…   # o configuración del SDK
npx tsx sdk.ts
```

Patrones:

| Necesidad | Cursor SDK |
|---|---|
| One-shot | `Agent.prompt(...)` |
| Multi-turn / stream | `Agent.create` + `agent.send` + `run.stream()` |
| Cloud vs local | `local: { cwd }` vs cloud runtime (docs SDK) |

También existen **Cursor Automations** / Cloud Agents en el producto — distintos del pipe Unix de Claude.

## 3. CI/CD (GitHub Actions)

Ver [`github-action-cursor.yml`](./github-action-cursor.yml) — revisión vía `@cursor/sdk`.

> El workflow original instalaba Claude Code y usaba `claude -p`. Eso **sigue siendo válido solo si
> quieres Claude en CI**. Para Cursor, usa API key del SDK (`CURSOR_API_KEY`), no `ANTHROPIC_API_KEY`
> del CLI de Claude (salvo que tu review sea deliberadamente Claude).

## 4. Tareas programadas

| Claude Code | Cursor |
|---|---|
| Routines `/schedule`, Desktop scheduled tasks, `/loop` | **Automations** / scheduling del producto Cursor (nombres y UI cambian) — no copies `/schedule` literal |
| Loop en sesión CLI | Skill `loop` del entorno Cursor o Automations |

Comprueba la docs actual de Cursor Automations; no asumas parity con Anthropic Routines.

## 5. Agent SDK

[`sdk.ts`](./sdk.ts) — `Agent.prompt` con least privilege conceptual (el modelo de permisos del SDK
no es idéntico a `allowedTools: ["Edit"]` de Claude; revisa la docs `@cursor/sdk` al cablear).

El `query_hook.js` de hooks es “IA revisando IA” con este mismo SDK.
