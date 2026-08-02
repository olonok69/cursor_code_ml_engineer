# GSD — "Get Stuff Done" — **solo Claude Code (hoy)**

Setup de Claude Code para gestión de proyectos por fases, instalado como **plugin** del marketplace
de Claude. Repo: https://github.com/tomascortereal/claude-code-setup

## Estado en Cursor

| Pieza GSD | ¿En Cursor? |
|---|---|
| Plugin `/plugin install` + skills `gsd-*` | **No** — no hay marketplace de plugins Claude |
| Ciclo discuss → plan → execute → verify | **Sí como disciplina** — Plan mode + skills propias |
| Estado en `.planning/` | Puedes adoptar la carpeta a mano; nadie te instala los comandos |
| Subagentes `gsd-planner`, `gsd-executor`, … | Sustituye por Task + prompts/skills con esos roles |

**Conclusión para el curso Cursor:** enseña GSD como *referencia* del método productizado en Claude Code,
y en Cursor usa:

1. **Plan mode** + skill `methodology-plan` (pack metodología).
2. Flujo de 11 etapas + `data/changes/` ([`../metodologia/`](../metodologia/)).
3. Task subagents para plan-check / verify si quieres paralelizar.

No digas “instala GSD en Cursor” — **no hay port oficial** en este material.

## La idea (sigue siendo válida)

En vez de “chatear”, un ciclo con gates y estado durable:

```
discutir → planificar (gate) → ejecutar → verificar (evidencia)
```

Artefactos típicos en `.planning/`: `PROJECT.md`, `ROADMAP.md`, `PLAN.md`, `VERIFICATION.md`.

## Por qué encaja con la metodología

GSD encarna plan → acuerdo → implementar y verificar con evidencia. En el proyecto de la Parte 2
**no se usa GSD a diario** (corre 11 etapas + `data/changes/`). GSD brilla en **greenfield**
multi-componente. En Cursor, replica los gates sin el plugin.
