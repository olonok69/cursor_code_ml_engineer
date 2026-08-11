# Cursor — Speaker guide (course in three parts)

> English version of [`GUIA_PRESENTACION.md`](./GUIA_PRESENTACION.md).
> Deck: [`presentacion/Cursor_Presentacion_EN.pptx`](./presentacion/Cursor_Presentacion_EN.pptx)
> (regenerate with [`presentacion/build_pptx_cursor_en.py`](./presentacion/build_pptx_cursor_en.py)).

> Narrative guide for the course/workshop. It is written for the **speaker**: each section maps to a
> block of slides in the deck ([`presentacion/`](./presentacion/)) and includes the story to tell,
> the key points, and a slide-ready closing line 🗣️. Audience: **technical / developers**. This is the
> **Cursor volume** of the course — the direct counterpart of
> [`GUIA_PRESENTACION_EN.md`](https://github.com/olonok69/claude_code_ml_engineer/blob/HEAD/GUIA_PRESENTACION_EN.md)
> (Claude Code, sibling repo), same structure and section numbering.
>
> The deck is **a single presentation** with **three distinct parts**:
> - **Part 1 — Cursor:** the tool, from the editor on your desk to agents in the cloud.
> - **Part 2 — The methodology:** how you actually work with an agent in production. It is **tool-agnostic**
>   — it is demonstrated with Cursor, but it was born in Claude Code and travels between both
>   (section 10, the most real example in the course).
> - **Part 3 — The ticket knowledge graph:** the same complete case built with **graphify**
>   as in the Claude Code volume — the pipeline was generated there, but the `kg`/`kg-refresh` skills are the
>   **same `SKILL.md`** and work the same way from Cursor.
>
> The implementation detail (configs, copy-paste code) lives in
> [`GUIA_TECNICA_EN.md`](./GUIA_TECNICA_EN.md) and in [`ejemplos/`](./ejemplos/). The
> [`docs/`](./docs/) folder is reference material from a real installation where the
> methodology is applied daily. **Live demos by slide:** [`DEMO_RUNBOOK_EN.md`](./DEMO_RUNBOOK_EN.md).
> Spanish originals: [`GUIA_PRESENTACION.md`](./GUIA_PRESENTACION.md) ·
> [`GUIA_TECNICA.md`](./GUIA_TECNICA.md) · [`DEMO_RUNBOOK.md`](./DEMO_RUNBOOK.md).
>
> **Verification note (2nd pass):** Cursor-specific content (Skills, Marketplace,
> Subagents, headless CLI, hooks, SDK…) was checked against `docs.cursor.com` on **9 August 2026**.
> Cursor moves fast — before you give the course, check whether anything has moved again.

---

## Index

**Part 1 — Cursor**

0. [What Cursor is (framing)](#0-what-cursor-is)
1. [Installation and basic usage](#1-installation-and-basic-usage)
2. [Memory, instructions, and sessions](#2-memory-instructions-and-sessions)
3. [Context: context window and prompt caching](#3-context)
4. [MCP — connecting your tools](#4-mcp)
5. [Skills and Marketplace](#5-skills-and-marketplace)
6. [Subagents](#6-subagents)
7. [Automation](#7-automation)

**Part 2 — The methodology (agnostic)**

8. [The methodology: principle, workflow, and a real example](#8-the-methodology)
9. [The method's tools: CodeGraph, Serena, GSD…](#9-the-methods-tools)
10. [Transferring the methodology: from Claude Code to Cursor](#10-transferring-the-methodology)
11. [Machine synchronization (tarball + S3)](#11-machine-synchronization)

**Part 3 — The ticket knowledge graph (graphify)**

12. [The ticket knowledge graph](#12-the-ticket-knowledge-graph)
13. [Closing](#13-closing)

---

# PART 1 — Cursor

## 0. What Cursor is

**Story:** Cursor is a code editor with a built-in agent that **reads your codebase, edits files,
runs commands**, and integrates with your tools — it started as a VS Code fork, but the real leap is
not the editor: it is the agent. It is not autocomplete: it understands the whole project and works across
multiple files and tools. And the same agent lives on three surfaces: the **editor**, the **CLI** (`agent`),
and the **cloud** (Background/Cloud Agents) — your `AGENTS.md`, rules, and MCP servers work across all three.

**What you can do with it (the headlines):**
- Automate the tedious parts: write tests, fix lint, resolve merge conflicts, update deps.
- Build features and fix bugs by describing them in natural language (Agent mode), with Plan mode first.
- Bugbot reviews every PR automatically on GitHub/GitLab/Bitbucket, with no custom script.
- Connect your tools with MCP; run headless in Unix pipelines; schedule with Automations.

🗣️ *"It's not autocomplete that suggests lines: it's a collaborator that plans, edits across files, and verifies — and it lives in the cloud when you need it."*

---

## 1. Installation and basic usage

**Story:** Installing is trivial — the editor downloads in one click. What matters is understanding that there are
**three ways in** (editor, CLI, cloud) and **two modes** of working inside them.

**Installation:**
```bash
# Editor: download from cursor.com (macOS / Windows / Linux)

# Cursor CLI (agent) — headless-capable
# macOS / Linux / WSL:
curl https://cursor.com/install -fsS | bash
# Windows PowerShell:
irm 'https://cursor.com/install?win32=true' | iex
```
Then, in any project:
```bash
cd your-project
agent             # interactive CLI; first time: agent login (or CURSOR_API_KEY)
```

**The two modes (the idea to make stick):**
- **Interactive** — editor (chat / Agent mode) or CLI `agent`. This is where **Plan mode** lives: Cursor proposes
  a plan before touching anything and you approve it.
- **Headless (`agent -p` / `--print`)** — a single prompt, result on stdout. For scripts and CI; combine with
  `--force` if it must apply edits, and with `--output-format text|json` depending on the consumer:
  ```bash
  agent -p --trust "summarize the changes on this branch"
  agent -p --trust --output-format text "security-review the files touched vs main"
  # Log content: pass it in the prompt or reference the file (do not assume stdin pipe → prompt)
  agent -p --trust "Read app.log (last ~200 lines) and tell me if you see anomalies"
  # --trust: first time in a workspace (or use agent login + trust interactively)
  ```

**Surfaces:** editor (chat + Agent mode + Plan mode, inline diffs), Cursor CLI (`agent` in the terminal —
ideal for SSH/servers), Background/Cloud Agents (`cursor.com/agents`, async cloud tasks with no editor
open), Bugbot (automatic PR review).

🗣️ *"Interactive to think with you; `agent -p` to drop it into scripts and CI. Same Cursor, three surfaces."*

---

## 2. Memory, instructions, and sessions

**Story:** The agent is only as good as the context you give it — and how you **manage** it. Three pieces:
`AGENTS.md` + rules, permissions, and Cursor Memories (a separate system).

### `AGENTS.md` + `.cursor/rules/*.mdc` — the project's memory
`AGENTS.md` at the root is the always-loaded orientation file (nested files per
subfolder are allowed: the most specific wins). Mandatory gates and tool precedence also live in
`.cursor/rules/*.mdc` with `alwaysApply: true`. That is where code standards, architecture decisions,
commands, and checklists go.

**The classic mistake and how I solve it — the two-tier pattern (same spirit as Claude Code):**
- **Tier 1 (always loaded):** small. Only orientation + **one-line pointers**.
- **Tier 2 (on demand):** the detail in files the agent reads only when needed.
- *Write-once* rule: each fact is written in a single place; `AGENTS.md`/rules carry the pointer, not the copy.
- Same trim goal as in the original Claude Code project (~73% without losing information).
  (Sanitized example in [`ejemplos/agents-md/`](./ejemplos/agents-md/).)

**Rules — the mechanism with no 1:1 equivalent in `CLAUDE.md`:** `.mdc` files with frontmatter
(`description`, `globs`, `alwaysApply`) and **four modes**: Always Apply, Apply Intelligently, Apply to
Specific Files, Apply Manually. Inside a rule, `@file` includes another file's content when
loading it (eager) — **this syntax does not exist in `AGENTS.md`**, only in `.mdc`.

### Permissions
`~/.cursor/permissions.json` (and `<repo>/.cursor/permissions.json`) defines allowlists with fields
**`mcpAllowlist`** and **`terminalAllowlist`** — `server:tool` entries with globs (`codegraph:*`,
`*:search`). When the file defines a key, it **replaces** the UI allowlist for that type.
Same posture as Claude Code — "the human owns external actions" — reinforced with
rules ("no push without asking") + UI approvals + hooks (`beforeShellExecution` to veto by
content). The CLI has its own permission system (`cli-config.json`), separate from the IDE.

### Memories — a DISTINCT system
Cursor generates **Memories** automatically from your chats — they are not files you write, and
**not the same mechanism** as Claude Code's auto-memory. Treat them as a complement, not a
substitute for the two-tier pattern: do not stop maintaining `AGENTS.md`/rules thinking Memories will
cover it.

### Sessions that travel
Same agent, same configuration, in editor, CLI, and Background/Cloud Agents (`cursor.com/agents`; you follow
progress from the web). Bugbot runs on every PR on its own, without you invoking it.

🗣️ *"The always-loaded `AGENTS.md` should be a 30-second onboarding, not a dumping ground. Pointers, not copies — and Memories are something else."*

---

## 3. Context

**Story:** This is the section that explains **why** the two-tier pattern from the previous section is not
an obsession: the context window is the resource that governs performance **and** cost. Two halves: managing it
(context window) and understanding what you can/cannot control about caching in a product that does not expose
the API directly. Material: [`ejemplos/context/`](./ejemplos/context/) and
[`ejemplos/prompt-caching/`](./ejemplos/prompt-caching/).

### 3a. Context window — the resource that governs everything

**What fills it before you type anything:** the system/agent prompt (hidden, always first), the
`alwaysApply` rules + `AGENTS.md` (you control these — that is why the two-tier pattern), Memories if any
(different system; review what snuck in), the MCP tools index, and then conversation, files read,
command output (grows every turn).

**The knobs:**
- Editor context ring — visualize usage block by block. Measure before optimizing.
- New chat / clean session — reset between unrelated tasks (in CLI: a new `agent` invocation).
- `/rewind` — go back to a previous message (CLI; enable in config).
- `/summarize` (alias `/compress`) — summarize and free context manually.
- Cursor **auto-resumes** as it approaches the limit — do not assume exact parity with Claude Code's `/compact`;
  the mechanism is different even though the goal is the same.

**Hygiene we actually apply:** minimal `AGENTS.md`/rules (two-tier); `@file` in rules only when
needed (eager load — use carefully); MCP in moderation (each server adds its tools block);
Subagents for research (section 6) so the noise doesn't live in your session; Plan mode before Agent
mode to separate exploration from implementation; targeted reads instead of "understand all of auth".

### 3b. Prompt caching — what belongs to the API, and what you control in the product

**The mechanism (Anthropic API, not Cursor):** every turn resends ALL the context. The API caches the
**stable prefix** (strict order: `Tools → System → Messages`): writing cache costs 1.25× (2× at 1h
TTL), **reading it costs 0.1×**. A 50-turn session rereads the prefix 50 times at a discount price. This
is from the Anthropic API — but if you automate with the **Cursor SDK** against Claude, it applies the same way.

**In the Cursor product you do not have that knob exposed** (no env vars like in Claude Code, no
visible `cache_control`) — whatever the model provider decides underneath applies. What you *do* control:

- Small, **stable** `AGENTS.md` + rules → a prefix that does not change between turns → better behavior.
- Editing rules/`AGENTS.md` mid-session → you pay the tax again.
- Many active MCP servers → large, changing tools block → more fixed context.
- New session / clean chat between unrelated tasks → avoid dragging an infinite transcript.
- Do not assume Cursor exposes `cache_control` like the API — it is a different product; do not copy Claude Code
  env vars (`ENABLE_PROMPT_CACHING_1H`, etc.); they do not exist here.

Runnable demo with the direct API (to understand the mechanism, not the product):
[`ejemplos/prompt-caching/cache_demo.py`](./ejemplos/prompt-caching/cache_demo.py).

**The bridge that joins 3a and 3b (and previews Part 2):** lean, stable context **performs better in any
product**, even if you never see the discount on screen. And the methodology's "tool precedence"
(CodeGraph before reading files) is, at bottom, context policy: maximum signal per token.

🗣️ *"The context window is your budget in any agent; prompt caching is API, not product — but lean and stable wins on both."*

---

## 4. MCP

**Story:** **MCP (Model Context Protocol)** is the same open standard as in Claude Code — CodeGraph,
Serena, and Playwright speak MCP in both products. The only thing that changes is where the configuration lives.

**The two scopes (where the config lives):**
- **project** → `.cursor/mcp.json` at the root, **versioned**, shared with the team.
- **user** → `~/.cursor/mcp.json` — editable **directly** (or via Settings → MCP in the editor).

**Adding one** (manual JSON edit — there is no `agent mcp add` command):
```jsonc
// .cursor/mcp.json
{ "mcpServers": { "serena": {
    "command": "uvx", "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server"] } } }
```
After editing `.cursor/mcp.json`: **reload/restart Cursor** — there is no hot-reload.

**The ones I use daily (the 5 from Part 2):** `codegraph` (code graph), `serena` (semantic
navigation), `playwright` (UI / contract in the browser), `context7` (up-to-date library docs), and the
**`kg`** skill (ticket graph via scripts in the repo — not an MCP server). `supabase` is only an optional
example of MCP + a secret via env var — **not** required for the course.

**Verification in the demo repo (ILS):** full checklist so an agent configures and installs the 5
tools and smoke-tests them →
[`docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md`](./docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md)
and, in the live repo, `document-parser-lambda/AGENT_SETUP_TOOLS.md`. Summary: open **that** repo in Cursor
(not only the parent workspace), correct CodeGraph `--path` pin, `codegraph` on PATH + **reload**,
MCP green, then one test prompt per tool.

**Best practices:** secrets via environment variable (never in the versioned JSON); server available
≠ tool allowed (`permissions.json` still controls access); and — this links to section 3 — **every
server adds context**: disable the ones the project doesn't use. Example config in
[`ejemplos/mcp/`](./ejemplos/mcp/).

**The distinction to make stick:** servers **are not installed in `AGENTS.md`** — that file is
prompt, not configuration. `.cursor/mcp.json`/`~/.cursor/mcp.json` (or a pack in the repo) provide the
**capability**; `AGENTS.md`/rules provide the **judgment** — the *trigger map* that makes the agent reach for the
right tool without being asked ("CodeGraph before reading whole files"). Installing turns "I don't
have the tool" into "I have it"; the rules turn "I have it" into "it gets used in the right order" (that is the
precedence of Part 2).

🗣️ *"MCP turns Cursor from 'knows code' into 'knows YOUR system': your docs, your tickets, your browser — the same standard as in Claude Code."*

---

## 5. Skills and Marketplace

**Story:** This is the section where the Cursor course and the original diverge most — and where they converge
again. When the first Cursor adaptation guide was written, **neither Skills nor Marketplace existed**
in the product. Today both are real, and one of the two capabilities is no longer a gap with Claude Code:
it is literally the **same file**.

1. **Tools** — what the agent can *do*: Read/Edit/Shell/Grep + Task + `mcp__*`. Governed by
   `permissions.json`.
2. **Skills** — `.cursor/skills/<n>/SKILL.md` with frontmatter `name` + `description`; the agent
   **auto-selects** it by that description, same as in Claude Code.
3. **Direct interop with Claude Code:** Cursor also reads `.claude/skills/` — the **same `SKILL.md`**
   works in both products with no translation. That is the basis for why the `kg`/`kg-refresh` skills in
   Part 3 work the same here.
4. **Marketplace** (`cursor.com/marketplace`) — installable packages of skills + subagents + MCP + hooks +
   rules. There is no `/plugin install` command: you browse and install from the product marketplace.

**What is NO LONGER a gap vs Claude Code:** check `docs.cursor.com` before assuming something
"has no equivalent" — this is the clearest example that Cursor's surface moves fast.

🗣️ *"Skill = a capability Cursor decides to use by its description. Marketplace = the versioned delivery. And the SKILL.md — literally the same file as in Claude Code."*

---

## 6. Subagents

**Story:** The fourth layer of extensibility: not *what Cursor knows how to do*, but how many agents work and
how they coordinate. Two steps: native subagents → real parallelism with Background/Cloud Agents — and
a deliberate absence to name: there are no Agent Teams. All the material in
[`ejemplos/subagents/`](./ejemplos/subagents/).

### 6a. Subagents (native) — isolating context

Delegation with **isolated** context per subagent — only the summary returns to your main session.
Invoked in natural language (or `/name`); parallel execution for independent work.
Built-ins documented today: **Explore**, **Bash**, **Browser** (plus Task-environment types depending on
version). Do not assume the list without checking `docs.cursor.com/subagents`.

**Custom subagents — yes, there is a definition file:** `.cursor/agents/<name>.md` (project) or
`~/.cursor/agents/` (user), with frontmatter `name` + `description` (+ optional `model`, `readonly`,
`is_background`). Cursor also reads `.claude/agents/` and `.codex/agents/` for compatibility. Lightweight
alternative: a prompt/skill template you paste at launch (examples in
[`ejemplos/subagents/prompts/`](./ejemplos/subagents/prompts/)):
> *"Act as refactor-scout: use CodeGraph `codegraph_explore` and THEN Serena
> `find_referencing_symbols` before proposing the rename."*

**The gotcha to tell:** the subagent **does not inherit your conversation** — the necessary context goes in
the launch prompt, same as in Claude Code.

### 6b. What does NOT exist: Agent Teams — the substitute is parallelism with Background/Cloud Agents

Cursor **does not have** the equivalent of Agent Teams (lead + teammates + shared inbox with direct
messaging). Do not try to port it 1:1 — there is no equivalent product. The pragmatic substitute: several
**Background/Cloud Agents** in parallel (`cursor.com/agents`), each a full session, on its own
branch, **without coordinating with each other** (no shared inbox). Ask in natural language: *"launch three
Background Agents, one per module, each on its own branch; you review and merge."* A human (or the
main agent) integrates the results.

### 6c. Subagent vs. Background/Cloud Agent (the decision slide)

| | Subagent | Background / Cloud Agent |
|---|---|---|
| Context | Isolated; returns a summary | Full session, async, on its branch |
| Communication | Result only → main session | None between agents (no inbox) |
| Cost | Low (the expensive work dies outside) | High (N full sessions) |
| Use it for | Side-quests: research, verify | Long/async work, or real parallelism |
| Config | `.cursor/agents/*.md`, prompt or skill at launch | `cursor.com/agents` (UI / handoff `&`) |

**Bridge to Part 2:** GSD (Claude Code, section 9) packages roles as plugin-subagents; in Cursor
those roles live as `.cursor/agents/` + skills/prompts — **this project uses the `data/changes/` flow,
not GSD** (see the clarification in section 9).

🗣️ *"Subagent so the noise dies outside; Background/Cloud Agent for long or async work. No shared inbox: partition files/branches — each agent owns its own."*

---

## 7. Automation

**Story:** From hooks to agents in the cloud — from deterministic control to full autonomy. Everything in
[`ejemplos/hooks/`](./ejemplos/hooks/) and [`ejemplos/automation/`](./ejemplos/automation/).

### a) Hooks — deterministic control
A hook is a command that fires on an agent lifecycle event. You don't *ask* it to behave:
you **force** it. Contract:
- Config in `.cursor/hooks.json` (project) or `~/.cursor/hooks.json` (user).
- Event payload on **STDIN**, **JSON** response on STDOUT.
- Events: `beforeShellExecution`, `beforeMCPExecution`, `beforeReadFile`, `afterFileEdit`,
  `preToolUse`/`postToolUse`, `beforeSubmitPrompt`, `stop`, and more.
- Response `{"permission": "allow"|"deny"|"ask", ...}` — **`exit 2` also blocks**.
  For demos/handoff gates use **`deny`** (`ask` is often ignored).
- `failClosed`: if the hook crashes, it blocks (not *fail-open*) — a stricter posture than Claude Code's
  `exit 0` allows / `exit 2` blocks, though the spirit is the same.

### b) Headless — `agent -p --trust` in scripts and CI (see section 1; do not assume stdin pipe → prompt).

### c) CI/CD — Bugbot (native, PR review with no custom script) or Cursor SDK in your own GitHub Action.
   Example workflow in [`ejemplos/automation/github-action-cursor.yml`](./ejemplos/automation/github-action-cursor.yml).

### d) Automations — cron + event triggers:
- **Automations** (distinct from Background/Cloud Agents) — cron scheduling and event triggers:
  Slack, Linear, PR merged, PagerDuty.
- **Background/Cloud Agents** — for on-demand async work, not scheduled.

### e) Cursor SDK — for custom workflows:
```ts
import { Agent } from "@cursor/sdk";
// One-shot (sdk.ts / review.ts)
const result = await Agent.prompt(prompt, { apiKey: process.env.CURSOR_API_KEY!, local: { cwd } });
// Multi-turn / stream
const agent = await Agent.create({ apiKey: process.env.CURSOR_API_KEY, local: { cwd } });
const run = await agent.send(prompt);
for await (const ev of run.stream()) { /* … */ }
```
With `cloud: { repos, autoCreatePR }` so the agent opens PRs automatically in the cloud.

🗣️ *"With instructions you ask it to behave; with a hook you guarantee it — same as in Claude Code, different JSON contract."*

---

# PART 2 — The methodology (tool-agnostic)

## 8. The methodology

**Story:** Tools without a method = fast chaos. This is the most valuable part of the course: **how you
actually work with a coding agent on a project in production.** It is not a perfect workflow — it is the
one we use, subject to constant revision. And it is **agnostic**: in this volume it is demonstrated with Cursor, but
it was born in Claude Code (section 10 shows it transferring between both). All the material is in
[`ejemplos/metodologia_en/`](./ejemplos/metodologia_en/) (sanitized).

### The principle
> **The agent is a disciplined collaborator, not an autopilot. Autonomy is earned per-decision, not
> granted wholesale.** The agent owns research, plans, implementation, tests, and documentation;
> the human owns go/no-go decisions, scope, and **every external action** (push, PR, deploy).

### The 11-stage workflow

![Cursor workflow — 11 stages](./ejemplos/metodologia_en/flow.png)

Chained by **gates** (the coral boxes in the diagram); a red gate is a STOP = *write no code*:

1. **Orient** — history-first AND status-first (`kg` skill + `STATUS.md`/ledgers + `git`/`gh`). In
   Cursor, `alwaysApply` rules point at these ledgers. Skipping it is the #1 cause of rework.
2. **Inbound triage** — is the symptom real in the **output contract**? If not → push back, no code.
3. **Regression vs. pre-existing** — reproduce against the previous state before assuming blame.
4. **Investigate** — **deterministic oracle** (parser/validator) first; the model is reserved for verifying.
5. **Plan** — Cursor **Plan mode**; explicit **human agreement** before touching code.
6. **Implement** — Agent mode; TDD: RED (for the right reason) → GREEN, minimal change.
7. **Verify** — unit + scoped + regression + **outbound gate** (five checks): **(0) validate the measuring
   instrument** against a known-answer case before trusting it; (1) reproduce the contract at the **real
   output stage** (the *wrapper* that rebuilds the output, not an internal function); (2) have the local
   JSON match — verified **on the member list, never on a total**; (3) verify it **inside the deployed
   image**; (4) **look** at the rendered output before the PR. Green tests don't prove what gets shipped.
8. **Document** — why + what + handover + acceptance criteria, each thing **once**.
9. **Sanitize** — the `sanitise-diff` skill scans the **added lines** for names/IDs/secrets/attribution.
10. **Handoff** — the agent does **not** push/PR/deploy unless explicitly asked (`beforeShellExecution` hook
    + rules guarantee it). The human does push/PR/deploy. **In the original Claude Code flow, Cursor often
    did the handoff to another tool; here Cursor IS the agent** — the human gate
    remains mandatory; it does not change because the product changed.
11. **Automated review + persist** — triage Bugbot findings like a human's; `kg-refresh` skill
    if the graph should see the new ticket; codify lessons in `PLAYBOOK.md`.

> **Where is the cost? The agent is the orchestrator — and that's where the inference lives.** No stage is
> "free": the **tools** (`kg` skill, `git`, parsers, `pytest`, `grep`) provide **facts with no inference**, but
> the agent **reads** those facts, **reasons**, and **decides** — and that costs. The method doesn't remove
> the cost, it **concentrates** it: cheap in 1–3 and 9 (reading facts + deciding), **expensive in 5–6–7**
> (plan, code, verify), where the model *thinks and creates*. Cost-per-stage table:
> [`metodologia_en/WORKFLOW.md`](./ejemplos/metodologia_en/WORKFLOW.md).

> **The weak point turned out to be the gate, not the fix.** Five ways a green proves nothing, all five
> real: **(a)** a **broken instrument** — bypassing the constructor to probe a predicate leaves attributes
> unset; if the method reads them and has its own `try/except`, the error comes back as a plausible `False`
> and the probe reports a uniform "no" for *every* case; **(b)** a **total that matches** — one item wrongly
> added and one wrongly dropped cancel out, so assert on the **list** (titles/ids), not on `len(...)`; the
> closer the number lands to the expected one, the **more** suspicious it is; **(c)** a **gate that couldn't
> fail** — if the reference corpus holds no example of the shape you touched, the clean run proves
> *no-regression and nothing else* (real case: a detector firing on **0 of 190** documents: `fires=0` reads
> the same whether the code is right or completely broken); **(d)** a **canary that never applied the real
> perturbation** — the instrument can be sound while the experiment is wrong (synthetic test renamed
> containers / 4% churn → 100% recovery; real rebuild changed item IDs / 88% → <1% recovery): state what
> production does to the data; if the canary doesn't, the gate is unproven; **(e)** a **structural gate read
> as a semantic one** — presence/uniqueness/wiring ≠ correctness (real migration: clean structural bill while
> **56%** of carried-over names didn't describe the thing; a wrong label is worse than a missing one). When
> meaning matters, schedule the human read. Always state what each gate **can** and **cannot** show.

### A real example (see [`metodologia_en/REAL_EXAMPLE.md`](./ejemplos/metodologia_en/REAL_EXAMPLE.md))
Same sanitized case as in the Claude Code course; the orchestrating agent is **Cursor**. Bug: *"a field
shows up empty in the UI but it's in the PDF."* → Orient (`kg` skill finds a `SHARP_EDGE` that constrains
the fix) → confirm the empty value in the contract JSON (Playwright) → pre-existing, not a regression →
Serena+CodeGraph locate the end-of-provision detector, and a deterministic `_diag_pdf.py` reveals the
cause (overflow into a 2nd column) **without a single model call** → Plan mode approved by the human
→ RED test → fix keyed on the *structural property* (not on the client) → byte-identical regression (no-op
proof) + contract reproduced locally (via the *wrapper*) and **inside the deployed image** → document →
sanitize (`sanitise-diff` skill) → the human does the push. Bugbot spots a left-column case → the test
is added and it goes into the `PLAYBOOK`.

🗣️ *"The agent orchestrates and that's where the inference lives; the expensive part concentrates in plan/code/verify, not in searching."*

---

## 9. The method's tools

**Story:** The workflow says *what* to do; this section says **with which tool and in what order** — and
what each one does. In Cursor, the rule lives in `.cursor/rules/01-tool-prevalence.mdc`: "having MCP
installed" is not enough, the agent must reach for the right tool **automatically**. Detail:
[`metodologia_en/tools.md`](./ejemplos/metodologia_en/tools.md).

### The precedence: cheap → expensive, deterministic → probabilistic

Actual rule: *"for 'what is this / who depends on it / what do I touch', a `codegraph_explore`
**first** — source + call paths + blast radius + test-coverage flags in a single call
(treat the source it returns as ALREADY read, don't reopen it); Serena `find_referencing_symbols` for the
**precise** check before renaming/deleting (disambiguates by class); grep/Read only for literals."*

| Workflow stage | Tool |
|---|---|
| Orient (1) | **`kg`** skill (ticket graph — **graphify**, Part 3) · `STATUS.md`/ledgers · `git` · `gh` (no inference) |
| Navigate / investigate (4) | **CodeGraph** `codegraph_explore` (MCP) — source + paths + blast radius + coverage, in 1 call |
| Precise refactor-check (4-6) | **Serena** `find_referencing_symbols` (MCP) — disambiguates by class; **mandatory** before renaming/deleting |
| Diagnose (4) | **Deterministic oracle** (parser, validator, `_diag_*.py`) — no inference, reproducible |
| Environment: logs, config (4) | **AWS CLI** — a first-class debugging tool (read-only) |
| Output contract (2, 7) | **Playwright** (MCP) / F12 on the endpoint the consumer sees |
| Verify what's deployed (7) | **Docker** — repro inside the runtime image; green tests ≠ what gets shipped |
| Only at the end (7) | The **agent** call — to *verify* the fix, not to diagnose |

> **"No inference" ≠ "free".** These stages don't fire the **model call** (the expensive, non-deterministic
> resource), but the agent does read their output — a **smaller, targeted** cost, like a `grep`'s, not zero.
> The expensive reasoning is paid **once** when building the graph / the oracle and is **amortized** on every
> use (the ROI: no inference per query, deterministic and reproducible results, time and money saved).

### What each tool is (one sentence each)

- **CodeGraph** ([`ejemplos/codegraph/`](./ejemplos/codegraph/)) — a **local, no API keys**
  tree-sitter→SQLite index via MCP; one query (`codegraph_explore`) returns source + call paths
  + blast radius + **test-coverage flags** (58% fewer tool calls in its benchmarks). It is the
  **first** navigation tool; registered in `.cursor/mcp.json` (not with `claude mcp add`). Phases:
  **investigate/navigate**.
- **Serena** ([`ejemplos/serena/`](./ejemplos/serena/)) — **semantic navigation via LSP**
  (MCP): symbols, not text. `find_referencing_symbols` disambiguates same-named methods by class — the
  **precise** check that CodeGraph's flat `impact` doesn't give. Complementary, not rivals. Phases:
  **investigate → implement** (pre-rename/delete).
- **GSD** ([`ejemplos/gsd/`](./ejemplos/gsd/)) — the method **productized**, but it **only
  exists in Claude Code today**: a *discuss → plan → execute → verify* cycle with subagents
  (`gsd-planner`, `gsd-executor`, `gsd-verifier`…). **There is no official port to Cursor.** The practical
  equivalent here: **Plan mode** for the discuss→plan gate, the `methodology-plan` skill to fill the
  template before implementing, and `gsd-*` roles reused as Task/subagents with role prompts.
  **Honesty — this project does NOT use GSD:** it runs the 11-stage workflow + `data/changes/`, more refined and
  focused on per-ticket fixes on a service in production; GSD makes more sense in a multi-component
  *greenfield*.
- **Playwright** (MCP) — reproduces the symptom where the consumer sees it (phases **triage and outbound gate**).
- **Context7** (MCP) — up-to-date library docs, instead of the training cutoff (phase **investigate**).
- **Home-grown deterministic oracles** (`_diag_*.py`) — the cheap, reproducible answer before spending
  the agent call (phase **investigate**). **They are not skills or MCP tools:** they are **loose code** the
  agent types and runs with Shell, gitignored under `data/changes/<ticket>/` (unlike `kg`/Serena/CodeGraph,
  which are registered capabilities). Detail:
  [`metodologia_en/tools.md`](./ejemplos/metodologia_en/tools.md).

🗣️ *"The classic inversion — pulling the model in to diagnose — is exactly what this order avoids: the model verifies; the oracles diagnose."*

### Installation / smoke checklist (before the live demo)

The tools do **not “live” in `AGENTS.md`**: they live in `.cursor/mcp.json` + CLIs on PATH + skills in
`.cursor/skills/`. In a multi-repo workspace it is common that "there are no tools" because Cursor opened the
parent, CodeGraph's `--path` points at another machine, or a reload is missing after `npm i -g codegraph`.

Runbook for the agent (install, path pins, reload, 5 smoke tests):
[`docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md`](./docs/ai-agents-code-methodology/AGENT_SETUP_TOOLS.md)
· in the demo repo: `D:\repos3\ILS_2\document-parser-lambda\AGENT_SETUP_TOOLS.md`.

| # | Tool | Minimum smoke |
|---|---|---|
| 1 | CodeGraph | `codegraph explore "ExtractorBase"` or MCP `codegraph_explore` |
| 2 | Serena | `find_referencing_symbols` on a known method |
| 3 | Playwright | Open `https://example.com` and read the title |
| 4 | Context7 | Current docs for a lib (e.g. pytest fixtures) |
| 5 | kg | `bash data/knowledge-graph/kg_query.sh letter-end` / `kg` skill |

---

## 10. Transferring the methodology

**Story:** The proof that Part 2 is **agnostic** — and the most real example in the whole course: the
method was born with Claude Code and is **packaged and transferred to Cursor** in this very repository, and
also to GitHub Copilot elsewhere. Real material:
[`docs/ai-agents-code-methodology/`](./docs/ai-agents-code-methodology/) (adaptation guides, templates,
bootstrap).

### What travels unchanged (the 5 rules to preserve)
1. Plan → agreement → implement.
2. Verify against the **consumer-visible contract**, not internal functions.
3. Solve the **general class** of the problem, not one sample input.
4. Durable trail of decisions (why, what changed, how it was verified).
5. The human owns irreversible external actions (merge, deploy, communication).

### What DOES change: the surface
| Claude Code | Cursor |
|---|---|
| `CLAUDE.md` (+ `~/.claude` hierarchy, subfolders, `CLAUDE.local.md`) | `AGENTS.md` + `.cursor/rules/*.mdc` |
| Skills in `~/.claude/skills/` | `.cursor/skills/` — **same `SKILL.md`**, no translation |
| Hooks + `settings.local.json` (`exit 2`) | `.cursor/hooks.json` (JSON `permission`, `failClosed`) |
| Plan mode | Plan mode — same discipline, same name |
| Subagents / Agent Teams | `.cursor/agents/*.md` + built-ins — **no** Agent Teams; parallelism with Background/Cloud Agents |
| `claude -p` (headless) | `agent -p` (Cursor CLI print mode) |

### What gets re-mapped per repo
The **contract** (HTTP payload / DB row / event / artifact), the **tracker** (Jira/Azure
Boards/Issues), the **test pyramid**, the deployed **runtime** (container/VM/serverless), and the local
**sanitization** rules.

### The kit — [`CURSOR_ADAPTATION.md`](./docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md)
The full mapping (surface, 11 stages in Cursor, precedence, install, MCP, context, plan template,
governance, 14-day rollout, success criteria, honest gaps) + a ready-to-copy surface
in [`cursor/`](./docs/ai-agents-code-methodology/cursor/) (rules, `AGENTS.md.example`, `hooks.json.example`,
`mcp.json.example`, skills `kg`/`kg-refresh`/`methodology-plan`/`sanitise-diff`) + script
`bootstrap-cursor-repo.ps1` (rules/skills/MCP/hooks). The same pack includes
[`COPILOT_ADAPTATION.md`](./docs/ai-agents-code-methodology/COPILOT_ADAPTATION.md) — **this repo is not a
special case: the discipline reaches a third agent.**

**Fallback without a ticket graph** (80% of the value, minimal setup): newest-first `STATUS.md` + per-ticket
folders + lexical search by symptom + commit history as a lightweight graph substitute + a
"danger zones" section.

The operating model is the same gated workflow: load orientation → triage on the contract → deterministic probes
→ plan gate → TDD gate → outbound gate → handover. First-day checklist: fill in
`STATUS.md`, 3–5 initial invariants, define the contract, scoped test commands, and **one complete issue
with RED → GREEN + contract**.

🗣️ *"This same repo is the proof: methodology born in Claude Code, running in Cursor with CURSOR_ADAPTATION.md. Tools get replaced; the discipline travels."*

---

## 11. Machine synchronization

**Story:** The same principles of the methodology applied to **ops**: moving the workspace between the
main machine and the laptop with a real runbook (see
[`metodologia_en/machine-sync.md`](./ejemplos/metodologia_en/machine-sync.md)). The original runbook was born
in a **Claude Code** environment — the principles (asymmetric sync, agent with guardrails, evidence, human
owns the external) apply the same way in Cursor; what changes is the surface:

| Claude Code | Cursor |
|---|---|
| Pointer in `CLAUDE.md` | Pointer in `AGENTS.md` / on-demand rule |
| `~/.claude` bundle (skills + memory) | Skills in `.cursor/skills/` or `~/.cursor/skills/`; Cursor Memories **≠** `MEMORY.md` |
| `codegraph` MCP in `~/.claude.json` | Re-pin `--path` in `.cursor/mcp.json` on the laptop |
| Claude `/kg-refresh` skill | Cursor pack `kg-refresh` skill + same `kg_refresh.sh` scripts |

**Do not blindly copy a `~/.claude` tarball as "Cursor setup".** Bring `data/`, git repos, and reinstall
the `.cursor/` surface (methodology pack bootstrap).

- **Asymmetric synchronization:** outbound = **full copy** (one tarball: workspace + `~/.cursor`/`.aws`/
  `.ssh`, with `-h` to dereference symlinks, excluding venvs/node_modules); inbound = **delta only**
  (the code is already on GitHub → `git fetch`; only the gitignored docs in `data/`, a few MB, travel).
- **Copying to USB has real gotchas:** WSL does not auto-mount a USB plugged in after boot
  (`sudo mount -t drvfs F: /mnt/f`); and the copy is **verified byte by byte** (`stat -c %s` on source and
  destination match) before ejecting — evidence, not "looks like it fits". The bundle **grows**
  (~0.9→~1.5 GB); size the USB up.
- **Durable memory, on demand:** the runbook does **not** live in the always-loaded `AGENTS.md` — there is
  a one-line pointer; it loads only when you travel.
- **The landing is driven by an agent with guardrails:** the delta's `INSTRUCTIONS.md` is written *for an
  agent*; non-destructive only (rename, don't delete), `git fetch` is the only network op, backup+`diff` of
  `STATUS.md`, and **STOP and ask** if the main machine made its own edits. The human approves; the agent
  does no push/merge.
- **"Discover, don't assume":** the commands **derive** the workspace root (`ls -d /mnt/*/ILS`), they
  don't hardcode it, because paths differ per machine.
- **The tooling syncs too:** the `.codegraph/` index is **excluded** from the tarball (it's local, with
  absolute paths) and rebuilt at the destination; an idempotent `target-setup.sh` reinstalls the CodeGraph
  CLI, updates GSD only if it's behind, and **corrects the MCP `--path`** to the laptop's real root
  (in `.cursor/mcp.json`, not `~/.claude.json`).
- **Bring-up and memory, with idempotent subcommands:** on a new laptop, `kg_refresh.sh bootstrap`
  installs what doesn't go in the bundle and verifies the `kg` skill (and re-bootstraps `.cursor/` — MCP
  `--path`, skills — if that machine didn't have it); and since Cursor memory does **not** travel the same way as
  Claude Code's, decide explicitly what travels (`data/changes/`, snapshots) with `snapshot-memory` /
  `restore-memory` — do not assume IDE Memories sync on their own. A `LAPTOP_START_HERE.md` is
  the single entry point for the laptop's agent.

**And the next step: from *transporting* to *sharing* (S3).** The tarball solves moving the workspace
between **your** machines. It does not solve a **team** working off the same record. Add a third
machine and a second person and three costs appear: the record is gitignored → it **can't be linked**
from a ticket or a PR; moving degenerates into archiving everything; and each person ends up with
**their own private index** of the same history. Runbook:
[`docs/synchro/s3-sync/README.md`](./docs/synchro/s3-sync/README.md).

- **Deliberately narrow scope:** engineering docs + the graph only. **No** client documents, fixtures
  or binaries without the bucket owner's sign-off — it is both a confidentiality line and a size line,
  and widening later is easy while retracting is not.
- **Write via sync, read via a read-only mount.** Object storage has **no** locking and no atomic
  rename: a writable mount isn't a convenience, it's corruption you discover weeks later. Read-only is
  the safety property, not a limitation to work around.
- **The destructive direction is opt-in:** dry-run by default, explicit `--go`, and `--delete`
  separately — because the normal case is a teammate pushing at the same time, and an exact mirror
  from a stale view **erases their work**.
- **Docs are the source of truth; the graph is derived.** Per-ticket files almost never collide (people
  work on different tickets); the generated graph is the **only** real contention point → exactly **one**
  machine publishes it. "Rebuild locally" is only safe if the generated tree is *purely* derived.
- **"Derived" is per file, not per folder.** Hand-authored curated community names live inside the
  generated graph tree; a rebuild destroyed them (<1% survived). Classify per file: *source* /
  *derived* / *authored-inside-derived* — the third travels always.
- **Pairs must move together.** Stamp the names overlay with a **fingerprint of the graph** it was built
  against; a per-object sync can leave a new graph with old names and raise no error.
- **Coordinate without locks.** Contributors request a rebuild via a one-file-per-request queue
  (`kg_refresh.sh request` → `refresh_queue/<utc>-<machine>.request`). Single publisher is scaffolding,
  not architecture — the queue is the trigger contract a scheduled job can consume later.
- **The agent-specific part — the machine has a role.** This only shows up once the same record is
  reachable from several machines with different permissions, and it's the easiest thing to forget:
  the session has to know **where it is and what it may do** *before* acting. Otherwise a *contributor*
  machine will republish the shared graph — the one thing it must not do — and report it as a job well
  done. Each machine declares a name and a role, generates a **machine-local** `IDENTITY.md` with live
  checks, and `AGENTS.md` points at it: every session reads its own role first.

🗣️ *"The methodology isn't just for code: durable memory, guardrails, and 'the human owns external actions' — in ops too — and the runbook travels from Claude Code to Cursor the same way as the rest of the method."*

🗣️ *"And when the durable trail goes from one machine to a team, a new question appears that didn't
exist before: the agent has to know which machine it's on before it acts."*

---

# PART 3 — The ticket knowledge graph (graphify)

## 12. The ticket knowledge graph

**Story:** The same complete case as in the Claude Code volume, from idea to tooling in production. If
CodeGraph indexes the *code*, this graph indexes the **project's memory** — per-ticket writeups, "sharp
edges", runbooks, memory notes — and answers *"what broke before near here?"* in one call,
**with no LLM**. The technology that builds it is **graphify** (not CodeGraph — CodeGraph is only the
*analogy*: same role, different domain, different tool). The build pipeline was originally generated **in
Claude Code**; today query and refresh live as `kg`/`kg-refresh` skills — the **same `SKILL.md`**
works in Cursor and Claude Code without changing a line. All the real material is in
[`docs/knowledge-graph/`](./docs/knowledge-graph/): design, scripts, tests, manifest, and the real output
([`output/graph.html`](./docs/knowledge-graph/output/graph.html)).

### 12a. The problem and the design (see [`docs/knowledge-graph/design.md`](./docs/knowledge-graph/design.md))

In a repo with **~540 files** of writeups, a "new" bug almost always has prior context that constrains
the fix: an invariant, a ticket that fixed something similar, a documented regression. Finding it by hand
= remembering it exists + grep. The graph makes it **explicit and queryable**.

- **A curated corpus, not a glob:** a **diffable** [`manifest.txt`](./docs/knowledge-graph/manifest.txt)
  enumerates exactly what goes in (~116 files, ~196k words): `sst-*` writeups (with a deterministic
  fallback for folders without a primary doc), hubs (`STATUS`, `SHARP_EDGES`, `PLAYBOOK`…), extractor
  status, ops runbooks, and the agent's memory.
- **Hard exclusions:** binaries, handovers that repeat the ticket, repetitive QA and — critically — the
  **stale copies** from a travel tarball (`payload/`): including them would create duplicate/conflicting
  nodes. *Density without new knowledge = noise.*
- **Phase 1 was a spike with a decision at the end** (keep/extend/replace): validate whether off-the-shelf
  `graphify` was enough before investing in custom extraction. It was — and it stayed.

### 12b. The pipeline and the `kg` / `kg-refresh` skills

Two **skills** (`kg`, `kg-refresh` — in `.cursor/skills/` or `.claude/skills/`, same file) + two
deterministic **scripts** ([`kg_query.sh`](./docs/knowledge-graph/kg_query.sh),
[`kg_refresh.sh`](./docs/knowledge-graph/kg_refresh.sh)) + two corpus utilities (`build_manifest.py`,
`stage_corpus.py`) + **tests** (`test_kg_*.py`):

```
kg_refresh.sh prepare   # build_manifest -> stage _corpus/ (names with provenance:
                        #   sst-5468__sst-5468.md, hub__STATUS.md, memory__x.md)
                        #   -> copy to a SCRATCH OUTSIDE the repo
(semantic extraction)   # the only step with the agent (subagents in parallel): extraction
                        #   of nodes/edges + clustering -> HTML/JSON/report
kg_refresh.sh finalize  # copy artifacts to output/ + leak-check (nothing outside data/)
```

- **The gotcha that underpins it:** `graphify` respects `.gitignore` and all of `data/` is gitignored →
  running the detector in place finds **0 files**. That's why the corpus is staged in a scratch outside the repo.
- **Why `kg-refresh` is a skill and not a script:** the semantic step is an agent step; the
  bookends (`prepare`/`finalize`) are deterministic and tested.
- **Deliberate location:** the `SKILL.md` files live **at the user level** (`~/.cursor/skills/kg/`,
  `kg-refresh/` or their `~/.claude/skills/` equivalents), outside the repo — for confidentiality (nothing from the KG
  in committable paths) and for scope (available machine-wide). They travel between machines inside the
  agent configuration tarball (section 11).
- Extra subcommands for the between-machines trip: `bootstrap` (new laptop), `snapshot-memory` /
  `restore-memory` (memory doesn't travel in the delta — it's parked under `data/` and merged back).

### 12c. The real output (see [`output/GRAPH_REPORT.md`](./docs/knowledge-graph/output/GRAPH_REPORT.md) and the slide with the visualization)

The project's real graph (captured from `output/graph.html`, an interactive vis-network with search,
node panel, and community filter) — **the same artifact as in the Claude Code volume**: the graph
is agnostic of which agent built or queries it:

- **507 nodes · 672 edges · 35 communities** over 116 files (~196k words).
- **92% `EXTRACTED` edges** (literal quotes, reliable) · 7% `INFERRED` (semantic similarity,
  mean confidence 0.7 — leads to verify, not facts).
- The **communities map to real danger zones**: "Letter-End & Run-in Titles", "Title Detection
  Failures", "Comment-Memo Boundaries", "PDF Extractor Cascade"… — exactly the clusters a senior
  engineer holds in their head.
- The **god-nodes** (most connected nodes) are the project's structural tickets — the report's top-10 is
  a free onboarding list.
- The report includes **"surprising connections"**: pairs of semantically twin lessons no one had
  connected by hand.

### 12d. How it's used and where it hooks in

```bash
kg explain <ticket|topic>  # a node's neighbors   (graphify explain)  ← the most common use
kg path <A> <B>            # shortest path A<->B (graphify path)
kg find <substr>           # discover a node's exact name
kg-refresh                 # rebuild after new tickets (cheap, re-runnable)
```

Fuzzy matching: `SST-1234`, `get_letter_end`, `"letter-end"` all resolve. **Deterministic, no LLM in the
query**: `kg_query.sh` reads `output/graph.json` directly. Real example: for an end-of-letter fix,
`kg explain get_letter_end` instantly returns the full danger zone — the 5–6 tickets that share that code.

> **"No LLM in the query" is not "free" — it is a smaller, amortized cost.** The expensive inference (the
> extraction with subagents) is paid **once** in `kg-refresh`; each `kg` query is then a deterministic
> algorithm over `graph.json` → **zero inference**. The only cost is the agent reading a small output (like a
> `grep`): smaller and targeted, not zero. Building the graph is thus an **investment** that amortizes: no
> inference per query, **deterministic and reproducible** results (a better outcome), and time and money
> saved per task. 🗣️ *"The graph isn't an expense: reason once, retrieve a thousand times."*

**Where it hooks in:** at **stage 1 (Orient)** of the methodology — the *history-first* rule in
`.cursor/rules/00-methodology-core.mdc` says **run `kg <ticket|topic>` before grepping** in
`data/changes/`. The graph points to *what to read*, it doesn't replace it. And it is a **derived artifact**:
derived parts rebuild wherever the corpus is, but **hand-authored files inside that tree travel** (section 11) —
classify per file, not per folder. Confidentiality: the nodes carry internal names → the whole tree lives under
gitignored `data/`; sharing it externally would require a separate sanitization pass.

🗣️ *"One semantic step at build time, zero LLM at query time. The graph is the map; the agent, the guide — whichever editor you ask from."*

---

## 13. Closing

**Part 1 — the tool:** installing is trivial; the value is in **how** you use it. The layers:
**install (editor/CLI/cloud) → memory (AGENTS.md + rules) & Memories → context & caching → MCP →
skills/Marketplace → subagents → automation.** The context window is the budget; hooks and permissions
are the guarantees.

**Part 2 — the method:** a powerful agent without a method is fast chaos. The 11-stage workflow channels
the power through **deterministic gates** (and the outbound gate is **five checks**, because a green that
proves nothing is worse than a red); the tools (CodeGraph, Serena, the oracles) embody the
cheap→expensive precedence — with GSD as the **productized** version of the method, only in Claude Code today —;
the discipline **travels** — and this same repo is the direct proof: from Claude Code to Cursor, with
`CURSOR_ADAPTATION.md` —; and the durable trail goes from *transport* (tarball) to *sharing* (S3 +
per-machine identity).

**Part 3 — the ticket graph:** the complete case that joins the two parts — skills born in Claude Code
(Part 1) in service of the methodology's *history-first* step (Part 2), built with **graphify**:
507 nodes, 672 edges, 35 communities that map to real danger zones, queryable from **either
agent** with the same `SKILL.md`.

**The level-up:** from "chatting with an assistant in an editor" to **a system**: hooks that guarantee
quality, MCP that connects your world, subagents that scale the work, and a methodology that treats the
agent as a collaborator with evidence gates — and that does not depend on which editor you have open.

**References:** official documentation <https://docs.cursor.com> · GSD
<https://github.com/tomascortereal/claude-code-setup> · CodeGraph <https://colbymchenry.github.io/codegraph/> ·
Serena <https://github.com/oraios/serena>.
