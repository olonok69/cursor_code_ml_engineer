# Cursor — Curso en tres partes (presentación + guías)

> **Volumen Claude Code:** el curso hermano
> [`claude_code_ml_engineer`](https://github.com/olonok69/claude_code_ml_engineer) —
> mismo curso, mismo método, otra herramienta. Este repo es el **volumen Cursor**.

Material para un **curso/workshop** sobre **Cursor**: una única presentación (`.pptx`) con **tres
partes diferenciadas** y dos guías escritas, con ejemplos reales y ejecutables. En español, orientado a
**desarrolladores**. Es la contrapartida directa del curso de Claude Code — misma estructura, mismos
ejemplos sanitizados, verificados contra `cursor.com/docs` (agosto 2026).

- **Parte 1 — Cursor:** instalación y uso básico · memoria (`AGENTS.md` + rules) e instrucciones ·
  **contexto (context window + prompt caching)** · MCP · **skills y marketplace** · **subagents** ·
  automatización (hooks, Bugbot, Cursor SDK, Automations).
- **Parte 2 — La metodología (agnóstica de la herramienta):** el flujo real de 11 etapas con gates ·
  las herramientas del método (CodeGraph, Serena, GSD, oráculos) · la transferencia — **de Claude Code
  a Cursor**, el ejemplo más real de este curso · la sincronización de máquinas.
- **Parte 3 — El grafo de conocimiento de tickets:** el mismo caso completo construido con **graphify**:
  corpus con manifest, pipeline `kg-refresh`, consulta `kg` sin LLM, la visualización real del grafo
  (507 nodos · 35 comunidades) y su enganche en la metodología — las skills `kg`/`kg-refresh` son el
  **mismo `SKILL.md`** en Cursor y en Claude Code.

## Contenido

| Archivo | Qué es |
|---|---|
| [`GUIA_PRESENTACION.md`](./GUIA_PRESENTACION.md) | Guía narrativa para el/la ponente, en dos partes: hilo a contar por slide + frases de cierre 🗣️ + links al código. |
| [`GUIA_TECNICA.md`](./GUIA_TECNICA.md) | Referencia de implementación copy-paste (configs, comandos, código), en las mismas dos partes. |
| [`DEMO_RUNBOOK.md`](./DEMO_RUNBOOK.md) | Cheatsheet de demos live: preflight, comando/click por slide, tiempos y fallos frecuentes. |
| [`presentacion/Cursor_Presentacion.pptx`](./presentacion/) | El deck (16:9, 36 slides), mismo estilo visual que el deck de Claude Code. |
| [`presentacion/build_pptx_cursor.py`](./presentacion/build_pptx_cursor.py) | Generador del deck (regenerable). |
| [`ejemplos/`](./ejemplos/) | Artefactos reales adaptados a Cursor, agrupados por sección del curso — mismo mapeo que los ejemplos del [curso hermano de Claude Code](https://github.com/olonok69/claude_code_ml_engineer/tree/HEAD/ejemplos). |
| [`docs/`](./docs/) | **Referencia**: documentos de una instalación real donde se aplica la metodología a diario (knowledge graph, adaptación a Cursor/Copilot, runbooks de sync). |

## Ejemplos (por sección del curso)

**Parte 1:**
- [`ejemplos/agents-md/`](./ejemplos/agents-md/) — el patrón de `AGENTS.md` + `.cursor/rules/` de dos niveles (§02).
- [`ejemplos/context/`](./ejemplos/context/) — gestión del context window en Cursor: anatomía, mandos, higiene (§03).
- [`ejemplos/prompt-caching/`](./ejemplos/prompt-caching/) — el mecanismo de caching (API Anthropic) + qué controlas de verdad en Cursor (§03).
- [`ejemplos/mcp/`](./ejemplos/mcp/) — `.cursor/mcp.json` con scopes y secretos por entorno (§04).
- [`ejemplos/skills-plugins/`](./ejemplos/skills-plugins/) — skills en `.cursor/skills/` (§05).
  **Live en este repo:** raíz `.cursor/skills/` (`audit`, `audit-python`, `deploy-staging`).
  **Targets de demo:** [`ex_npm/`](./ex_npm/) (`/audit`) · [`ex_app/`](./ex_app/) (`/audit-python`) · [`ex_staging/`](./ex_staging/) (`/deploy-staging`).
- [`ejemplos/subagents/`](./ejemplos/subagents/) — plantillas de subagent y el diagrama subagent-vs-Background/Cloud Agent (§06).
  **Live:** raíz `.cursor/agents/refactor-scout.md`.
- [`ejemplos/hooks/`](./ejemplos/hooks/) — hooks reales de Cursor (`.cursor/hooks.json`, eventos, permission JSON) + payloads (§07).
- [`ejemplos/permissions/`](./ejemplos/permissions/) — `permissions.json` con `mcpAllowlist` / `terminalAllowlist` (§02/§03).
- [`ejemplos/automation/`](./ejemplos/automation/) — GitHub Action con Cursor, Cursor SDK, Automations (§07).

**Parte 2:**
- [`ejemplos/metodologia/`](./ejemplos/metodologia/) — **el flujo real de 11 etapas, un ejemplo concreto de principio a fin, la prevalencia de tools** (Serena/CodeGraph/Playwright/AWS/Docker/oráculo determinista), el **gate outbound de tres checks**, el **runbook de ops** (sincronizar el workspace entre máquinas, con las notas de adaptación a Cursor) y el diagrama del flujo (§08, §11).
- [`ejemplos/gsd/`](./ejemplos/gsd/) · [`ejemplos/codegraph/`](./ejemplos/codegraph/) · [`ejemplos/serena/`](./ejemplos/serena/) — las herramientas del método en Cursor, en profundidad (§09).
- [`docs/ai-agents-code-methodology/`](./docs/ai-agents-code-methodology/) — el starter-kit portable: [`CURSOR_ADAPTATION.md`](./docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md) + superficie lista para copiar en [`cursor/`](./docs/ai-agents-code-methodology/cursor/) (§10).
- [`docs/synchro/`](./docs/synchro/) — runbooks reales de sincronización entre máquinas (§11).

**Parte 3:**
- [`docs/knowledge-graph/`](./docs/knowledge-graph/) — el grafo de conocimiento de tickets, construido con **graphify**: diseño (`design.md`), scripts (`kg_query.sh`, `kg_refresh.sh`, `build_manifest.py`, `stage_corpus.py`), tests, `manifest.txt` y la **salida real** (`output/graph.html` interactivo + `GRAPH_REPORT.md`) — el mismo artefacto que en el curso Claude Code (§12).
- [`docs/KNOWLEDGE_GRAPH.md`](./docs/KNOWLEDGE_GRAPH.md) — el resumen narrativo del mismo sistema.
- [`presentacion/kg_graph.png`](./presentacion/) — la captura del grafo usada en este deck (mismo grafo real del proyecto).

## Regenerar el deck y los diagramas

```bash
pip install python-pptx pillow
python presentacion/build_pptx_cursor.py       # -> presentacion/Cursor_Presentacion.pptx
python ejemplos/metodologia/render_flow.py     # -> flow.png (flujo de 11 etapas)
python ejemplos/subagents/render_agents.py     # -> agents.png (subagent vs Background/Cloud Agent)
python presentacion/capture_kg_graph.py        # -> kg_graph.png (mismo grafo de tickets; requiere playwright)
```

## Documentación de las tecnologías

| Tecnología | Qué es en el curso | Documentación |
|---|---|---|
| **Cursor** | La herramienta (Parte 1) | <https://docs.cursor.com> · [AGENTS.md](https://docs.cursor.com/context/rules) · [hooks](https://docs.cursor.com/agent/hooks) · [subagents](https://docs.cursor.com/agent/subagents) · [CLI](https://docs.cursor.com/cli/overview) · [SDK](https://docs.cursor.com/background-agent/api/overview) |
| **MCP** | El estándar de conexión (§04) | <https://modelcontextprotocol.io> |
| **Cursor SDK** | Automatización a medida (§07) | <https://docs.cursor.com/background-agent/api/overview> |
| **CodeGraph** | Grafo del código (§09) | <https://colbymchenry.github.io/codegraph/> · [repo](https://github.com/colbymchenry/codegraph) |
| **Serena** | Navegación semántica LSP (§09) | <https://github.com/oraios/serena> |
| **GSD** | El método productizado — solo Claude Code (§09) | <https://github.com/tomascortereal/claude-code-setup> |
| **graphify** | El grafo de tickets (Parte 3) | <https://graphify.net> · [repo](https://github.com/Graphify-Labs/graphify) |
| **Playwright MCP** | Verificación del contrato (§09) | <https://github.com/microsoft/playwright-mcp> |
| **Context7** | Docs de librerías al día (§09) | <https://context7.com> |
| **tree-sitter** | El parser bajo CodeGraph | <https://tree-sitter.github.io/tree-sitter/> |

## Fuentes

Documentación oficial <https://docs.cursor.com> (verificada **9 ago 2026**, 2ª revisión — Cursor cambia
rápido, revisa antes de reutilizar) · GSD <https://github.com/tomascortereal/claude-code-setup> · CodeGraph
<https://colbymchenry.github.io/codegraph/> · Serena <https://github.com/oraios/serena> · graphify
<https://graphify.net>.

> Los ejemplos derivados de un proyecto profesional real están **sanitizados** (sin nombres de cliente,
> IDs de ticket ni secretos).
