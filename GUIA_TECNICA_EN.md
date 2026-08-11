# Cursor — Technical implementation guide (course in three parts)

> Copy-paste reference for building each piece. It complements
> [`GUIA_PRESENTACION_EN.md`](./GUIA_PRESENTACION_EN.md) (the narrative thread) with the **how**.
> All runnable artifacts are in [`ejemplos/`](./ejemplos/);
> [`docs/`](./docs/) is reference material from a real installation. Claude Code volume:
> [`GUIA_TECNICA_EN.md`](https://github.com/olonok69/claude_code_ml_engineer/blob/HEAD/GUIA_TECNICA_EN.md)
> (sibling repo) — same structure and section numbering.
>
> English version of [`GUIA_TECNICA.md`](./GUIA_TECNICA.md). Spanish original stays at that path.
>
> **Verification note (2nd pass):** Cursor-specific content (Skills, Marketplace,
> Subagents, headless CLI, hooks, SDK…) was checked against `docs.cursor.com` on **9 August 2026**.
> Cursor moves fast — before reusing this guide, check whether anything has moved again.

## Table of contents

**Part 1 — Cursor**

1. [Installation and CLI](#1-installation-and-cli)
2. [Memory: AGENTS.md, rules and Memories](#2-memory)
3. [Permissions](#3-permissions)
4. [Sessions across surfaces](#4-sessions)
5. [Context window](#5-context-window)
6. [Prompt caching](#6-prompt-caching)
7. [MCP](#7-mcp)
8. [Skills and Marketplace](#8-skills-and-marketplace)
9. [Subagents](#9-subagents)
10. [Hooks](#10-hooks)
11. [Automation: headless, CI, Automations, SDK](#11-automation)

**Part 2 — The methodology**

12. [The workflow and the real example](#12-methodology)
13. [The tools: CodeGraph, Serena, GSD](#13-the-methods-tools)
14. [Transferring the methodology (starter-kit / from Claude Code to Cursor)](#14-transferring-the-methodology)
15. [Machine sync (tarball + S3)](#15-machine-sync)

**Part 3 — The ticket knowledge graph (graphify)**

16. [Ticket knowledge graph](#16-ticket-knowledge-graph)

---

# PART 1 — Cursor

## 1. Installation and CLI

```bash
# Editor: download from cursor.com (macOS / Windows / Linux)

# Cursor CLI (agent) — headless-capable
# macOS / Linux / WSL:
curl https://cursor.com/install -fsS | bash
# Windows PowerShell:
irm 'https://cursor.com/install?win32=true' | iex

# Start
cd your-project && agent          # first time: agent login  (or CURSOR_API_KEY / --api-key)
agent status                     # authenticated?

# Headless / print mode (one prompt, stdout)
agent -p --trust "summarize the changes on this branch"
agent -p --trust --output-format text "security-review the files touched vs main"
# Real edits in scripts: add --force (or --yolo)
# --trust skips the interactive Workspace Trust prompt on the first headless run

# Background/Cloud Agents: cursor.com/agents (or handoff `&` in the product).
# Do not use `agent -p --background` — that flag does not exist on the current CLI.
```
Useful commands in a CLI session: `/summarize` (alias `/compress`), `/rewind` (if enabled),
`/plan` `/ask` modes, and the editor ones (Plan mode, Agent mode, chat). MCP: edit `.cursor/mcp.json`
and manage with `agent mcp list|enable|disable|login` (there is no `agent mcp add`). Skills are invokable with
`/name`. Reference: `docs.cursor.com/cli`.

---

## 2. Memory

### `AGENTS.md` (root + nested — most specific wins)
```
AGENTS.md                    # repo root, no frontmatter, always loaded
<subdir>/AGENTS.md           # more specific: wins over the root when working there
```
There is no eager `@path/file` import syntax in `AGENTS.md` (it does exist inside `.mdc` rules, see
below) — use pointers + have the agent read the file, or move that content into a rule.

### `.cursor/rules/*.mdc` — gates and prevalence
Frontmatter: `description`, `globs`, `alwaysApply`. **Four modes**: Always Apply, Apply Intelligently,
Apply to Specific Files, Apply Manually. In the body, `@file` includes another file's content when
the rule loads (*eager* load — counts against context whenever the rule is active):
```yaml
---
description: Project tool gates and prevalence
globs:
alwaysApply: true
---
Before touching code: orient with the `kg` skill + STATUS.md. For navigation, `codegraph_explore`
FIRST. @../data/changes/SHARP_EDGES.md
```
Recommended: split gates across several `.mdc` files (1 concern per rule, <50 lines), not one huge file.

### Two-tier pattern (see [`ejemplos/agents-md/`](./ejemplos/agents-md/))
- **Tier 1** = `AGENTS.md` + `alwaysApply` rules always loaded: orientation + one-line pointers.
  Small.
- **Tier 2** = files under `data/changes/` (`STATUS.md`, `PLAYBOOK.md`, `SHARP_EDGES.md`,
  `TEST_MAP.md`, `CONVENTIONS.md`, `TICKETS.md`, `FOLLOWUPS.md`, `<TICKET>/<TICKET>.md`) that are read
  on demand.
- **Write-once rule:** each fact lives in a single canonical ledger; the core carries the pointer, not the copy.
- **Tier 0 (machine-local):** `IDENTITY.md` — which machine this is and what role it holds (`publisher` /
  `contributor`) in the shared record (§15B). Gitignored, never synced: the one file
  that must **not** be the same everywhere.

> **The index goes stale too.** Moving content out of the always-loaded file into an on-demand file
> **does not refresh it** — it inherits the original's staleness while *looking* freshly written. Real
> case: a 28-entry ticket→test list was moved to `TEST_MAP.md`, and the verification check asserted
> "the file has 28 entries". It had exactly 28 — and 28 was the wrong number: `tests/` held **80**
> files and the list had stopped ~40 tickets earlier. The count could not fail, because it was derived
> from the same stale source it was checking. Verify a moved list **against the thing it describes**
> (the filesystem, the code), never against its own former self.

### Memories — a DISTINCT system
Cursor generates Memories automatically from your chats — they are **not** versionable files you
write, and **not** the same mechanism as Claude Code's auto-memory (`MEMORY.md`). Do not copy the
Claude Code mental model blindly: treat them as a complement to the two-tier pattern, not as a
substitute.

---

## 3. Permissions

```jsonc
// ~/.cursor/permissions.json  and/or  <repo>/.cursor/permissions.json
// If both exist, Cursor CONCATENATES the arrays for each field.
{
  "mcpAllowlist": [
    "serena:find_symbol",
    "playwright:browser_navigate",
    "codegraph:*"
  ],
  "terminalAllowlist": [
    "git",
    "npm",
    "pytest"
  ]
}
```
Real fields: **`mcpAllowlist`**, **`terminalAllowlist`**, optional **`autoRun`** (steering the
classifier in Auto-review). MCP format: `server:tool` with globs (`server:*`, `*:tool`). When the
file defines a key, it **replaces** the UI allowlist for that type — do not invent a field named
`"allow"`. Do not copy Claude Code's `mcp__serena__…` JSON: re-implement the *policy* with this
format. The human owns push/PR/deploy → do not put them on the allowlist lightly; reinforce with
rules + hooks (`beforeShellExecution`, §10).

**Note:** the **Cursor CLI** has separate permissions in `cli-config.json` (`permissions.allow` /
`permissions.deny` with syntax `Mcp(server:tool)`, `Shell(…)`, etc.). Do not mix the two files.

### The layers that govern access — compared with Claude Code

1. **`permissions.json`** — `mcpAllowlist` / `terminalAllowlist` (user ∪ project).
2. **UI Approvals / Run Mode** — interactive confirmation in the editor.
3. **Rules** — policy declared in prose (prevalence, "no push without asking"): they do not veto by themselves, but
   steer agent behavior consistently.
4. **Hooks** — a `beforeShellExecution`/`preToolUse` with `permission: "deny"` (or `exit 2`) vetoes by
   *content*, which the static allowlist cannot (§10).

> Summary rule: **Claude Code manages a tool-name allowlist** (`mcp__server__tool`);
> **Cursor IDE manages the same with `mcpAllowlist: ["server:tool"]`**, reinforced by rules and hooks. The
> *policy* — the human owns everything external — is identical; the mechanism changes.

---

## 4. Sessions

| I need… | Tool |
|---|---|
| Work in the editor with inline diffs | **Cursor Editor** (chat / Agent mode / Plan mode) |
| Terminal / SSH / server without UI | **Cursor CLI** (`agent`) |
| Long cloud task, editor closed | **Background / Cloud Agents** (`cursor.com/agents`) |
| Automatic review of every PR | **Bugbot** (GitHub/GitLab/Bitbucket) |

The same agent and the same configuration (`AGENTS.md`/rules/MCP/permissions/hooks) work across the three
interactive surfaces; Bugbot runs on its own, without you invoking it.

> There is no direct equivalent of `claude --teleport` / Remote Control / `/desktop` (Claude Code's explicit
> handoff between terminal CLI and desktop app): in Cursor, editor/CLI/cloud are independent entry points
> into the same agent, not a session that is "handed off" between surfaces with one command.

---

## 5. Context window

Full reference: [`ejemplos/context/`](./ejemplos/context/). What the session loads
before your first prompt: system/agent prompt (hidden, always first) · `alwaysApply` rules +
`AGENTS.md` (you control these) · Memories if any (distinct system — review what slipped in) · MCP tool
index · then conversation, files read, command output (grows every turn).

```text
/summarize                     # (alias /compress) summarize and free context
/rewind                        # return to a previous message (CLI; if enabled)
# + context ring in the editor: per-block usage
# + new chat / new `agent` invocation between unrelated tasks
```

- Cursor **auto-summarizes** near the limit (in addition to manual `/summarize`) — do not assume
  exact parity with Claude Code's `/compact <focus>`; the automatic summarization mechanism is different.
- MCP: every server adds context → disable ones the project does not use (`.cursor/mcp.json`).
- Noisy research → subagents (§9): the noise dies outside; the summary comes back.
- `AGENTS.md`/rules: same rule as in the Claude Code docs — *if you can delete it without the agent getting
  things wrong, delete it*.

---

## 6. Prompt caching

Reference and runnable demo (Anthropic API, to understand the mechanism — not exposed as such in the
Cursor product): [`ejemplos/prompt-caching/`](./ejemplos/prompt-caching/)
([`cache_demo.py`](./ejemplos/prompt-caching/cache_demo.py)).

**Mechanics (API):** a **contiguous prefix** is cached up to a `cache_control` breakpoint; strict
hierarchy `Tools → System → Messages` (a change invalidates its level and the ones after it).

| | Write | Read |
|---|---|---|
| 5 min TTL (default) | 1.25× input | **0.1×** input |
| 1 h TTL (`"ttl": "1h"`) | 2× input | **0.1×** input |

```python
system=[{ "type": "text", "text": STABLE_INSTRUCTIONS,
          "cache_control": {"type": "ephemeral"} }]   # breakpoint AT THE END of the stable part
messages=[{"role": "user", "content": query}]          # variable part AFTER (outside the cache)
```

Diagnosis in `response.usage`: `cache_creation_input_tokens` / `cache_read_input_tokens`.
Minimum cacheable ~1,024 tokens (4,096 on Haiku); max 4 explicit breakpoints.

**In the Cursor product** there is no exposed control (no env vars like `ENABLE_PROMPT_CACHING_1H`, no
visible `cache_control`) — whatever the model provider decides underneath applies. What you *do* control:
small, **stable** `AGENTS.md`/rules (prefix that does not change); do not edit them mid-session; few
active MCP servers (stable tools block); new session/chat between unrelated tasks. If you automate with the
**Cursor SDK** against the Anthropic API directly (§11), the rules above apply as written.

---

## 7. MCP

See [`ejemplos/mcp/mcp.json.example`](./ejemplos/mcp/mcp.json.example). Scopes: **project**
(`.cursor/mcp.json`, versioned) and **user** (`~/.cursor/mcp.json`, editable directly or via Settings →
MCP).

```jsonc
// .cursor/mcp.json — edit the JSON (or UI). CLI: agent mcp list|enable|disable|login
// Interpolation: ${env:NAME}, ${workspaceFolder}, ${userHome}
{ "mcpServers": {
    "serena": { "command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"] },
    "context7": { "url": "https://mcp.context7.com/mcp" },
    "codegraph": {
      "command": "codegraph",
      "args": ["serve", "--path", "${workspaceFolder}", "--mcp"] },
    "supabase": {
      "command": "npx", "args": ["-y", "@supabase/mcp-server-supabase@latest"],
      "env": { "SUPABASE_ACCESS_TOKEN": "${env:SUPABASE_ACCESS_TOKEN}" } }
} }
```
After editing: **reload/restart Cursor** (recommended; Reload Window sometimes suffices). MCP tools are
allowed/denied in `permissions.json` (§3) with `mcpAllowlist` (`server:tool` + globs).

**The daily five (Part 2):** CodeGraph · Serena · Playwright · Context7 · `kg` skill (repo scripts).
Supabase in the example below is **optional** (demo of a secret via env).

**Install + verify in the demo repo:** follow the runbook
[`AGENT_SETUP_TOOLS.md`](./docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md)
(operational copy in `ILS_2/document-parser-lambda/AGENT_SETUP_TOOLS.md`). Critical steps:

1. Open **`document-parser-lambda`** as the folder (or ensure its `.cursor/mcp.json` loads).
2. `npm i -g @colbymchenry/codegraph@latest` if `codegraph` is not on PATH → **restart Cursor**.
3. Pin CodeGraph: `"args": ["serve", "--path", "${workspaceFolder}", "--mcp"]`
   (or an absolute path if needed, e.g. `D:/repos3/ILS_2/document-parser-lambda`).
4. Skills `kg`/`kg-refresh` under `.cursor/skills/`; scripts in `data/knowledge-graph/`.
5. Reload Window → MCP green → smoke tests from the table in `AGENT_SETUP_TOOLS.md` §D.

> **Config gives capability; `AGENTS.md`/rules give judgment.** MCP servers are **not** installed in
> `AGENTS.md` — that file is prompt only, not configuration. They are installed in `.cursor/mcp.json` /
> `~/.cursor/mcp.json` (or brought by a pack in the repo). But installing Serena only makes the tool *exist*;
> making the agent **reach for it unprompted** takes a rule with a *trigger map*: "CodeGraph BEFORE
> reading whole files; `find_referencing_symbols` ALWAYS before a rename". That is the prevalence rule
> from [`metodologia_en/tools.md`](./ejemplos/metodologia_en/tools.md) — config turns
> "I don't have the tool" into "I have it"; the rule turns "I have it" into "it is used in the right order".

---

## 8. Skills and Marketplace

**Skill** — `.cursor/skills/<n>/SKILL.md` with frontmatter `name` + `description` (the `description` drives
auto-selection, same as in Claude Code). May carry scripts/templates in its folder.

**Direct interop:** Cursor also reads `.claude/skills/` — **the same `SKILL.md` works in both
products** with no translation. That is why the Part 3 `kg`/`kg-refresh` skills (originally created
for Claude Code) work the same here.

**Marketplace** (`cursor.com/marketplace`): installable packages of skills + subagents + MCP + hooks +
rules, from the product UI. There is no `/plugin install` command.

```
.cursor/skills/kg/SKILL.md
.cursor/skills/kg-refresh/SKILL.md
.cursor/skills/sanitise-diff/SKILL.md
.cursor/skills/methodology-plan/SKILL.md
```
Real project skill examples: [`ejemplos/skills-plugins/.cursor/skills/`](./ejemplos/skills-plugins/.cursor/skills/)
(`audit`, `deploy-staging`). Methodology pack with the four skills above:
[`docs/ai-agents-code-methodology/cursor/skills/`](./docs/ai-agents-code-methodology/cursor/skills/).

> **Note (August 2026):** Skills, Marketplace, `.cursor/agents/` and `agent -p` are documented at
> `docs.cursor.com`. If a row in [`ejemplos/README.md`](./ejemplos/README.md) looks stale, trust
> the official docs and this guide.

---

## 9. Subagents

Full reference + diagram: [`ejemplos/subagents/`](./ejemplos/subagents/).

**Native:** delegation with **isolated** context per subagent — only the summary returns to the main
session. Invoked by natural language or `/name`; parallel execution. Documented built-ins:
**Explore**, **Bash**, **Browser** (plus Task types depending on version/environment). Check
`docs.cursor.com/subagents` before assuming names.

**Custom subagents — definition files:**
```text
.cursor/agents/<name>.md     # project (versionable)
~/.cursor/agents/<name>.md   # user
# Compat: .claude/agents/ and .codex/agents/ are also loaded
```
Typical frontmatter: `name`, `description`, optional `model` (`inherit` / slug), `readonly`,
`is_background`. Ready example: [`ejemplos/subagents/.cursor/agents/refactor-scout.md`](./ejemplos/subagents/.cursor/agents/refactor-scout.md).

**Lightweight alternative:** prompt / skill template at launch (no agent file):
[`security-reviewer`](./ejemplos/subagents/prompts/security-reviewer.md) ·
[`refactor-scout`](./ejemplos/subagents/prompts/refactor-scout.md). **Gotcha:** the subagent does not inherit your
conversation — context goes in the launch prompt.

**What does NOT exist: Agent Teams.** No lead+teammates+shared inbox. The pragmatic substitute is
parallelism with **Background/Cloud Agents** (`cursor.com/agents`, or handoff `&` in the product): each
is a full session, on its own branch, **with no messaging between agents**. Partition work by
branch/file before launching; a human (or the main agent) integrates results. **Do not** use
`agent -p --background` — that flag does not exist on the current CLI.

| | Subagent | Background / Cloud Agent |
|---|---|---|
| Context | Isolated; returns a summary | Full session, async, on its branch |
| Communication | Result only → main session | None between agents (no inbox) |
| Cost | Low | High (N full sessions) |
| Config | `.cursor/agents/*.md`, prompt or skill | `cursor.com/agents` (UI / handoff `&`) |

---

## 10. Hooks

Everything in [`ejemplos/hooks/`](./ejemplos/hooks/). Config in `.cursor/hooks.json` (project) or
`~/.cursor/hooks.json` (user):

```jsonc
// hooks.json.example
{ "hooks": {
    "beforeReadFile": [{ "command": "node ./hooks/read_hook.js" }],
    "beforeShellExecution": [{ "command": "node ./hooks/block_external.js" }],
    "afterFileEdit": [
      { "command": "node ./hooks/format_hook.js" },
      { "command": "node ./hooks/tsc.js" }
    ]
} }
```

**Contract:** event payload on **STDIN** · **JSON** response on STDOUT with
`{"permission": "allow"|"deny"|"ask", "user_message"?: string}` — **`exit 2` also blocks**.
For demos/handoff gates use **`deny`** (`ask` is often ignored in practice).
`failClosed`: if the hook crashes, block (stricter posture than the implicit fail-open of a hook that
does not respond in Claude Code).

**Available events (more granular than Claude Code):** `preToolUse`, `postToolUse`, `beforeReadFile`,
`afterFileEdit`, `beforeShellExecution`, `beforeMCPExecution`, `beforeSubmitPrompt`, `stop`, and more.

**Blocking pattern (JS)** — in the repo the scripts are **ESM** (`import` + top-level `await`); the
minimal snippet below is CJS only for the whiteboard:
```js
// beforeReadFile — block .env (minimal CJS version)
const p = JSON.parse(require("fs").readFileSync(0, "utf8"));
if ((p.path || "").includes(".env")) {
  console.log(JSON.stringify({ permission: "deny", user_message: "Blocked: do not read .env" }));
  process.exit(0);
}
console.log(JSON.stringify({ permission: "allow" }));
process.exit(0);
```
Real payloads: [`pre-log.json`](./ejemplos/hooks/pre-log.json),
[`post-log.json`](./ejemplos/hooks/post-log.json). Handoff-veto example:
[`block_external.js`](./ejemplos/hooks/block_external.js) (`beforeShellExecution` → `permission: "deny"`
for push/PR/deploy) — also in
[`docs/ai-agents-code-methodology/cursor/hooks/block-external-git.ps1`](./docs/ai-agents-code-methodology/cursor/hooks/block-external-git.ps1).

---

## 11. Automation

See [`ejemplos/automation/`](./ejemplos/automation/).

**Headless / print mode:**
```bash
agent -p "summarize the changes on this branch"
agent -p --output-format text "security-review the files touched vs main"
# Preferable to assuming stdin→prompt piping (not documented the way Claude Code does):
agent -p "Read app.log (last ~200 lines) and flag any anomalies"
```

**CI/CD:** **Bugbot** (native, PR review without your own script) or Cursor SDK in your own GitHub Action —
see [`github-action-cursor.yml`](./ejemplos/automation/github-action-cursor.yml).

**Automations** (distinct from Background/Cloud Agents) — cron + event triggers: Slack, Linear, PR
merged, PagerDuty. **Background/Cloud Agents** (`cursor.com/agents`) are for on-demand async work,
not scheduled.

**Cursor SDK** (`@cursor/sdk`):
```ts
import { Agent } from "@cursor/sdk";

// One-shot (what sdk.ts / review.ts / query_hook.js use)
const result = await Agent.prompt(prompt, {
  apiKey: process.env.CURSOR_API_KEY!,
  local: { cwd },
});

// Multi-turn / stream
const agent = await Agent.create({ apiKey: process.env.CURSOR_API_KEY, local: { cwd } });
const run = await agent.send(prompt);
for await (const ev of run.stream()) {
  // progress / result events
}
```
For the agent to work in the cloud and open the PR itself: `Agent.create({ cloud: { repos, autoCreatePR: true } })`.
Full example: [`sdk.ts`](./ejemplos/automation/sdk.ts) ·
[`review.ts`](./ejemplos/automation/review.ts) (automatic PR review with the SDK).

> **Patterns:** `Agent.prompt(...)` = one-shot; `Agent.create` + `send` + `stream` = multi-turn.
> Verify the exact signature against `docs.cursor.com` / the `@cursor/sdk` README if time has passed.

---

# PART 2 — The methodology

## 12. Methodology

All the deep material (11-stage workflow, real end-to-end example, tool-precedence) is in
[`ejemplos/metodologia_en/`](./ejemplos/metodologia_en/). Summary:

### The real workflow (see [`metodologia_en/WORKFLOW.md`](./ejemplos/metodologia_en/WORKFLOW.md))
Agent = disciplined collaborator; autonomy is earned per-decision. 11 stages chained by **deterministic
gates**: orient (`kg` skill + history+status) → inbound triage against the **output contract** →
regression vs pre-existing → investigate with a **deterministic oracle** (before the paid LLM call) →
**Plan mode** + agreement → Agent mode: TDD RED→GREEN → verify (unit+scoped+regression+contract via the
*wrapper* AND inside the deployed image) → document → **sanitize** (`sanitise-diff` skill on
added lines) → handoff (the agent does **not** push/PR/deploy unless explicitly asked — hook
`beforeShellExecution`/rules; the human does it) → Bugbot review + persist (`kg-refresh` skill if
applicable).
Diagram: [`metodologia_en/flow.png`](./ejemplos/metodologia_en/flow.png) (source `flow.mmd`, render
`render_flow.py`). Concrete case from start to finish:
[`metodologia_en/REAL_EXAMPLE.md`](./ejemplos/metodologia_en/REAL_EXAMPLE.md).

> **The outbound gate is FIVE checks** (not just "the tests pass"):
> **(0) validate the measuring instrument before trusting it** — any `_diag_*`/`_sweep_*` that informs a ship
> decision is first run against a **known-answer case**, and that result recorded next to the finding; never
> wrap the measurement in your own `try/except → return False`;
> (1) reproduce at the **real output stage** — the *wrapper* that rebuilds the contract, not an internal
> `extract()` function; (2) the local JSON matches the contract, and **is verified on the member LIST,
> never on a total**; (3) verify it **inside the deployed image** (download/build the runtime image, mount
> the `src`, re-run); (4) **look at the output** rendered, by eye, before the PR — for geometry/highlight
> changes, before/after artifacts are **mandatory**.
> Green tests are not proof of what gets deployed. Identical in role to the Claude Code gate — only
> which agent runs it changes.
>
> **Five ways a green gate proves nothing** — all five have bitten us:
> **Broken instrument.** Bypassing the constructor to probe a predicate cheaply leaves unset every attribute
> you didn't think to set; if the method reads one and has its own `try/except`, the error is swallowed and
> comes back as a plausible `False`. The probe then reports a confident, uniform "no" for **every** case.
> Canary against a known answer, always.
> **A total that matches.** A count that lands on the expectation is **not** a passing test: one item wrongly
> added and one wrongly dropped cancel exactly. Assert on **titles/ids**, not on `len(...)`; and where the fix
> has a known direction, measure a **delta** against a baseline (gained/lost), not two totals. The closer a
> number falls to the expected one, the **more** suspicious it should be, not less.
> **A gate that couldn't fail.** If the reference corpus holds no positive example of the shape you just
> touched, the clean run proves **no-regression and nothing else**. Say so explicitly, and name what carries
> the correctness evidence instead. (Real case: a detector that fires on **0 of 190** corpus documents —
> `fires=0` reads identically whether the code is correct or completely broken.)
> **A canary that never applied the real perturbation.** The instrument can be flawless and still prove
> nothing, because what it does to the data **is not what production does**. Real case: the synthetic test
> renamed the *containers* and churned 4% of the items, recovered **100%** of the mapping, and was reported
> as "verified"; the real rebuild changed something the test never touched — the **identifiers of the items
> themselves**, 88% of them — and recovery fell below **1%**. Before trusting a green canary, state in one
> sentence *what production does to this data* and check the canary does the same. If you can't, the gate is
> **unproven**: "the test I could build passed" is not "the risk is retired".
> **A structural gate read as a semantic one.** Checking that everything is present, unique and correctly
> wired says **nothing** about whether any of it is *right*. Real case: a migration reported a clean bill of
> health — every group matched, none lost, zero orphans — while **56%** of the carried-over names did not
> describe what they were attached to, because the matching had fallen back to a shallow proxy. A wrong name
> is **worse** than a missing one: the missing one asks a question, the wrong one answers it incorrectly and
> sends the next person to the wrong place. When a value's correctness is a matter of **meaning**, no
> automated check retires it — schedule the human read and say so in the gate's description.
>
> **The output contract is a living document.** When a change alters what is emitted, consult the governing
> rule **before** designing the fix and do exactly one of three things: **comply**, **revise** it as part of
> the same change, or **record** why it's out of scope. All three are valid; **silence is not**. Revision is
> normal: a correct fix revealing that an agreed rule was wrong is *how* the contract improves. Two practical
> notes: cite the rule by **stable identifier** (never by file path — local paths don't resolve for whoever
> reads it in a ticket), and don't turn it into a CI gate: the decision is **three-valued**, and a binary check
> would block precisely the correct "revise the rule" outcome.
>
> **Where does the "expected" number come from?** "The other environment returns X" is evidence **about that
> environment**, never a specification — and if that environment runs the same code path you're fixing,
> matching it reproduces the bug. Derive the target from the document's structure and the contract, and say so
> plainly when the ticket's expectation is wrong (real case: the ticket said 12; the correct answer was 13).

### Tool-precedence (see [`metodologia_en/tools.md`](./ejemplos/metodologia_en/tools.md))
`.cursor/rules/` and `AGENTS.md` don't just say *what* to do, but **with which tool and in what order**
(cheap→expensive, deterministic→probabilistic):
```
Orient       -> kg skill (ticket knowledge graph) · STATUS.md/ledgers · git · gh   (no inference)
Navigate     -> CodeGraph codegraph_explore (MCP): source+paths+blast radius+coverage (1 call; treat it as ALREADY read)
Refactor-chk -> Serena find_referencing_symbols (MCP) (disambiguates by class)  MANDATORY before renaming/deleting
Diagnose     -> deterministic oracle (parser/validator/_diag_*.py)  (no inference, reproducible)
Environment  -> AWS CLI (CloudWatch, lambda get-function, SQS/DLQ)   (read-only)
Contract     -> Playwright (MCP) / F12 against the output endpoint
Deployed     -> Docker: repro inside the runtime image (real stage = wrapper); green tests != what ships
Only at the end -> the agent turn, to VERIFY the fix (not to diagnose)
```

### Method permissions (different mechanism from Claude Code, same policy)
Claude Code: hand-curated allowlist in `settings.local.json` (`mcp__serena__…`). Cursor: (1) **Rules**
— prevalence and "no push without asking"; (2) UI/settings **Approvals**; (3) **Hooks** — e.g.
`beforeShellExecution` for push/PR/deploy. Do not copy Claude Code's `allow` JSON: re-implement the
*policy* with rules + hooks + `permissions.json`.

---

## 13. The method's tools

**Setup / smoke of the 5 tools in the demo repo:**  
[`AGENT_SETUP_TOOLS.md`](./docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md) ·
`D:\repos3\ILS_2\document-parser-lambda\AGENT_SETUP_TOOLS.md`.

### CodeGraph ([`ejemplos/codegraph/`](./ejemplos/codegraph/)) — local code intelligence (via MCP)
Tree-sitter index → SQLite in `.codegraph/` (no API keys). Returns symbols + call paths +
blast radius + **test-coverage flags**. Benchmarks: 58% fewer tool calls, 22% faster.
```bash
codegraph init        # creates .codegraph/ and builds the index   codegraph sync   # incremental after editing
codegraph explore "<symbol|question>"       # source + paths + blast radius, in 1 round-trip
codegraph impact|callers|node <symbol>      # blast radius / callers / 1 symbol + trail
```
```jsonc
// .cursor/mcp.json — manual registration, there is no "codegraph install --target=cursor"
{ "mcpServers": { "codegraph": { "command": "codegraph", "args": ["serve", "--path", "<repo>", "--mcp"] } } }
```
It is the **first** navigation tool (before grep/Read); treat the source it prints as **already read**
(do not re-open that file). The MCP **has no default project** unless you set `--path`: do it and
`codegraph_explore` will not need `projectPath`; pass it only to query **another** indexed repo. On WSL2
`/mnt` the watcher can miss changes → `codegraph sync` after editing.

### Serena ([`ejemplos/serena/`](./ejemplos/serena/)) — semantic navigation via LSP (MCP)
```jsonc
// .cursor/mcp.json
{ "mcpServers": { "serena": { "command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"] } } }
```
Key tools: `find_symbol` (with `body=true`), `get_symbols_overview`, `search_for_pattern`, and above all
**`find_referencing_symbols`** — the **precise** check before renaming/deleting: it disambiguates
same-named methods by class, where CodeGraph's flat `impact` mixes them up. It complements CodeGraph, it
does not replace it. The [`refactor-scout`](./ejemplos/subagents/prompts/refactor-scout.md) template
packages the CodeGraph→Serena→grep order as a subagent procedure.

### GSD ([`ejemplos/gsd/`](./ejemplos/gsd/)) — the method turned into tooling, **Claude Code only**
Phase-based cycle with versioned state in `.planning/` and specialized subagents (`gsd-planner`,
`gsd-plan-checker`, `gsd-executor`, `gsd-code-reviewer`, `gsd-verifier`, `gsd-phase-researcher`) — **there
is no official port to Cursor**.

**Practical Cursor equivalent:**
```
Plan mode                    -> discuss gate -> plan (human approves before touching code)
skill methodology-plan       -> fills the plan template before implementing
Task / subagents + prompt    -> substitutes for the gsd-* roles (planner/executor/verifier)
data/changes/                -> the same state as in Claude Code (not GSD's .planning/)
```
> **Honesty — do we use it here?** **No.** This project does not run GSD (it does not exist in Cursor) nor its
> equivalent: it uses the 11-stage workflow + `data/changes/`, more refined and tuned for per-ticket fixes on
> a service in production. GSD (Claude Code) makes more sense in a **multi-component greenfield**.

---

## 14. Transferring the methodology

Real material: [`docs/ai-agents-code-methodology/`](./docs/ai-agents-code-methodology/) —

- **Cursor:** [`CURSOR_ADAPTATION.md`](./docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md) +
  surface [`cursor/`](./docs/ai-agents-code-methodology/cursor/) (`AGENTS.md.example`,
  `hooks.json.example`, `mcp.json.example`, `rules/00-methodology-core.mdc`,
  `rules/01-tool-prevalence.mdc`, `rules/02-gates-and-handoff.mdc`, `skills/kg/`, `skills/kg-refresh/`,
  `skills/methodology-plan/`, `skills/sanitise-diff/`, `hooks/block-external-git.ps1`) +
  [`scripts/bootstrap-cursor-repo.ps1.txt`](./docs/ai-agents-code-methodology/scripts/bootstrap-cursor-repo.ps1.txt)
- Shared: [`TRANSFER_AND_BOOTSTRAP.md`](./docs/ai-agents-code-methodology/TRANSFER_AND_BOOTSTRAP.md),
  [`templates/CURSOR_WORKING_AGREEMENT_TEMPLATE.md`](./docs/ai-agents-code-methodology/templates/CURSOR_WORKING_AGREEMENT_TEMPLATE.md),
  [`scripts/bootstrap-new-repo.ps1.txt`](./docs/ai-agents-code-methodology/scripts/bootstrap-new-repo.ps1.txt)
- The same pack ships [`COPILOT_ADAPTATION.md`](./docs/ai-agents-code-methodology/COPILOT_ADAPTATION.md) —
  this repo is not a special case: the discipline reaches a third agent.

**What travels unchanged:** plan→agreement→implement · verify against the consumer's contract · solve
the general class · durable trail · the human owns everything external.

**What changes — the surface (full table):**
```
CLAUDE.md (+ hierarchy)              -> AGENTS.md + .cursor/rules/*.mdc
Skills ~/.claude/skills/             -> .cursor/skills/ (or ~/.cursor/skills/) — SAME SKILL.md
Allowlist settings.local.json        -> permissions.json (mcpAllowlist / terminalAllowlist)
Hooks (exit 0/2, stdin JSON)         -> .cursor/hooks.json (permission JSON, stdin/stdout, failClosed)
Plan mode                            -> Plan mode (same discipline, same name)
Subagents (Task) + Agent Teams       -> .cursor/agents/*.md + built-ins — NO Agent Teams
claude -p (headless)                 -> agent -p (Cursor CLI print mode)
Auto-memory (MEMORY.md)              -> Memories (DISTINCT system, not 1:1)
Agent SDK (query/allowedTools)       -> Cursor SDK (Agent.prompt one-shot; Agent.create+send stream)
```

**Bootstrap in the target repo:**
```powershell
Expand-Archive ai-agent-methodology-package.zip -DestinationPath data/changes
Rename-Item …/scripts/bootstrap-new-repo.ps1.txt bootstrap-new-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1
# creates: STATUS.md · FOLLOWUPS.md · SHARP_EDGES.md · handover and QA templates

# Cursor: AGENTS.md + rules + skills + MCP + hooks
Rename-Item …/scripts/bootstrap-cursor-repo.ps1.txt bootstrap-cursor-repo.ps1
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1
```
(The script travels as `.ps1.txt` to dodge email active-content blocking.)

**Fallback without a ticket knowledge graph** (80% of the value, minimal setup): newest-first `STATUS.md` +
per-ticket folders · lexical search by symptom/symbol/contract field · commit history (file
overlap) as a lightweight substitute for the graph · a short "danger zones" section.

**First-day checklist:** fill in `STATUS.md` · 3-5 invariants in `SHARP_EDGES.md` · define the
output contract · scoped test commands · one complete issue with RED→GREEN + contract verification.

---

## 15. Machine sync

Two mechanisms, and they do **not** compete: **(A)** tarball+USB for a *full machine
bring-up*, and **(B)** shared object storage (S3) for the *day-to-day engineering record*.
(B) is the recent change and is what gets used daily; (A) remains the path when a machine
has to be stood up from scratch.

### A. Full bring-up: tarball + USB (asymmetric)

Real (sanitized) procedure that applies the same principles to an ops task
(see [`metodologia_en/machine-sync.md`](./ejemplos/metodologia_en/machine-sync.md);
runbooks from the real installation in [`docs/synchro/`](./docs/synchro/)). The original runbook was born in
Claude Code — the adaptation table:
```
Claude Code                          Cursor
Pointer in CLAUDE.md                 Pointer in AGENTS.md / on-demand rule
Bundle ~/.claude (skills + memory)   Skills in .cursor/skills/ or ~/.cursor/skills/; Memories != MEMORY.md
codegraph MCP in ~/.claude.json      Re-pin --path in .cursor/mcp.json on the laptop
/kg-refresh Claude skill             Cursor pack kg-refresh skill + same kg_refresh.sh scripts
```
Do not blindly copy a `~/.claude` tarball as "Cursor setup": carry `data/`, git repos, and reinstall the
`.cursor/` surface (methodology pack bootstrap). **Asymmetric:**

```bash
# OUTBOUND (main -> laptop): FULL COPY. -h dereferences the .aws symlink (critical);
# venvs/node_modules/caches are excluded; .gnupg is skipped if it doesn't exist.
WS=$(ls -d /mnt/*/ILS 2>/dev/null | head -1)          # DERIVE the root, don't assume it
tar -czhf ~/ils-migration-$(date +%Y%m%d).tar.gz \
  --exclude='*/node_modules' --exclude='*/.codegraph' --exclude='*/.venv' --exclude='*/__pycache__' --exclude='*.pyc' \
  -C "$(dirname "$WS")" "$(basename "$WS")" \
  -C /home/$USER .cursor .aws .ssh
# USB: WSL does not auto-mount a USB plugged in after boot -> sudo mount -t drvfs F: /mnt/f ; copy, sync,
# and verify byte for byte (stat -c %s of source and destination match) before ejecting. The bundle grows (~1.5 GB).
# On the target: bash data/machine-sync/target-setup.sh  -> reinstalls the CodeGraph CLI, updates GSD if it's
# behind, fixes the MCP --path to the laptop's real root (in .cursor/mcp.json), rebuilds the index.

# INBOUND (laptop -> main): DELTA ONLY. The code is already on GitHub.
git fetch origin                                      # the only network op (read-only)
cp data/changes/STATUS.md data/changes/STATUS.md.mainbak   # backup FIRST
tar -xzf "$TARBALL" -C "$REPO"                         # only the gitignored docs under data/
diff data/changes/STATUS.md.mainbak data/changes/STATUS.md # additions only? keep. own edits? STOP
```

**Two gaps, two idempotent subcommands** (the workspace carries a `kg` graph — §16): on a new laptop,
`kg_refresh.sh bootstrap` installs the tooling that doesn't travel in the bundle and pins the interpreter (and
re-bootstraps `.cursor/`: MCP `--path`, skills, if that machine didn't have them); and since agent memory
does **not** travel the same way as in Claude Code, decide explicitly what travels: `snapshot-memory` parks it under
`data/` (so it travels) and `restore-memory` merges it back with a backup on the main machine, before
`kg-refresh` — do not assume editor Memories sync by themselves. Single entry point for the
laptop's agent: `LAPTOP_START_HERE.md` (restore → `bootstrap` → carry on as usual → send the delta). The
graph is a **derived** artifact: it is rebuilt wherever the corpus is. ⚠️ **But the curated names overlay
does travel both ways** — it lives inside the generated tree and nothing regenerates it, so rebuilding
without it leaves every community unnamed (see the §15B table and the Part 3 correction).

Guardrails (the landing is driven **by an agent**, with an `INSTRUCTIONS.md` written *for* it): only
non-destructive actions (rename, don't delete; never two move ops at once on a Windows mount); no
git writes to remote (no push/merge/PR); STOP and ask when in doubt; the AWS CLI binary does
**not** travel in the bundle (reinstall on the target + `aws sso login`) — same for the CodeGraph CLI and the
`.codegraph/` index, which `target-setup.sh` restores. The human owns external
actions; the agent prepares and reports with evidence (file counts, PR statuses).

### B. The shared record: `data/` over S3

The tarball solves **transport**, not **sharing**. Add a third machine and a second person
and three costs appear: the record is gitignored → it **can't be linked** from a ticket or
PR; moving degenerates into archiving everything; and every teammate ends up with **their
own private index** of the same history. Full runbook:
[`docs/synchro/s3-sync/README.md`](./docs/synchro/s3-sync/README.md).

```bash
# Dry-run is the DEFAULT: nothing transfers until --go
./data-pull.sh            # preview  ->  ./data-pull.sh --go
./data-push.sh            # preview  ->  ./data-push.sh --go
./mount-data.sh           # live shared view, READ-ONLY (~/s3-<name>-data)
./validate.sh             # a machine isn't set up until this prints MACHINE READY
```

| Rule | Why |
|---|---|
| Narrow scope: only `changes/**/*.md` + the graph | Confidentiality and size. **No** client documents, fixtures or binaries without the bucket owner's sign-off. |
| **Write via sync, read via read-only mount** | Object storage has no locking and no atomic rename: a writable mount corrupts, and you find out weeks later. |
| Dry-run by default; `--delete` is a separate opt-in | An exact mirror from a stale local view **erases** what a teammate just pushed. |
| Docs = source of truth; the graph is **derived** | Per-ticket files almost never collide. The generated graph is the **only** real contention point → **one** machine publishes it. ⚠️ "Rebuild locally" is only safe if the generated tree is *purely* derived — see the next rows. |
| **"Derived" is a property of the file, not of the folder** | Inside the generated tree lives a **hand-authored** file (the curated community names) that nothing regenerates: on a rebuild, **<1%** survived. Classify per file — *source* / *derived* / *authored inside derived* — and treat the third as source. |
| **Pairs must move together** | The names overlay is only meaningful against the graph it came from, but sync compares **object by object** → new graph + old names = names glued to the wrong community, **with no error**. Stamp the overlay with a **fingerprint of the graph** and make the health check fail loudly. |
| **Coordinate without locks** | To request a rebuild, each contributor writes **their own file** in a queue (`kg_refresh.sh request` → `refresh_queue/<utc>-<machine>.request`). Distinct keys never collide; a shared queue file would be lost to last-writer-wins. Same trigger contract a scheduled job can consume later. Single publisher is scaffolding, not architecture. |
| Bucket versioning on | The recovery net — turn it on before the first accident, not after. |

**The agent-specific part — the machine has a role.** Once the same record is reachable
from several machines with different permissions, the session must know **where it is and
what it may do** *before* acting; otherwise a *contributor* machine will republish the
shared graph — the one thing it must not do — and report it as work done. Each machine
declares `MACHINE_NAME`/`MACHINE_ROLE` in its `config.env`, `identity.sh --write` generates
a **machine-local** `IDENTITY.md` (with live checks: authenticated account, bucket
reachable, mount present), and `AGENTS.md` **points at it**, so every session reads its own
role first. `IDENTITY.md` is the one file that must **not** be the same everywhere:
gitignored, never synced, never packaged.

> **Before the first shared push:** scrub embedded credentials from the records. This is not
> hypothetical — investigation notes capture signed URLs and tokens **on purpose**, as
> evidence of a bug, and those are exactly the strings you don't want in shared storage. Run
> the sanitisation scan (`sanitise-diff` skill) over the **whole** record, not over a
> diff.

---

# PART 3 — The ticket knowledge graph (graphify)

## 16. Ticket knowledge graph

**Technology: `graphify` — not CodeGraph.** CodeGraph is only the analogy (same role, different domain): if
CodeGraph indexes the *code*, this graph indexes the **project's memory** — per-ticket writeups, "sharp
edges", runbooks, memory notes. The build pipeline was originally generated **in Claude Code**; today
query and refresh live as skills, portable without changes. All the real material is in
[`docs/knowledge-graph/`](./docs/knowledge-graph/): [`design.md`](./docs/knowledge-graph/design.md) (Phase 1
design, a spike with a keep/extend/replace decision), scripts, tests, manifest and the real output.
Additional narrative summary: [`docs/KNOWLEDGE_GRAPH.md`](./docs/KNOWLEDGE_GRAPH.md).

### The pieces

| Piece | What it is |
|---|---|
| `kg` (skill) | Query: `explain` / `path` / `find` — deterministic, **no LLM** |
| `kg-refresh` (skill) | Rebuilds the graph: `prepare` → semantic extraction → `finalize` |
| [`kg_query.sh`](./docs/knowledge-graph/kg_query.sh) | Wrapper around `graphify explain`/`path` over `output/graph.json` + `find` (discover node names); resolves interpreter and graph path, cleans warnings |
| [`kg_refresh.sh`](./docs/knowledge-graph/kg_refresh.sh) | Deterministic bookends: `prepare` / `finalize` / `bootstrap` / `snapshot-memory` / `restore-memory` |
| [`build_manifest.py`](./docs/knowledge-graph/build_manifest.py) / [`stage_corpus.py`](./docs/knowledge-graph/stage_corpus.py) | Enumerate and stage the corpus with provenance-preserving names (`sst-5468__sst-5468.md`, `hub__STATUS.md`, `memory__x.md`) |
| `test_kg_corpus.py` · `test_kg_query.py` · `test_kg_refresh.py` | The bookends are **tested** — the pipeline is infrastructure, not a one-off |
| [`manifest.txt`](./docs/knowledge-graph/manifest.txt) | The explicit, diffable corpus (~116 files, ~196k words) |

**Is `kg` a slash command or a skill? A skill** — the name-invocation mechanism (`/kg` in Claude
Code, `kg` in Cursor) does not by itself distinguish them. What makes it a skill: it carries **assets** (the shell
wrappers), it has a **`description`** so the agent auto-selects it at the orient stage without you
typing it, and `kg-refresh` **orchestrates a step of the agent itself** (semantic extraction) — a slash
command is just a saved prompt. The definitions (`SKILL.md`) live **at user level, outside the
repo**: `~/.cursor/skills/kg/`, `~/.cursor/skills/kg-refresh/` (or `~/.claude/skills/…` — **same
file**, both products read it). Deliberate location: (1) **confidentiality** — nothing of the KG lives in
committable paths; (2) **scope** — user-level makes it available in any session on the machine,
consistent with the fact that the graph also indexes agent memory. And since user config travels in the
machine-sync outbound tarball (§15), the skills reach the laptop with the full copy; the
(derived) graph is rebuilt there with `bootstrap` + `kg-refresh`.

### Building and querying

```bash
# build / refresh (the only agent step is semantic extraction, with parallel subagents)
kg_refresh.sh prepare        # manifest -> stage _corpus/ -> copy to a scratch OUTSIDE the repo
                              # node/edge extraction + clustering -> HTML/JSON/report
kg_refresh.sh finalize       # copy artifacts to output/ + leak-check (nothing outside data/)

# query (zero LLM: kg_query.sh reads output/graph.json directly)
kg explain <ticket|topic>    # a node's neighbors    (graphify explain)  <- the most common use
kg path <A> <B>              # shortest path A<->B (graphify path)
kg find <substr>             # discover a node's exact name
```

**Gotcha that holds the pipeline together:** `graphify` honors `.gitignore` and all of `data/` is ignored →
running the detector in place finds 0 files; the corpus is staged in a scratch outside the repo and the artifacts
are copied back. **That's why `kg-refresh` is a skill and not a script:** the semantic step is an agent
step; the bookends are deterministic.

### The real output (see [`output/`](./docs/knowledge-graph/output/))

- [`graph.html`](./docs/knowledge-graph/output/graph.html) — **interactive vis-network** visualization:
  node search, info panel, community filter. The screenshot for the deck is regenerated with
  [`presentacion/capture_kg_graph.py`](./presentacion/capture_kg_graph.py) → `presentacion/kg_graph.png`
  (same real graph, reused unchanged across both course volumes).
- `graph.json` — NetworkX node-link; **typed** edges (`relation`) with `confidence`
  (`EXTRACTED`/`INFERRED` + score). This is what `kg_query.sh` reads.
- [`GRAPH_REPORT.md`](./docs/knowledge-graph/output/GRAPH_REPORT.md) — the audit report:
  **507 nodes · 672 edges · 35 communities**; **92% `EXTRACTED`** · 7% `INFERRED` (mean confidence 0.7);
  god-nodes (the structural tickets, free onboarding) and "surprising connections" (twin lessons
  no one had connected by hand). The communities map to real danger zones
  ("Letter-End & Run-in Titles", "Title Detection Failures", "PDF Extractor Cascade"…).

### Hook-in and lifecycle

Hooked into the **history-first** rule of `.cursor/rules/00-methodology-core.mdc` (stage 1, Orient):
run `kg explain <ticket|topic>` *before* grepping `data/changes/`; one call surfaces the related tickets
+ the danger zone to read (it points to *what to read*, it doesn't replace it). Honesty: the real gain
is **recall in dense zones**; `EXTRACTED` = reliable, `INFERRED` = a lead to verify. In the real
installation everything lives under gitignored `data/` (the nodes carry internal names → internal; sharing outside =
a separate sanitization pass). It is a **derived** artifact: it's rebuilt wherever the corpus is (§15, with
`bootstrap` / `snapshot-memory` / `restore-memory` closing the loop).

> ⚠️ **Correction: "derived" is a property of the file, not of the folder.** This guide used to say the
> graph "never travels between machines" because it gets rebuilt. That holds **only while rebuilding is
> lossless**, and it stopped being so: inside the generated tree lives a **hand-authored** file — the
> curated community names — that nothing regenerates. A rebuild re-derives the graph's internal
> identifiers from scratch, so the names no longer attach to anything: measured on a real rebuild,
> **under 1% survived**, and even after fixing the underlying cause only ~38% carried across. Recreating
> them is an hour of judgement, not a command. Classify **per file**: *source*, *derived*, and
> **"authored but living inside the derived tree"** — the third is treated as source: it always travels.
>
> And because the names overlay is only meaningful against the exact graph it came from, while
> `aws s3 sync` compares **each object independently**, a machine can end up with a new graph and an old
> overlay. That raises no error: it produces **names attached to the wrong communities**. Stamp the
> overlay with a **fingerprint of the graph** it was built against, and make the health check fail loudly
> when they disagree. A per-file sync cannot express atomicity; the check has to live in the data.

> **Cost — honest, and why it pays off.** "No LLM at query time" is **not** "free": the expensive reasoning
> is paid **once** when building the graph (`kg-refresh`, with subagents); each `kg` query is then a
> deterministic algorithm over `graph.json` → **zero inference**, with the only cost being that the agent reads
> a short output (like a `grep`) — a **smaller, targeted** cost, not zero. The cost of building (graph,
> oracles, deterministic skills) is **amortized**: it's an investment → no inference per query, **deterministic
> and reproducible** answers (better outcome), expensive reasoning replaced by cheap lookup →
> **time and money saved** per task. Paid once, collected on every use — from either
> agent.
