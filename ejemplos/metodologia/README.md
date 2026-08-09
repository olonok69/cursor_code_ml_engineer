# Metodología real de trabajo con Cursor

> English: [`../metodologia_en/`](../metodologia_en/).

Cómo se aplica la **misma** metodología de 11 etapas del curso (nacida en Claude Code) usando
**Cursor** como agente. No es una plantilla ideal: es el flujo de producción, con la superficie
adaptada (rules, skills, MCP, hooks).

| Archivo | Qué es |
|---|---|
| [`WORKFLOW.md`](./WORKFLOW.md) | Las 11 etapas + memoria de dos niveles, con tools en Cursor. |
| [`EJEMPLO_REAL.md`](./EJEMPLO_REAL.md) | Un caso concreto (campo vacío) por las 11 etapas. |
| [`herramientas.md`](./herramientas.md) | Prevalencia: CodeGraph, Serena, Playwright, skill `kg`, oráculos. |
| [`machine-sync.md`](./machine-sync.md) | Runbook de ops (tarball bring-up + evolución a S3); nota de adaptación Cursor al inicio. |
| [`../../docs/synchro/s3-sync/README.md`](../../docs/synchro/s3-sync/README.md) | Registro de ingeniería compartido sobre S3 (sync vs mount, roles, identidad). |
| [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md) | Grafo de tickets (graphify) — scripts iguales; skill `kg` en Cursor. |
| [`../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md`](../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md) | Pack completo de adaptación. |
| [`flow.png`](./flow.png) | Diagrama del flujo. |

![Flujo de trabajo — 11 etapas](./flow.png)

## Idea central

> **El agente es un colaborador disciplinado, no un autopilot. La autonomía se gana por-decisión.**

Gates deterministas (contrato, oráculo, tests, sanitise, humano en lo externo) — iguales que en Claude Code.

## Superficie Cursor (dónde vive qué)

| Rol | Claude Code | Cursor |
|---|---|---|
| Orientación always-on | `CLAUDE.md` | `AGENTS.md` + `.cursor/rules/` |
| Skills `/kg`, sanitise… | `~/.claude/skills/` | `.cursor/skills/` |
| MCP | `.mcp.json` / `claude mcp add` | `.cursor/mcp.json` |
| Hard gates | hooks + allowlist | `.cursor/hooks.json` |
| Plan gate | Plan mode | **Plan mode** |
| Handoff externo | a menudo “el humano / Cursor” | humano (Cursor *es* el agente → rules/hooks bloquean push) |

## Cómo encaja con las herramientas

- **GSD** ([`../gsd/`](../gsd/)) — plugin **solo Claude Code**; en Cursor usa Plan + skills.
- **Skill `kg`** — mismos scripts graphify; ver pack `cursor/skills/kg`.
- **CodeGraph / Serena / Playwright** — MCP en `.cursor/mcp.json`.
- **Docker** — outbound en imagen desplegada (igual).

## Portabilidad

Starter-kit: [`../../docs/ai-agents-code-methodology/`](../../docs/ai-agents-code-methodology/)
(`CURSOR_ADAPTATION.md` + `bootstrap-cursor-repo.ps1`).
