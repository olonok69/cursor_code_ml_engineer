# Tool prevalence — what Cursor uses and when

**Rules** (`.cursor/rules/`) and `AGENTS.md` do not only say *what* to do; they say **which tool**
and in what order. That turns "I have MCP installed" into "the agent pulls the right tool."

## The golden rule: graph navigation before reading files

> **"For 'what is this / who depends / what do I touch', a `codegraph_explore` **first** — source + call
> paths + blast radius + test-coverage flags in one call (treat the source it returns as ALREADY
> read; do not re-open it). Serena `find_referencing_symbols` for the **precise** check before renaming or
> deleting a helper (disambiguates by class). grep/Read only for literals."** — rule in
> `.cursor/rules/01-tool-prevalence.mdc`.

> **Two graphs, two domains.** CodeGraph indexes the *code*; the **`kg`** skill (graphify) indexes
> *project memory* (tickets, sharp edges). Detail: [`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md).

## Prevalence table

| I need… | Preferred tool | Why / rule |
|---|---|---|
| Survey: what is / who depends / blast / tested? | **CodeGraph** `codegraph_explore` | 1 query; treat as ALREADY read |
| Precise check before rename/delete | **Serena** `find_referencing_symbols` | Mandatory; disambiguates by class |
| Body / overview of a large file | Serena `find_symbol` / `get_symbols_overview` | Or the source from `explore` |
| Output contract | **Playwright** / F12 | What the consumer sees |
| Deployed runtime | **Docker** (same image) | Green tests ≠ what was shipped |
| Cheap root cause | **Oracle** (`_diag_*.py` / parser) | No model call to diagnose |
| Cloud logs / config | **AWS CLI** (read-only) | First-class debugging |
| Library docs | **Context7** | Vs training cutoff |
| git / PRs | `gh`, `git` | status-first |
| Tickets / lessons in the area | **Skill `kg`** (or STATUS fallback) | history-first before grep |
| Independent parallel work | **Task** (explore / generalPurpose) | Without cluttering the main thread |

## Install and smoke (Cursor / ILS demo)

Runbook to configure the 5 tools (CodeGraph, Serena, Playwright, Context7, kg) and try them:
[`../../docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md`](../../docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md)
· in the live repo: `document-parser-lambda/AGENT_SETUP_TOOLS.md`.

## The order (cheap → expensive)

1. Orientation: `STATUS.md` + `git`/`gh` + skill **`kg`**
2. Navigation: CodeGraph → Serena
3. Diagnosis: deterministic oracle
4. Environment: AWS CLI
5. Contract: Playwright
6. Outbound: wrapper + Docker
7. Only at the end: model call to verify the fix

## Skills vs oracles

| | **Skills / MCP** | **Oracles** (`_diag`, parser) |
|---|---|---|
| What it is | Registered capability (auto-select by `description`) | Code the agent writes and runs in Shell |
| Where (Cursor) | `.cursor/skills/` · `~/.cursor/skills/` · MCP | `data/changes/<ticket>/` (gitignored) or `src/`/`tests/` |
| Examples | `kg`, `sanitise-diff`, Serena, CodeGraph, Playwright | `_diag_pdf.py` |

In Claude Code `/kg` lived in `~/.claude/skills/`. In Cursor: project skill (methodology pack) or user.

## Permissions (different from Claude)

Claude Code: hand-curated allowlist in `settings.local.json` (`mcp__serena__…`, etc.).

Cursor:

1. **Rules** — prevalence and “no push unless asked.”
2. **Approvals** from the product UI / settings.
3. **Hooks** — e.g. `beforeShellExecution` for push/PR/deploy ([`../hooks/`](../hooks/)).

Do not copy Claude's allow JSON; re-implement the *policy* with rules + hooks.
