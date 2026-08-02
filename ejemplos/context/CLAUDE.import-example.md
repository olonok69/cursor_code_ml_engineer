# CLAUDE.md — ejemplo de imports y carga bajo demanda

> Fragmento de ejemplo (sintaxis real) de un CLAUDE.md nivel-1 que usa `@imports` **y** punteros
> en vez de copiar contenido. Compáralo con el patrón completo en [`../claude-md/CLAUDE.md`](../claude-md/CLAUDE.md).
>
> ⚠️ **`@import` y "carga bajo demanda" son mecanismos OPUESTOS, no lo mismo:**
> - **`@ruta`** = **EAGER**: incorpora el contenido **al arrancar** → cuenta contra el contexto *siempre*.
>   Solo para cositas **pequeñas y estables** (aquí: `@README.md`, `@package.json`).
> - **Puntero** (`data/changes/STATUS.md`…) = **LAZY**: el agente lo **lee con `Read` solo cuando hace falta**;
>   coste 0 hasta entonces. Es lo que hace *lean* el nivel 1.
> - **El patrón de dos niveles se implementa con PUNTEROS, no con `@import`.** El proyecto real **no usa `@`
>   para los ledgers** — meterlos con `@import` los cargaría enteros al arrancar y perderías el lean-context.

## Proyecto

API de facturación. Monorepo: `api/` (FastAPI) + `web/` (React). Ver @README.md para el overview
y @package.json para los scripts disponibles.

## Comandos

- Tests: `.venv/bin/pytest tests/ -q` (nunca `pytest` a secas: usa el venv)
- Lint: `npm run lint --workspace=web`

## Reglas

- Antes de renombrar/borrar un símbolo compartido: `codegraph_explore` + Serena
  `find_referencing_symbols` (detalle: una línea aquí, el porqué vive en `data/changes/CONVENTIONS.md`).
- Estado vivo por ticket: `data/changes/STATUS.md` (leer al orientarse, no copiar aquí).

<!--
  Notas sobre la carga:
  - @README.md y @package.json se incorporan al cargar ESTE fichero (import explícito, EAGER).
  - api/CLAUDE.md y web/CLAUDE.md existen pero solo se cargan cuando Claude entra a esas carpetas.
  - Todo lo demás son punteros de una línea: el agente lo lee bajo demanda con Read (LAZY).
  - ANTI-PATRÓN: NO metas los ledgers grandes (STATUS/SHARP_EDGES/PLAYBOOK) con @import -> los cargaría
    enteros al arrancar y matarías el lean-context. Esos van SIEMPRE por puntero + Read.
  - Resultado: nivel 1 pequeño y estable -> menos tokens fijos y mejor prompt caching.
-->
