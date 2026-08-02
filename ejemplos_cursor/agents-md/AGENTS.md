# AGENTS.md — orientación del proyecto (Cursor)

> **Regla de oro de este fichero:** se carga como orientación de sesión.
> Mantenlo pequeño. Aquí va solo orientación + punteros de una línea; el detalle vive
> en ficheros bajo `data/changes/` que se leen **bajo demanda**.
> Los gates obligatorios viven además en `.cursor/rules/*.mdc` (`alwaysApply: true`).

## Qué es este proyecto

Servicio de extracción de documentos (AWS Lambda, Python 3.12). Convierte PDFs en datos
estructurados y los valida contra un esquema.

## Estructura (repos del workspace)

| Repo | Rol | Permiso |
|---|---|---|
| `document-parser` | **Propiedad** — donde trabajamos. | Editar / commit (push solo si el humano lo pide). |
| `frontend`, `monolith`, `infra` | **Contexto de solo lectura.** | Leer libremente. **No** editar salvo petición explícita; si hace falta un fix, propónlo. |

> No hagas commit/stage desde la raíz del workspace: opera siempre dentro de un repo concreto.

## Comandos

```bash
.venv/bin/pytest tests/ -q          # tests
.venv/bin/python -m parser <pdf>    # ejecutar el parser sobre un fichero
```

## Navegación de código

Orden obligatorio (también en `.cursor/rules/01-tool-prevalence.mdc`):

1. **CodeGraph** `codegraph_explore` primero (survey + blast radius).
2. **Serena** `find_referencing_symbols` **siempre** antes de renombrar/borrar.
3. grep/Read solo para literales.

## Convenciones

- Ramas: `fea/tck-NNNN` (feature) · `fix/tck-NNNN` (bugfix).
- **Confidencialidad:** nunca nombres de cliente, IDs de ticket ni secretos en código/commits.
- **Sin auto-atribución del agente** en artefactos entregados.
- **Plan → agree → implement**; acciones externas = humano (salvo petición explícita).

## Memoria bajo demanda — punteros (NO copiar el detalle aquí)

- Estado vivo por ticket → `data/changes/STATUS.md`
- Lecciones de debugging → `data/changes/PLAYBOOK.md`
- Invariantes / decisiones bloqueadas → `data/changes/SHARP_EDGES.md`
- Política de sanitización → `data/changes/CONVENTIONS.md`
- Plantilla de handover → `data/changes/_HANDOVER_TEMPLATE.md`
- Pack metodología Cursor → `data/changes/ai-agent-methodology/CURSOR_ADAPTATION.md`

<!-- NO añadas un ledger por-ticket aquí: este fichero se carga siempre; mantenlo pequeño.
     Cada registro se escribe UNA vez en su ledger canónico; aquí solo el puntero. -->
