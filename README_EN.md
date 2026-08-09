# Cursor — A course in three parts (deck + guides)

> English version of [`README.md`](./README.md). English deliverables:
> [`GUIA_PRESENTACION_EN.md`](./GUIA_PRESENTACION_EN.md) (speaker guide),
> [`GUIA_TECNICA_EN.md`](./GUIA_TECNICA_EN.md) (technical reference),
> [`DEMO_RUNBOOK_EN.md`](./DEMO_RUNBOOK_EN.md) (live-demo cheatsheet),
> [`presentacion/Cursor_Presentacion_EN.pptx`](./presentacion/) (the deck), and
> [`ejemplos/metodologia_en/`](./ejemplos/metodologia_en/) (methodology walkthrough in English).
>
> Prefer Spanish? Use the originals: [`README.md`](./README.md),
> [`GUIA_PRESENTACION.md`](./GUIA_PRESENTACION.md), [`GUIA_TECNICA.md`](./GUIA_TECNICA.md),
> [`DEMO_RUNBOOK.md`](./DEMO_RUNBOOK.md), [`presentacion/Cursor_Presentacion.pptx`](./presentacion/),
> [`ejemplos/metodologia/`](./ejemplos/metodologia/).

> **Claude Code volume:** the sibling course
> [`claude_code_ml_engineer`](https://github.com/olonok69/claude_code_ml_engineer) —
> same course, same method, different tool. This repo is the **Cursor volume**.

Material for a **course/workshop** on **Cursor**: a single presentation (`.pptx`) with **three
distinct parts**, two written guides, and real, runnable examples. Aimed at **developers**. Direct
counterpart of the Claude Code course — same structure, same sanitized examples, checked against
`cursor.com/docs` (August 2026).

- **Part 1 — Cursor:** installation and basic usage · memory (`AGENTS.md` + rules) and instructions ·
  **context (context window + prompt caching)** · MCP · **skills and marketplace** · **subagents** ·
  automation (hooks, Bugbot, Cursor SDK, Automations).
- **Part 2 — The methodology (tool-agnostic):** the real 11-stage workflow with gates · the method's
  tools (CodeGraph, Serena, GSD, oracles) · the transfer — **from Claude Code to Cursor**, the most
  real example in this course · machine sync **and the shared engineering record over S3**. The
  outbound gate is **five checks** (validate the instrument · contract via *wrapper* · member list,
  not totals · deployed image · look at the output).
- **Part 3 — The ticket knowledge graph:** the same complete case built with **graphify**:
  corpus with manifest, `kg-refresh` pipeline, zero-LLM `kg` query, the real graph visualization
  (507 nodes · 35 communities) and where it hooks into the methodology — the `kg` / `kg-refresh`
  skills are the **same `SKILL.md`** in Cursor and in Claude Code.

## Contents

| File | What it is |
|---|---|
| [`GUIA_PRESENTACION_EN.md`](./GUIA_PRESENTACION_EN.md) | Speaker guide: narrative per slide + closing one-liners 🗣️ + links to the code. |
| [`GUIA_TECNICA_EN.md`](./GUIA_TECNICA_EN.md) | Copy-paste implementation reference (configs, commands, code). |
| [`DEMO_RUNBOOK_EN.md`](./DEMO_RUNBOOK_EN.md) | Live-demo cheatsheet: preflight, click/command per slide, timings, common failures. |
| [`presentacion/Cursor_Presentacion_EN.pptx`](./presentacion/) | The English deck (16:9, 36 slides), same visual style as the Claude Code deck. |
| [`presentacion/build_pptx_cursor_en.py`](./presentacion/build_pptx_cursor_en.py) | Generator for the English deck (regenerable). |
| [`ejemplos/metodologia_en/`](./ejemplos/metodologia_en/) | English methodology pack: 11-stage flow, end-to-end example, five-check outbound gate, S3 sync notes. |
| [`ejemplos/`](./ejemplos/) | Real artifacts adapted for Cursor, grouped by course section — same mapping as the [sibling Claude Code course](https://github.com/olonok69/claude_code_ml_engineer/tree/HEAD/ejemplos) (mostly Spanish filenames; methodology also under `metodologia_en/`). |
| [`docs/`](./docs/) | **Reference**: documents from a real installation where the methodology is applied daily (knowledge graph, Cursor/Copilot adaptation, sync runbooks). |

Spanish originals of the guides and deck remain at [`README.md`](./README.md) and the paths listed in the banner above.

## Examples (by course section)

**Part 1:**
- [`ejemplos/agents-md/`](./ejemplos/agents-md/) — the two-level `AGENTS.md` + `.cursor/rules/` pattern (§02).
- [`ejemplos/context/`](./ejemplos/context/) — context-window management in Cursor: anatomy, controls, hygiene (§03).
- [`ejemplos/prompt-caching/`](./ejemplos/prompt-caching/) — the caching mechanism (Anthropic API) + what you actually control in Cursor (§03).
- [`ejemplos/mcp/`](./ejemplos/mcp/) — `.cursor/mcp.json` with scopes and per-environment secrets (§04).
- [`ejemplos/skills-plugins/`](./ejemplos/skills-plugins/) — skills under `.cursor/skills/` (§05).
  **Live in this repo:** root `.cursor/skills/` (`audit`, `audit-python`, `deploy-staging`).
  **Demo targets:** [`ex_npm/`](./ex_npm/) (`/audit`) · [`ex_app/`](./ex_app/) (`/audit-python`) · [`ex_staging/`](./ex_staging/) (`/deploy-staging`).
- [`ejemplos/subagents/`](./ejemplos/subagents/) — subagent templates and the subagent-vs-Background/Cloud Agent diagram (§06).
  **Live:** root `.cursor/agents/refactor-scout.md`.
- [`ejemplos/hooks/`](./ejemplos/hooks/) — real Cursor hooks (`.cursor/hooks.json`, events, permission JSON) + payloads (§07).
- [`ejemplos/permissions/`](./ejemplos/permissions/) — `permissions.json` with `mcpAllowlist` / `terminalAllowlist` (§02/§03).
- [`ejemplos/automation/`](./ejemplos/automation/) — GitHub Action with Cursor, Cursor SDK, Automations (§07).

**Part 2:**
- [`ejemplos/metodologia_en/`](./ejemplos/metodologia_en/) — **the real 11-stage flow, one concrete end-to-end example, tool prevalence** (Serena/CodeGraph/Playwright/AWS/Docker/deterministic oracle), the **five-check outbound gate** (validate the instrument · contract via *wrapper* · member list, not totals · deployed image · look at the output), the **ops runbook** (sync the workspace across machines — and its evolution to a shared record — with Cursor adaptation notes) and the flow diagram (§08, §11). Spanish original: [`ejemplos/metodologia/`](./ejemplos/metodologia/).
- [`ejemplos/gsd/`](./ejemplos/gsd/) · [`ejemplos/codegraph/`](./ejemplos/codegraph/) · [`ejemplos/serena/`](./ejemplos/serena/) — the method's tools in Cursor, in depth (§09).
- [`docs/ai-agents-code-methodology/`](./docs/ai-agents-code-methodology/) — the portable starter-kit: [`CURSOR_ADAPTATION.md`](./docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md) + ready-to-copy surface under [`cursor/`](./docs/ai-agents-code-methodology/cursor/) (§10).
- [`docs/synchro/`](./docs/synchro/) — real sync runbooks: `machine-sync/` (tarball+USB, full bring-up), `ils-to-main/` (delta back), and **`s3-sync/`** (the shared engineering record over S3: sync vs read-only mount, publisher/contributor roles, per-machine identity) (§11).

**Part 3:**
- [`docs/knowledge-graph/`](./docs/knowledge-graph/) — the ticket knowledge graph, built with **graphify**: design (`design.md`), scripts (`kg_query.sh`, `kg_refresh.sh`, `build_manifest.py`, `stage_corpus.py`), tests, `manifest.txt` and the **real output** (interactive `output/graph.html` + `GRAPH_REPORT.md`) — the same artifact as in the Claude Code course (§12).
- [`docs/KNOWLEDGE_GRAPH.md`](./docs/KNOWLEDGE_GRAPH.md) — narrative summary of the same system.
- [`presentacion/kg_graph.png`](./presentacion/) — the graph capture used in this deck (same real project graph).

## Regenerating the deck and diagrams

```bash
pip install python-pptx pillow
python presentacion/build_pptx_cursor_en.py    # -> presentacion/Cursor_Presentacion_EN.pptx
python ejemplos/metodologia_en/render_flow.py  # -> flow.png (11-stage workflow)
python ejemplos/subagents/render_agents.py     # -> agents.png (subagent vs Background/Cloud Agent)
python presentacion/capture_kg_graph.py        # -> kg_graph.png (same ticket graph; needs playwright)
```

Spanish deck / methodology diagram:

```bash
python presentacion/build_pptx_cursor.py       # -> presentacion/Cursor_Presentacion.pptx
python ejemplos/metodologia/render_flow.py     # -> flow.png (Spanish metodologia pack)
```

## Technology documentation

| Technology | Role in the course | Documentation |
|---|---|---|
| **Cursor** | The tool (Part 1) | <https://docs.cursor.com> · [AGENTS.md](https://docs.cursor.com/context/rules) · [hooks](https://docs.cursor.com/agent/hooks) · [subagents](https://docs.cursor.com/agent/subagents) · [CLI](https://docs.cursor.com/cli/overview) · [SDK](https://docs.cursor.com/background-agent/api/overview) |
| **MCP** | The connection standard (§04) | <https://modelcontextprotocol.io> |
| **Cursor SDK** | Custom automation (§07) | <https://docs.cursor.com/background-agent/api/overview> |
| **CodeGraph** | The code graph (§09) | <https://colbymchenry.github.io/codegraph/> · [repo](https://github.com/colbymchenry/codegraph) |
| **Serena** | Semantic LSP navigation (§09) | <https://github.com/oraios/serena> |
| **GSD** | The productized method — Claude Code only (§09) | <https://github.com/tomascortereal/claude-code-setup> |
| **graphify** | The ticket knowledge graph (Part 3) | <https://graphify.net> · [repo](https://github.com/Graphify-Labs/graphify) |
| **Playwright MCP** | Contract verification (§09) | <https://github.com/microsoft/playwright-mcp> |
| **Context7** | Up-to-date library docs (§09) | <https://context7.com> |
| **tree-sitter** | The parser under CodeGraph | <https://tree-sitter.github.io/tree-sitter/> |

## Sources

Official docs <https://docs.cursor.com> (verified **9 Aug 2026**, 2nd pass — Cursor moves fast, re-check
before reuse) · GSD <https://github.com/tomascortereal/claude-code-setup> · CodeGraph
<https://colbymchenry.github.io/codegraph/> · Serena <https://github.com/oraios/serena> · graphify
<https://graphify.net>.

> Examples derived from a real professional project are **sanitized** (no client names, ticket IDs or
> secrets).
