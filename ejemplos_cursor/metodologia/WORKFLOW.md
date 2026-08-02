# El flujo real de trabajo con Cursor

> Misma metodología de 11 etapas que en Claude Code; cambia la superficie del agente.
> Principio: **colaborador disciplinado, no autopilot.** El humano posee decisiones y acciones externas.

## El proyecto (contexto sanitizado)

- Servicio de extracción de documentos (AWS Lambda, Python 3.12).
- Repo propio + repos de contexto solo-lectura.
- **Contrato de salida** = `status endpoint` JSON. Ahí se reproducen y verifican bugs.

## Las 11 etapas

![Flujo de trabajo — 11 etapas](./flow.png)

> Diagrama: [`flow.png`](./flow.png). Fuente: [`flow.mmd`](./flow.mmd) · `python render_flow.py`.

1. **Orientar — history-first Y status-first.** Skill **`kg`** (o STATUS fallback) + `STATUS.md` +
   `git`/`gh`. En Cursor: rules always-on apuntan a estos ledgers ([`../agents-md/`](../agents-md/)).
2. **Triaje inbound** — síntoma en el contrato (Playwright/F12). Si no → push back, no código.
3. **Regresión vs. pre-existente** — repro en baseline previo.
4. **Investigar** — CodeGraph → Serena → oráculo `_diag_*.py` antes de gastar el modelo en diagnosticar.
5. **Plan** — **Plan mode** de Cursor; acuerdo humano explícito; opciones rechazadas escritas.
6. **Implementar** — Agent mode; TDD RED → GREEN; cambio mínimo.
7. **Verificar** — unit + scoped + regresión; outbound: wrapper + JSON local + imagen Docker.
8. **Documentar** — write-once en `data/changes/`.
9. **Sanitizar** — skill `sanitise-diff` sobre líneas **añadidas** del staged diff.
10. **Handoff** — el agente **no** hace push/PR/deploy salvo petición explícita (hook
    `block_external` / rules). Prepara rama + handover.
11. **Revisión bot + persistir** — triage hallazgos; `FOLLOWUPS` / `PLAYBOOK`; skill `kg-refresh` si aplica.

## Coste por etapa (igual filosofía)

| # | Etapa | Hechos sin tirada de modelo | Inferencia del agente |
|---|---|---|---|
| 1 | Orientar | `kg` · STATUS · git/gh | sintetizar qué leer |
| 2–3 | Triaje / provenance | contrato · baseline | clasificar |
| 4 | Investigar | CodeGraph · Serena · `_diag` | escribir diag + causa |
| 5–7 | Plan / code / verify | pytest · Docker · Playwright | **caro** (decidir y crear) |
| 8–11 | Docs / sanitise / handoff / persist | grep · bot · kg-refresh | escribir / triagear |

## Memoria de dos niveles

**Nivel 1 — always-on:** `AGENTS.md` + `.cursor/rules/*.mdc` (pequeños, punteros).

**Nivel 2 — on-demand:** `data/changes/` (STATUS, SHARP_EDGES, PLAYBOOK, per-ticket, …).

Write-once: el always-on **apunta**, no copia. Grafo de tickets: skill `kg` sobre artefactos graphify
([`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)).

Pack: [`../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md`](../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md).
