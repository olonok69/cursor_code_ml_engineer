# DEMO_RUNBOOK — presentación Cursor (36 slides)

Runbook para el/la **ponente**. Comandos verificados en Windows (PowerShell) el 9 ago 2026.
Guía narrativa: `[GUIA_PRESENTACION.md](./GUIA_PRESENTACION.md)` · Deck: `[presentacion/Cursor_Presentacion.pptx](./presentacion/Cursor_Presentacion.pptx)`.

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

| Qué | Cómo |
|---|---|
| Skill **npm** | `/audit @ex_npm` (Express mini-app + `npm test`) |
| Skill **Python** | `/audit-python @ex_app` (Streamlit TS forecasting + `pip-audit`) |
| Skill **staging** | `/deploy-staging @ex_staging` (tests → build → **pide OK** → deploy local → smoke) |
| Subagent | “Lanza el subagent **refactor-scout** sobre el símbolo `Agent` en `ejemplos/automation/sdk.ts`” |
| Rule | Siempre activa: `00-lean-memory` (no hace falta invocarla) |
| Hook `.env` | En Agent: “lee el fichero `.env`” → debe **deny** |
| Hook push | “haz `git push`” → debe **deny** |
| MCP | Customize → MCP: `context7`, `playwright` verdes · “usa context7 para docs de python-pptx” |

### Targets de skills (auditoría + deploy)

| Skill | Target | Stack | Qué hace |
|---|---|---|---|
| `/audit` | [`ex_npm/`](./ex_npm/) | Node + Express | `npm audit` → fix seguro → `npm test` |
| `/audit-python` | [`ex_app/`](./ex_app/) | Python + Streamlit | `pip-audit -r requirements.txt` → smoke |
| `/deploy-staging` | [`ex_staging/`](./ex_staging/) | Node (sin Express) | `npm test` → `build` → **confirmación humana** → `deploy:staging` → `GET /health` |

**Preflight de esos targets (T1):**

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
# dry-run opcional (sin skill): npm run deploy:staging ; curl health ; npm run staging:stop
```

En Agent chat (tras Reload):

```text
/audit @ex_npm
/audit-python @ex_app
/deploy-staging @ex_staging
```

En `/deploy-staging`, el agente **debe parar** antes de `npm run deploy:staging` y esperar tu OK.
El “staging” es un servidor local (escribe `.staging-url`); no hay cloud.

Teaching copies: `ejemplos/skills-plugins/.cursor/skills/{audit,audit-python,deploy-staging}/`.
Live copies: `.cursor/skills/{audit,audit-python,deploy-staging}/`.

**Mejor en DPL** (`document-parser-lambda`): los **5** MCP/skills del día a día (CodeGraph, Serena, Playwright, Context7, `kg`) — prompts listos en Parte 2 abajo. Este repo de curso no indexa producto.

---

## Antes de empezar (5 min)

**Terminals sugeridos**


| #   | Abrir en                                 | Para                      |
| --- | ---------------------------------------- | ------------------------- |
| T1  | `D:\repos3\cursor_code`                  | Parte 1 demos + kg        |
| T2  | `D:\repos3\ILS_2\document-parser-lambda` | Parte 2 MCP / metodología |
| T3  | (opcional) Cursor IDE en T2              | MCP verde + skills        |


**Cargar keys (T1)**

```powershell
cd D:\repos3\cursor_code
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k,$v = $_.Split('=',2)
  Set-Item -Path "Env:$($k.Trim())" -Value $v.Trim()
}
agent status   # o CURSOR_API_KEY ya basta para -p
docker ps      # Engine up
```

**Preflight**


| Check                                          | OK si…                                         |
| ---------------------------------------------- | ---------------------------------------------- |
| `python ejemplos\prompt-caching\cache_demo.py` | 2ª llamada `cache_read > 0`                    |
| `agent -p --trust --mode ask "di OK"`          | imprime OK                                     |
| `bash docs/knowledge-graph/kg_query.sh SST`    | nodos del grafo                                |
| Cursor en DPL → MCP                            | codegraph/serena/playwright/context7 **verde** |
| `codegraph status` en DPL                      | índice presente                                |


**No demos live (solo slide / explicación)**

- `ejemplos/gsd/` — solo Claude Code
- Bugbot / Automations / Cloud Agents — UI producto o cuenta cloud
- `hooks/query_hook.js`, `tsc.js`, `format_hook.js` — patrón; no CI de este repo
- `kg_refresh` completo — lento; usa grafo ya generado

---



## Parte 1 — Cursor (slides 1–19)


| Slide | Tema                       | Demo (click / comando)                                                                                                                                                | Artefacto              |
| ----- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1–3   | Portada / agenda / divider | Solo deck                                                                                                                                                             | —                      |
| 4–5   | Install + CLI              | T1: `agent --version` · `agent -p --trust --mode ask "Responde: OK-CURSOR-CLI"`                                                                                       | CLI                    |
| 6–7   | Memoria + permisos         | Abrir `ejemplos/agents-md/AGENTS.md` + `.cursor/rules/00-lean-memory.mdc` · mostrar `ejemplos/permissions/permissions.json.example`                                   | agents-md, permissions |
| 8     | Sesiones                   | Cursor UI: chat / Agent / Plan · mencionar `cursor.com/agents`                                                                                                        | —                      |
| 9–11  | Context window             | Abrir `ejemplos/context/README.md` + `AGENTS.pointers-example.md` · en chat: `/summarize`                                                                             | context                |
| 12    | Prompt caching             | T1: `python ejemplos\prompt-caching\cache_demo.py` · señalar write→read                                                                                               | prompt-caching         |
| 13    | MCP                        | Abrir `ejemplos/mcp/mcp.json.example` · Cursor → MCP (servers del día a día; supabase = opcional)                                                                     | mcp                    |
| 14    | Skills                     | Live: `/audit @ex_npm` · `/audit-python @ex_app` · `/deploy-staging @ex_staging` · Marketplace | skills-plugins, ex_npm, ex_app, ex_staging |
| 15–17 | Subagents                  | Abrir `.cursor/agents/refactor-scout.md` · mostrar `ejemplos/subagents/agents.png` · **decir**: no Agent Teams; Cloud = `cursor.com/agents` (no `--background`)       | subagents              |
| 18    | Hooks                      | T1:                                                                                                                                                                   | hooks                  |
|       |                            | `'{"path":".env"}' | node ejemplos\hooks\read_hook.js`                                                                                                                |                        |
|       |                            | `'{"command":"git push"}' | node ejemplos\hooks\block_external.js`                                                                                                    |                        |
|       |                            | Esperado: `permission: deny`                                                                                                                                          |                        |
| 19    | Automatización / SDK       | T1: `cd ejemplos\automation; npx tsx sdk.ts` (o prompt corto) · Action YAML solo abrir                                                                                | automation             |


**PowerShell one-liners hooks (Windows)**

```powershell
'{"path":"D:/repos3/cursor_code/.env"}' | node ejemplos\hooks\read_hook.js
'{"command":"git push origin HEAD"}' | node ejemplos\hooks\block_external.js
'{"command":"git status"}' | node ejemplos\hooks\block_external.js
```

---



## Parte 2 — Metodología (slides 20–30)

**Workspace:** Cursor abierto en `D:\repos3\ILS_2\document-parser-lambda` (no el parent `ILS_2`).


| Slide | Tema                        | Demo                                                                                                                       | Artefacto         |
| ----- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 20    | Divider Parte 2             | Solo deck                                                                                                                  | —                 |
| 21–23 | Flujo 11 etapas + ejemplo   | Abrir `ejemplos/metodologia/flow.png` · `WORKFLOW.md` · 2 min de `EJEMPLO_REAL.md`                                         | metodologia       |
| 24–25 | CodeGraph / Serena          | Live: ejemplos **1–2** abajo · o T2: `codegraph explore "ExtractorBase"`                                                   | codegraph, serena |
| 26    | GSD                         | **Solo slide** — “no hay port en Cursor; Plan mode + skill `methodology-plan`”                                             | gsd               |
| 27–28 | Playwright / prevalencia    | Live: ejemplos **3–5** abajo · abrir `ejemplos/metodologia/herramientas.md`                                                | metodologia, docs |
| 29    | Transferencia Claude→Cursor | Abrir `docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md` · carpeta `cursor/` (rules/skills/hooks)                      | pack              |
| 30    | Sync máquinas               | Abrir `ejemplos/metodologia/machine-sync.md` · `docs/synchro/` (1 pantalla)                                                | synchro           |


**Si MCP no está verde:** seguir `document-parser-lambda/AGENT_SETUP_TOOLS.md` (o la copia en `docs/ai-agents-code-methodology/`) — Reload Window, pin CodeGraph path, reiniciar Cursor tras `npm i -g codegraph`.

### 5 ejemplos live en DPL (skills + MCP del lambda)

MCP en DPL (`.cursor/mcp.json`): **codegraph**, **serena**, **playwright**, **context7**.  
Skills de proyecto: **`kg`**, `kg-refresh`, `methodology-plan`, `sanitise-diff`.  
Runbook canónico con smoke + pass criteria: `D:\repos3\ILS_2\document-parser-lambda\AGENT_SETUP_TOOLS.md` §D.

En Agent chat (workspace = `document-parser-lambda`), pegar **uno** por herramienta:

| # | Tool | Prompt (copiar) | Pass si… |
|---|---|---|---|
| 1 | **CodeGraph** (MCP) | `Use the CodeGraph MCP tool codegraph_explore on ExtractorBase. Return: defining file, blast radius (callers), and whether tests cover it. Do not re-Read files already shown in the explore output.` | explore con callers bajo `src/services/extractor_wrappers/` (o equiv.) |
| 2 | **Serena** (MCP) | `Using Serena MCP, call find_referencing_symbols for ExtractorBase._format_provision_description (disambiguate by class). List file:line references. Do not rename anything.` | refs con clase (no grep plano) |
| 3 | **Playwright** (MCP) | `Using Playwright MCP, open https://example.com and report the page title. Then close the browser.` | título real (p.ej. Example Domain) |
| 4 | **Context7** (MCP) | `Using Context7 MCP, fetch current docs guidance for pytest fixtures. Give a 5-line summary with source attribution from Context7.` | cita Context7 / docs, no solo memoria del modelo |
| 5 | **kg** (skill) | `Run the kg skill for topic "letter-end". List related tickets / danger zones and what to read next. Do not start coding.` | tickets SST relacionados (o STATUS fallback explícito) |

**CLI de apoyo (T2)** — si quieres evidencia sin Agent:

```powershell
cd D:\repos3\ILS_2\document-parser-lambda
codegraph status
codegraph explore "ExtractorBase"
bash data/knowledge-graph/kg_query.sh "letter-end"
```

**Bonus (si sobra tiempo):** Plan mode + `/methodology-plan` (rellena plantilla; no implementa). No hace falta demo de `kg-refresh` live (lento).

---



## Parte 3 — Grafo de tickets (slides 31–36)

**Workspace:** T1 `cursor_code` (el grafo del curso vive aquí).


| Slide | Tema            | Demo                                                                                                             | Artefacto       |
| ----- | --------------- | ---------------------------------------------------------------------------------------------------------------- | --------------- |
| 31    | Divider Parte 3 | Solo deck                                                                                                        | —               |
| 32    | Idea del KG     | Abrir `docs/KNOWLEDGE_GRAPH.md` (1 min)                                                                          | docs            |
| 33    | Pipeline        | Mostrar `docs/knowledge-graph/` (`build_manifest`, `stage_corpus`, `kg_refresh.sh`) — **no** correr refresh live | knowledge-graph |
| 34    | Query live      | T1: `bash docs/knowledge-graph/kg_query.sh SST` · segundo query con un ID que salga                              | kg_query.sh     |
| 35    | Visual          | Abrir `docs/knowledge-graph/output/graph.html` en browser · o slide con `presentacion/kg_graph.png`              | graph.html      |
| 36    | Cierre          | Recap: herramienta (Cursor) + método (11 etapas) + memoria (grafo)                                               | —               |


```powershell
cd D:\repos3\cursor_code
bash docs/knowledge-graph/kg_query.sh SST
# opcional: abrir el HTML
start docs\knowledge-graph\output\graph.html
```

---



## Orden cronometrado sugerido (~90–120 min)


| Bloque     | Slides | Tiempo    | Demos imprescindibles                               |
| ---------- | ------ | --------- | --------------------------------------------------- |
| Parte 1    | 1–19   | 40–50 min | `agent -p`, cache_demo, hooks deny, skill file, SDK |
| Parte 2    | 20–30  | 30–40 min | flow.png + **2–3** de los 5 smokes DPL + pack       |
| Parte 3    | 31–36  | 15–20 min | `kg_query` + graph.html                             |
| Buffer Q&A | —      | 10 min    | —                                                   |


**Si vas corto:** corta Cloud Agents UI, sync máquinas a 1 frase, GSD a 30 s, skip SDK (deja `agent -p`).

**Si sobra tiempo:** en DPL corre los 5 smokes de la tabla Parte 2; Plan mode + `/methodology-plan`.

---



## Cheat-sheet de fallos frecuentes


| Síntoma                               | Fix rápido                                                            |
| ------------------------------------- | --------------------------------------------------------------------- |
| `agent -p` pide Workspace Trust       | añade `--trust`                                                       |
| `Not logged in`                       | `CURSOR_API_KEY` en env **o** `agent login`                           |
| cache_demo falla                      | `pip install anthropic python-dotenv` + `.env`                        |
| MCP rojo / vacío                      | abrir **DPL** como root · Reload · path CodeGraph                     |
| `codegraph` “no index” en cursor_code | normal; demo explore en **DPL**                                       |
| hook no bloquea push en IDE           | usa ejemplo con `permission: deny` (ya en repo); `ask` es poco fiable |
| bash no encontrado                    | Git Bash / WSL en PATH                                                |


---



## Mapa ejemplo → sección del curso


| Carpeta                           | Parte  | ¿Live?                            |
| --------------------------------- | ------ | --------------------------------- |
| `ejemplos/agents-md/`             | §02    | Sí (abrir)                        |
| `ejemplos/permissions/`           | §02/03 | Sí (abrir)                        |
| `ejemplos/context/`               | §03    | Sí (abrir + `/summarize`)         |
| `ejemplos/prompt-caching/`        | §03    | Sí (ejecutar)                     |
| `ejemplos/mcp/`                   | §04    | Sí (abrir + UI)                   |
| `ejemplos/skills-plugins/`        | §05    | Sí (abrir + `/audit` · `/audit-python`) |
| `ex_npm/`                         | §05    | Sí (`/audit @ex_npm`)                 |
| `ex_app/`                         | §05    | Sí (`/audit-python @ex_app`)          |
| `ex_staging/`                     | §05    | Sí (`/deploy-staging @ex_staging`) — pide OK humano |
| `ejemplos/subagents/`             | §06    | Sí (abrir + PNG)                  |
| `ejemplos/hooks/`                 | §07    | Sí (node stdin)                   |
| `ejemplos/automation/`            | §07    | Sí (`agent -p` + SDK)             |
| `ejemplos/codegraph/` · `serena/` | §09    | Sí en **DPL**                     |
| `ejemplos/gsd/`                   | §09    | No (explicar)                     |
| `ejemplos/metodologia/`           | §08/11 | Sí (MD + PNG; walkthrough en DPL) |
| `docs/knowledge-graph/`           | §12    | Sí (query + HTML)                 |


