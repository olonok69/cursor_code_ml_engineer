# DEMO_RUNBOOK — Cursor presentation (36 slides)

Runbook for the **presenter**. Commands verified on Windows (PowerShell) on 9 Aug 2026.
Speaker guide: [`GUIA_PRESENTACION_EN.md`](./GUIA_PRESENTACION_EN.md) · Deck:
[`presentacion/Cursor_Presentacion_EN.pptx`](./presentacion/Cursor_Presentacion_EN.pptx).

Spanish originals: [`DEMO_RUNBOOK.md`](./DEMO_RUNBOOK.md) ·
[`GUIA_PRESENTACION.md`](./GUIA_PRESENTACION.md) ·
[`presentacion/Cursor_Presentacion.pptx`](./presentacion/Cursor_Presentacion.pptx).

## Skills / subagents / hooks — live in *this* repo

Cursor only auto-loads from the **workspace root**:

- `.cursor/skills/*/SKILL.md`
- `.cursor/agents/*.md`
- `.cursor/rules/*.mdc`
- `.cursor/hooks.json` + scripts
- `.cursor/mcp.json`

The teaching copies under `ejemplos/**/.cursor/` are **not** loaded until copied. This repo’s root
`.cursor/` is already wired from those examples (plus lean `AGENTS.md`).

**After opening `D:\repos3\cursor_code` in Cursor → Reload Window**, try:

| What | How |
|---|---|
| Skill **npm** | `/audit @ex_npm` (Express mini-app + `npm test`) |
| Skill **Python** | `/audit-python @ex_app` (Streamlit TS forecasting + `pip-audit`) |
| Skill **staging** | `/deploy-staging @ex_staging` (tests → build → **asks OK** → local deploy → smoke) |
| Subagent | “Launch the **refactor-scout** subagent on the `Agent` symbol in `ejemplos/automation/sdk.ts`” |
| Rule | Always on: `00-lean-memory` (no need to invoke it) |
| Hook `.env` | In Agent: “read the `.env` file” → must **deny** |
| Hook push | “run `git push`” → must **deny** |
| MCP | Customize → MCP: `context7`, `playwright` green · “use context7 for python-pptx docs” |

### Skill targets (audit + deploy)

| Skill | Target | Stack | What it does |
|---|---|---|---|
| `/audit` | [`ex_npm/`](./ex_npm/) | Node + Express | `npm audit` → safe fix → `npm test` |
| `/audit-python` | [`ex_app/`](./ex_app/) | Python + Streamlit | `pip-audit -r requirements.txt` → smoke |
| `/deploy-staging` | [`ex_staging/`](./ex_staging/) | Node (no Express) | `npm test` → `build` → **human confirmation** → `deploy:staging` → `GET /health` |

**Preflight for those targets (T1):**

```powershell
cd D:\repos3\cursor_code\ex_npm
npm install
npm test
npm audit

cd D:\repos3\cursor_code\ex_app
python -m pip install pip-audit
python -m pip_audit -r requirements.txt

cd D:\repos3\cursor_code\ex_staging
npm test
npm run build
# optional dry-run (no skill): npm run deploy:staging ; curl health ; npm run staging:stop
```

In Agent chat (after Reload):

```text
/audit @ex_npm
/audit-python @ex_app
/deploy-staging @ex_staging
```

On `/deploy-staging`, the agent **must stop** before `npm run deploy:staging` and wait for your OK.
“Staging” is a local server (writes `.staging-url`); there is no cloud.

Teaching copies: `ejemplos/skills-plugins/.cursor/skills/{audit,audit-python,deploy-staging}/`.
Live copies: `.cursor/skills/{audit,audit-python,deploy-staging}/`.

**Better on DPL** (`document-parser-lambda`): CodeGraph, Serena, skills `kg` / `methodology-plan` — this
course repo is not a product app with an index.

---

## Before you start (5 min)

**Suggested terminals**


| #   | Open at                                  | For                       |
| --- | ---------------------------------------- | ------------------------- |
| T1  | `D:\repos3\cursor_code`                  | Part 1 demos + kg         |
| T2  | `D:\repos3\ILS_2\document-parser-lambda` | Part 2 MCP / methodology  |
| T3  | (optional) Cursor IDE on T2              | Green MCP + skills        |


**Load keys (T1)**

```powershell
cd D:\repos3\cursor_code
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k,$v = $_.Split('=',2)
  Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim()
}
agent status   # or CURSOR_API_KEY alone is enough for -p
docker ps      # Engine up
```

**Preflight**


| Check                                          | OK if…                                         |
| ---------------------------------------------- | ---------------------------------------------- |
| `python ejemplos\prompt-caching\cache_demo.py` | 2nd call `cache_read > 0`                      |
| `agent -p --trust --mode ask "say OK"`         | prints OK                                      |
| `bash docs/knowledge-graph/kg_query.sh SST`    | graph nodes                                    |
| Cursor on DPL → MCP                            | codegraph/serena/playwright/context7 **green** |
| `codegraph status` on DPL                      | index present                                  |


**Not live demos (slide / explanation only)**

- `ejemplos/gsd/` — Claude Code only
- Bugbot / Automations / Cloud Agents — product UI or cloud account
- `hooks/query_hook.js`, `tsc.js`, `format_hook.js` — pattern; not CI for this repo
- Full `kg_refresh` — slow; use the already-generated graph

---



## Part 1 — Cursor (slides 1–19)


| Slide | Topic                      | Demo (click / command)                                                                                                                                                | Artifact               |
| ----- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1–3   | Cover / agenda / divider   | Deck only                                                                                                                                                             | —                      |
| 4–5   | Install + CLI              | T1: `agent --version` · `agent -p --trust --mode ask "Reply: OK-CURSOR-CLI"`                                                                                          | CLI                    |
| 6–7   | Memory + permissions       | Open `ejemplos/agents-md/AGENTS.md` + `.cursor/rules/00-lean-memory.mdc` · show `ejemplos/permissions/permissions.json.example`                                       | agents-md, permissions |
| 8     | Sessions                   | Cursor UI: chat / Agent / Plan · mention `cursor.com/agents`                                                                                                          | —                      |
| 9–11  | Context window             | Open `ejemplos/context/README.md` + `AGENTS.pointers-example.md` · in chat: `/summarize`                                                                              | context                |
| 12    | Prompt caching             | T1: `python ejemplos\prompt-caching\cache_demo.py` · point out write→read                                                                                             | prompt-caching         |
| 13    | MCP                        | Open `ejemplos/mcp/mcp.json.example` · Cursor → MCP (day-to-day servers; supabase = optional)                                                                         | mcp                    |
| 14    | Skills                     | Live: `/audit @ex_npm` · `/audit-python @ex_app` · `/deploy-staging @ex_staging` · Marketplace | skills-plugins, ex_npm, ex_app, ex_staging |
| 15–17 | Subagents                  | Open `.cursor/agents/refactor-scout.md` · show `ejemplos/subagents/agents.png` · **say**: no Agent Teams; Cloud = `cursor.com/agents` (not `--background`)            | subagents              |
| 18    | Hooks                      | T1:                                                                                                                                                                   | hooks                  |
|       |                            | `'{"path":".env"}' | node ejemplos\hooks\read_hook.js`                                                                                                                |                        |
|       |                            | `'{"command":"git push"}' | node ejemplos\hooks\block_external.js`                                                                                                    |                        |
|       |                            | Expected: `permission: deny`                                                                                                                                          |                        |
| 19    | Automation / SDK           | T1: `cd ejemplos\automation; npx tsx sdk.ts` (or short prompt) · Action YAML open only                                                                                | automation             |


**PowerShell one-liners for hooks (Windows)**

```powershell
'{"path":"D:/repos3/cursor_code/.env"}' | node ejemplos\hooks\read_hook.js
'{"command":"git push origin HEAD"}' | node ejemplos\hooks\block_external.js
'{"command":"git status"}' | node ejemplos\hooks\block_external.js
```

---



## Part 2 — Methodology (slides 20–30)

**Workspace:** Cursor open on `D:\repos3\ILS_2\document-parser-lambda` (not the parent `ILS_2`).

English presenters: open the same files under [`ejemplos/metodologia_en/`](./ejemplos/metodologia_en/)
instead of `ejemplos/metodologia/` where noted below.


| Slide | Topic                       | Demo                                                                                                                       | Artifact          |
| ----- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 20    | Part 2 divider              | Deck only                                                                                                                  | —                 |
| 21–23 | 11-stage flow + example     | Open `ejemplos/metodologia_en/flow.png` · `WORKFLOW.md` · 2 min of `REAL_EXAMPLE.md`                                         | metodologia_en    |
| 24–25 | CodeGraph / Serena          | On DPL chat: *“use CodeGraph to locate X”* · or T2: `codegraph explore "<symbol>"` · Serena via MCP `find_symbol`          | codegraph, serena |
| 26    | GSD                         | **Slide only** — “no Cursor port; Plan mode + skills”                                                                      | gsd               |
| 27–28 | Playwright / prevalence     | Playwright MCP smoke (navigate + snapshot) · open `ejemplos/metodologia_en/tools.md` · runbook `AGENT_SETUP_TOOLS.md` | metodologia_en, docs |
| 29    | Transfer Claude→Cursor     | Open `docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md` · `cursor/` folder (rules/skills/hooks)                        | pack              |
| 30    | Machine sync + S3           | Open `ejemplos/metodologia_en/machine-sync.md` (§ evolution) · `docs/synchro/s3-sync/README.md` (1 screen)               | synchro           |


**If MCP is not green:** follow `docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md` (Reload Window, pin CodeGraph path, restart Cursor after `npm i -g codegraph`).

---



## Part 3 — Ticket graph (slides 31–36)

**Workspace:** T1 `cursor_code` (the course graph lives here).


| Slide | Topic           | Demo                                                                                                             | Artifact        |
| ----- | --------------- | ---------------------------------------------------------------------------------------------------------------- | --------------- |
| 31    | Part 3 divider  | Deck only                                                                                                        | —               |
| 32    | KG idea         | Open `docs/KNOWLEDGE_GRAPH.md` (1 min)                                                                           | docs            |
| 33    | Pipeline        | Show `docs/knowledge-graph/` (`build_manifest`, `stage_corpus`, `kg_refresh.sh`) — **do not** run refresh live   | knowledge-graph |
| 34    | Live query      | T1: `bash docs/knowledge-graph/kg_query.sh SST` · second query with an ID that appears                           | kg_query.sh     |
| 35    | Visual          | Open `docs/knowledge-graph/output/graph.html` in browser · or slide with `presentacion/kg_graph.png`             | graph.html      |
| 36    | Close           | Recap: tool (Cursor) + method (11 stages) + memory (graph)                                                       | —               |


```powershell
cd D:\repos3\cursor_code
bash docs/knowledge-graph/kg_query.sh SST
# optional: open the HTML
start docs\knowledge-graph\output\graph.html
```

---



## Suggested timed order (~90–120 min)


| Block      | Slides | Time      | Must-run demos                                      |
| ---------- | ------ | --------- | --------------------------------------------------- |
| Part 1     | 1–19   | 40–50 min | `agent -p`, cache_demo, hooks deny, skill file, SDK |
| Part 2     | 20–30  | 30–40 min | flow.png + 1 MCP tool on DPL + transfer pack      |
| Part 3     | 31–36  | 15–20 min | `kg_query` + graph.html                             |
| Q&A buffer | —      | 10 min    | —                                                   |


**If short on time:** cut Cloud Agents UI, machine sync to 1 sentence, GSD to 30 s, skip SDK (keep `agent -p`).

**If time left:** on DPL run skill `/kg` or Plan mode with `methodology-plan`.

---



## Common-failure cheat sheet


| Symptom                               | Quick fix                                                              |
| ------------------------------------- | ---------------------------------------------------------------------- |
| `agent -p` asks for Workspace Trust   | add `--trust`                                                          |
| `Not logged in`                       | `CURSOR_API_KEY` in env **or** `agent login`                           |
| cache_demo fails                      | `pip install anthropic python-dotenv` + `.env`                         |
| MCP red / empty                       | open **DPL** as root · Reload · CodeGraph path                         |
| `codegraph` “no index” on cursor_code | expected; explore demo on **DPL**                                      |
| hook does not block push in IDE       | use the `permission: deny` example (already in repo); `ask` is flaky   |
| bash not found                        | Git Bash / WSL on PATH                                                 |


---



## Example → course-section map


| Folder                            | Part   | Live?                             |
| --------------------------------- | ------ | --------------------------------- |
| `ejemplos/agents-md/`             | §02    | Yes (open)                        |
| `ejemplos/permissions/`           | §02/03 | Yes (open)                        |
| `ejemplos/context/`               | §03    | Yes (open + `/summarize`)         |
| `ejemplos/prompt-caching/`        | §03    | Yes (run)                         |
| `ejemplos/mcp/`                   | §04    | Yes (open + UI)                   |
| `ejemplos/skills-plugins/`        | §05    | Yes (open + `/audit` · `/audit-python`) |
| `ex_npm/`                         | §05    | Yes (`/audit @ex_npm`)            |
| `ex_app/`                         | §05    | Yes (`/audit-python @ex_app`)     |
| `ex_staging/`                     | §05    | Yes (`/deploy-staging @ex_staging`) — asks human OK |
| `ejemplos/subagents/`             | §06    | Yes (open + PNG)                  |
| `ejemplos/hooks/`                 | §07    | Yes (node stdin)                  |
| `ejemplos/automation/`            | §07    | Yes (`agent -p` + SDK)            |
| `ejemplos/codegraph/` · `serena/` | §09    | Yes on **DPL**                    |
| `ejemplos/gsd/`                   | §09    | No (explain)                      |
| `ejemplos/metodologia/`           | §08/11 | Yes (MD + PNG; walkthrough on DPL) |
| `ejemplos/metodologia_en/`        | §08/11 | Yes (EN pack; same demos)         |
| `docs/knowledge-graph/`           | §12    | Yes (query + HTML)                |
