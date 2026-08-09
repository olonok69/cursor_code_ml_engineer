# The real workflow with Cursor

> Same 11-stage methodology as in Claude Code; only the agent surface changes.
> Principle: **disciplined collaborator, not autopilot.** The human owns decisions and external actions.

## The project (sanitized context)

- Document extraction service (AWS Lambda, Python 3.12).
- Own repo + read-only context repos.
- **Output contract** = `status endpoint` JSON. Bugs are reproduced and verified there.

## The 11 stages

![Workflow — 11 stages](./flow.png)

> Diagram: [`flow.png`](./flow.png). Source: [`flow.mmd`](./flow.mmd) · `python render_flow.py`.

1. **Orient — history-first AND status-first.** Skill **`kg`** (or STATUS fallback) + `STATUS.md` +
   `git`/`gh`. In Cursor: always-on rules point at these ledgers ([`../agents-md/`](../agents-md/)).
2. **Inbound triage** — symptom on the contract (Playwright/F12). If not → push back, no code.
3. **Regression vs. pre-existing** — repro on prior baseline.
4. **Investigate** — CodeGraph → Serena → oracle `_diag_*.py` before spending the model on diagnosis.
5. **Plan** — Cursor **Plan mode**; explicit human agreement; rejected options written down.
6. **Implement** — Agent mode; TDD RED → GREEN; minimal change.
7. **Verify** — unit + scoped + regression; outbound (**five checks**): validate the instrument ·
   wrapper · local JSON (member list, not a total) · Docker image · look at the output.
8. **Document** — write-once under `data/changes/`.
9. **Sanitise** — skill `sanitise-diff` on **added** lines of the staged diff.
10. **Handoff** — the agent does **not** push/PR/deploy unless explicitly asked (hook
    `block_external` / rules). Prepares branch + handover.
11. **Bot review + persist** — triage findings; `FOLLOWUPS` / `PLAYBOOK`; skill `kg-refresh` if applicable.

## Cost per stage (same philosophy)

| # | Stage | Facts without a model call | Agent inference |
|---|---|---|---|
| 1 | Orient | `kg` · STATUS · git/gh | synthesize what to read |
| 2–3 | Triage / provenance | contract · baseline | classify |
| 4 | Investigate | CodeGraph · Serena · `_diag` | write diag + root cause |
| 5–7 | Plan / code / verify | pytest · Docker · Playwright | **expensive** (decide and create) |
| 8–11 | Docs / sanitise / handoff / persist | grep · bot · kg-refresh | write / triage |

## Two-level memory

**Level 1 — always-on:** `AGENTS.md` + `.cursor/rules/*.mdc` (small, pointers).

**Level 2 — on-demand:** `data/changes/` (STATUS, SHARP_EDGES, PLAYBOOK, per-ticket, …).

Write-once: always-on **points**, does not copy. Ticket graph: skill `kg` over graphify artifacts
([`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)).

Pack: [`../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md`](../../docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md).
