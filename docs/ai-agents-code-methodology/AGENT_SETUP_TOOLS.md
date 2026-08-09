# AGENT SETUP — day-to-day tools (Cursor / Part 2)

> **Canonical runbook for the agent working on the live demo repo:**  
> `D:\repos3\ILS_2\document-parser-lambda\AGENT_SETUP_TOOLS.md`  
> (same content intent; keep that file updated when paths change.)
>
> Guides: [`../../GUIA_PRESENTACION.md`](../../GUIA_PRESENTACION.md) §4 + §9 ·
> [`../../GUIA_TECNICA.md`](../../GUIA_TECNICA.md) §7 + §13 ·
> [`CURSOR_ADAPTATION.md`](./CURSOR_ADAPTATION.md).

## The 5 tools

| # | Tool | Kind | Smoke test |
|---|---|---|---|
| 1 | **CodeGraph** | MCP + CLI | `codegraph explore "ExtractorBase"` / MCP `codegraph_explore` |
| 2 | **Serena** | MCP (`uvx`) | `find_referencing_symbols` on a known method |
| 3 | **Playwright** | MCP (`npx`) | Open `https://example.com`, report title |
| 4 | **Context7** | MCP URL | Library docs query (e.g. pytest fixtures) |
| 5 | **kg** | Skill + `kg_query.sh` | `bash data/knowledge-graph/kg_query.sh letter-end` |

## Why they often look “not installed” in a multi-repo workspace

1. Cursor was opened on the **parent** `ILS_2` folder — project MCP/skills under
   `document-parser-lambda/.cursor/` may not load as expected.
2. CodeGraph `--path` in `.cursor/mcp.json` still points at an old path (`D:/ILS/...`).
3. `codegraph` was installed but **Cursor was not restarted**, so MCP cannot find the binary on PATH.
4. Serena/Playwright need a first cold start (`uvx` / `npx` download).
5. Skills exist on disk but the window was not reloaded.

## Agent instructions (short)

When asked to configure tools in `document-parser-lambda`:

1. Read and follow **`AGENT_SETUP_TOOLS.md` in that repo root** end-to-end.
2. Install host CLIs if missing (`codegraph`, `uvx`, `node`/`npx`, `bash`).
3. Pin `.cursor/mcp.json` CodeGraph path to this repo’s absolute path.
4. Ensure skills `kg` / `kg-refresh` and rules `00`/`01`/`02` exist (run bootstrap if needed).
5. Tell the human to **Reload Window** and confirm MCP green lights.
6. Run all five smoke tests; report a pass/fail table with evidence.

Do **not** port Claude `settings.local.json`. Do **not** require Supabase. Do **not** push/PR unless asked.

## Pack paths

- MCP example: [`cursor/mcp.json.example`](./cursor/mcp.json.example)
- Bootstrap: [`scripts/bootstrap-cursor-repo.ps1.txt`](./scripts/bootstrap-cursor-repo.ps1.txt)
- Examples: [`../../ejemplos/mcp/`](../../ejemplos/mcp/), [`../../ejemplos/codegraph/`](../../ejemplos/codegraph/), [`../../ejemplos/serena/`](../../ejemplos/serena/)
