# Metodología real de trabajo con Claude Code

Cómo se usa Claude Code de verdad en un proyecto en producción — **no una plantilla ideal**, sino el
flujo que usamos, sujeto a revisión constante. Sanitizado (sin nombres de cliente, IDs de ticket ni
secretos); las herramientas, gates y organización son los reales.

| Archivo | Qué es |
|---|---|
| [`WORKFLOW.md`](./WORKFLOW.md) | Las 11 etapas + la memoria de dos niveles, con las tools reales. |
| [`EJEMPLO_REAL.md`](./EJEMPLO_REAL.md) | **Un caso concreto de principio a fin** (un bug de "campo vacío") por las 11 etapas. |
| [`herramientas.md`](./herramientas.md) | Prevalencia de tools: qué usa Claude y cuándo (Serena, CodeGraph, Playwright, AWS CLI, oráculo determinista). |
| [`machine-sync.md`](./machine-sync.md) | **Un runbook real de ops**: sincronizar el workspace entre máquinas (copia completa vs. delta), aterrizado por un agente con guardrails. Incluye bring-up desde cero (`bootstrap`) y round-trip de memoria (`snapshot`/`restore`) para el grafo `/kg`. |
| [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md) | El **grafo de tickets** (`/kg`, con **graphify**): CodeGraph pero para tickets/lecciones — la capa de orientación de la etapa 1. |
| [`flow.png`](./flow.png) | El diagrama del flujo, renderizado (gates en coral, la rama roja es STOP). |
| [`flow.mmd`](./flow.mmd) · [`render_flow.py`](./render_flow.py) | Fuente editable (Mermaid) y el script que genera `flow.png` (`python render_flow.py`). |

![Flujo de trabajo — 11 etapas](./flow.png)

## Idea central

> **El agente es un colaborador disciplinado, no un autopilot. La autonomía se gana por-decisión.**

El agente hace la anchura (investigar, planificar, implementar, testear, documentar); el humano es dueño
de las decisiones y de **toda acción externa**. Entre medias, una serie de **gates deterministas**
—contrato de salida, oráculo determinista (sin inferencia), batería de tests, prueba no-op, escaneo de sanitización— convierten
la capacidad bruta del modelo en salida fiable.

## Cómo encaja con las herramientas del repo

- **GSD** ([`../gsd/`](../gsd/)) es este método **productizado**: separa discutir/planificar/ejecutar/
  verificar con estado en `.planning/` y subagentes especializados. **Este proyecto no lo usa a diario**
  (corre el flujo de 11 etapas + `data/changes/`, más afinado a fixes por ticket); GSD encaja mejor en un
  *greenfield* multi-componente con roadmap → fases.
- **`/kg`** (grafo de tickets, [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)) es la capa de
  **orientación** (etapa 1): CodeGraph pero para tickets/lecciones, construido con **graphify** — saca la
  zona de peligro antes de grep.
- **CodeGraph** ([`../codegraph/`](../codegraph/)) y **Serena** son la capa de navegación (etapa 4).
- **Playwright** verifica el contrato de salida (etapa 2 y 7); en la etapa 7, **Docker** re-corre el repro
  **dentro de la imagen desplegada** (los tests en verde no prueban lo que se envía).

## El método es portable (no vive atado a este repo)

La disciplina —plan→acuerdo, contrato de salida, gates de evidencia, "el humano hace lo externo"— es
**agnóstica de la herramienta**. Existe un *starter-kit* portable (plantillas de `STATUS` / `SHARP_EDGES` /
handover / criterios de QA + un script de bootstrap) para llevar estos guardrails a **otro repo** o a
**GitHub Copilot**: viaja la metodología, y las tools concretas (Serena, CodeGraph, `/kg`) se sustituyen por
las del nuevo entorno. Es la misma idea que el runbook de ops de [`machine-sync.md`](./machine-sync.md):
el método se empaqueta y se transporta, no se reinventa en cada sitio.
