# AGENTS.md — ejemplo de punteros (lazy) vs carga eager

> Fragmento de ejemplo de un `AGENTS.md` nivel-1. Compáralo con el patrón completo en
> [`../agents-md/AGENTS.md`](../agents-md/AGENTS.md).
>
> ⚠️ En Claude Code existía `@ruta` (**EAGER**: incorpora al arrancar). **Cursor no tiene ese
> `@import` en AGENTS.md.** Aquí solo hay un patrón seguro:
> - **Puntero** (`data/changes/STATUS.md`…) = **LAZY**: el agente lo lee con Read cuando hace falta.
> - **Anti-patrón:** pegar el contenido de STATUS/SHARP_EDGES/PLAYBOOK dentro de AGENTS.md o de una
>   rule `alwaysApply` → lo pagas en **cada** turno.

## Proyecto

API de facturación. Monorepo: `api/` (FastAPI) + `web/` (React).
Overview del repo: lee `README.md` cuando lo necesites (no lo incrustes aquí).
Scripts npm: lee `package.json` on-demand.

## Comandos

- Tests: `.venv/bin/pytest tests/ -q` (nunca `pytest` a secas: usa el venv)
- Lint: `npm run lint --workspace=web`

## Reglas

- Antes de renombrar/borrar un símbolo compartido: `codegraph_explore` + Serena
  `find_referencing_symbols` (el porqué vive en `data/changes/CONVENTIONS.md`).
- Estado vivo por ticket: `data/changes/STATUS.md` (leer al orientarse, no copiar aquí).
- Gates siempre-on: `.cursor/rules/` (metodología).

<!--
  - Todo son punteros de una línea: el agente lee bajo demanda.
  - ANTI-PATRÓN: NO pegues ledgers grandes en AGENTS.md ni en rules alwaysApply.
  - Resultado: nivel 1 pequeño y estable.
-->
