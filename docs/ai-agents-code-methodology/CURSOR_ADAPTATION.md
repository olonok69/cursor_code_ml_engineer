# Adapting the AI-agent methodology for Cursor

> Purpose: take the methodology from [`README.md`](README.md) / [`TECHNICAL.md`](TECHNICAL.md)
> and run it end-to-end in **Cursor**, with the same tool *roles* you use in Claude Code
> (CodeGraph, Serena, Playwright, graphify/`/kg`, deterministic oracles).
>
> Companion pack (copy-ready rules, skills, MCP, hooks): [`cursor/`](cursor/).
> Parallel guide for GitHub Copilot: [`COPILOT_ADAPTATION.md`](COPILOT_ADAPTATION.md).

---

## 1) What transfers unchanged

These are stack-independent and should remain strict:

1. Plan -> agree -> implement.
2. Verify via the consumer-visible output contract, not internal functions.
3. Solve the general class of issue, not one sample input.
4. Keep a durable decision trail (why, what changed, how verified).
5. Human owns irreversible external actions (merge, deploy, stakeholder comms).
6. **Canary the instrument before believing it** — a filter/lock/scan that returns "nothing" or "ok" without a known-answer check is not evidence (success and total failure look identical when silence is the correct behaviour; a negative result must not share an output with a failed measurement).
7. **Read the machine/session role before writing shared state** — once the trail is shared, a contributor session that republishes the derived index is the one failure mode the single-publisher rule exists to prevent. Point `AGENTS.md` / always-on rules at a machine-local `IDENTITY.md`.

If you keep only five rules, keep **1–5**. Add **6–7** as soon as you share a durable trail across machines or people.

---

## 2) Claude Code → Cursor surface map

| Role in the methodology | Claude Code | Cursor |
|---|---|---|
| Always-loaded orientation | `CLAUDE.md` (+ lean pointers) | `.cursor/rules/*.mdc` with `alwaysApply: true` and/or `AGENTS.md` |
| On-demand detail | `data/changes/**` | Same path — do not move detail into always-on rules |
| Tool prevalence (auto-select) | Rules in `CLAUDE.md` + MCP allowlist | Rules in `.cursor/rules/` + MCP enabled in `.cursor/mcp.json` |
| Slash skills (`/kg`, `/kg-refresh`) | `~/.claude/skills/` | Project skills: `.cursor/skills/<name>/SKILL.md` (or personal `~/.cursor/skills/`) |
| Hard gates (block push, etc.) | Hooks + `settings.local.json` allowlist | `.cursor/hooks.json` + `beforeShellExecution` / `beforeMCPExecution` |
| Plan gate | Plan mode | Cursor **Plan** mode — same discipline: no production code until agreed |
| Parallel exploration | Subagents / Agent Teams | Cursor **Task** / subagents (`explore`, `generalPurpose`, …) |
| Persistent memory | `~/.claude` memory corpus | Lean snapshot in `data/changes/` + optional Cursor memories; **write-once** still applies |
| Headless / CI compose | `claude -p` | Cursor SDK / Automations when needed — not required for the daily 11-step loop |
| External git/PR | Often delegated *to* Cursor | If Cursor *is* the agent: **rules + hooks** enforce “prepare, don’t push unless asked” |

Tools are fungible; discipline is not. CodeGraph / Serena / Playwright / graphify fill the same
roles as in the Claude Code setup — they speak MCP in both products.

---

## 3) The 11 stages in Cursor

| # | Stage | Cursor practice | Preferred tools |
|---|---|---|---|
| 1 | Orient | Session start: load rules → read `STATUS.md` → query ticket index → `git`/`gh` live state | Skill `kg` / `kg_query` · ledgers · Shell |
| 2 | Inbound triage | Reproduce symptom at **output contract** before any edit | Playwright MCP · browser · contract fixture |
| 3 | Provenance | Repro on pre-change baseline; classify regression vs pre-existing | Shell + git · same contract harness |
| 4 | Investigate | Cheap deterministic oracle before expensive model diagnosis | CodeGraph → Serena → `_diag_*.py` / parser |
| 5 | Plan | Switch to **Plan** mode; present options; get explicit agreement | Plan mode · write plan into issue note |
| 6 | Implement | Agent mode; TDD RED → GREEN; minimal diff | Editor tools · pytest / local test runner |
| 7 | Verify | Unit + scoped + full suite; outbound gate ×5 (canary instrument · contract via last writer · member list not totals · shipping artifact · look at output) | Tests · Playwright · Docker |
| 8 | Document | Write-once: issue note, STATUS pointer, QA, handover | Templates under `data/changes/` |
| 9 | Sanitise | Scan **added** staged lines for names/IDs/secrets/attribution | Skill `sanitise-diff` · hook optional |
| 10 | Hand off | Prepare branch + handover; **do not** push/PR/deploy unless human explicitly asks | Rules + `block-external-git` hook |
| 11 | Review + persist | Triage bot findings; update FOLLOWUPS / PLAYBOOK; refresh ticket graph | `gh` · skill `kg-refresh` |

Cost concentration stays the same as in [`ejemplos/metodologia/WORKFLOW.md`](../../ejemplos/metodologia/WORKFLOW.md):
cheap fact-finding in 1–4 and 9; expensive inference in 5–7.

---

## 4) Tool prevalence (same order as Claude Code)

Golden rule — encode this in an always-applied Cursor rule:

> For “what is this / who depends / what breaks”, call **CodeGraph `codegraph_explore` first**
> (treat returned source as already read). Use **Serena `find_referencing_symbols`** before
> rename/delete. Use grep/Read only for literals. For history-first orientation, query the
> ticket graph (`kg` skill / `kg_query`) before grepping `data/changes/`.

| Need | Tool | Stage |
|---|---|---|
| Related prior tickets / danger zone | `kg` skill → graphify index (or STATUS fallback) | 1 |
| Survey symbol + callers + blast radius + test coverage | CodeGraph `codegraph_explore` | 4 |
| Precise refs before rename/delete | Serena `find_referencing_symbols` | 4–6 |
| Consumer-visible contract | Playwright MCP / F12 | 2, 7 |
| Deployed runtime parity | Docker (same image as prod) | 7 |
| Root cause without LLM diagnosis | `_diag_*.py` / parser / schema check | 4 |
| Live library docs | Context7 MCP | 4 |
| Branch / PR state | `git`, `gh` | 1, 10–11 |

### No-knowledge-graph fallback

If graphify/`/kg` is not set up yet, use the same fallback as Copilot:

1. `data/changes/STATUS.md` newest-first + per-issue folders.
2. Lexical search by symptom / contract fields / symbols.
3. Commit/PR history by file overlap.
4. Short `SHARP_EDGES.md` danger-zone list.

That recovers ~80% of graph value with minimal setup. See also
[`COPILOT_ADAPTATION.md`](COPILOT_ADAPTATION.md) §3.

---

## 5) Fast path — install the Cursor pack (30–60 minutes)

From a target repository root (after copying this methodology folder to
`data/changes/ai-agent-methodology`):

```powershell
# 1) Ledger templates (shared with Copilot path)
Rename-Item data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1.txt bootstrap-new-repo.ps1 -ErrorAction SilentlyContinue
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-new-repo.ps1

# 2) Cursor surface (rules, skills, MCP example, hooks)
Rename-Item data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1.txt bootstrap-cursor-repo.ps1 -ErrorAction SilentlyContinue
pwsh data/changes/ai-agent-methodology/scripts/bootstrap-cursor-repo.ps1
```

Then:

1. Edit `.cursor/mcp.json` — set CodeGraph `--path` to **this** repo’s absolute path; enable Serena / Playwright / Context7 as needed.
2. Index code: `codegraph init` (and add `.codegraph/` to `.gitignore`).
3. Fill `data/changes/STATUS.md` + 3–5 `SHARP_EDGES.md` entries + output contract in orientation / rules.
4. Fill `templates/CURSOR_WORKING_AGREEMENT_TEMPLATE.md` (or the copy under `data/changes/`) with the team.
5. Restart Cursor (MCP config changes require reload).
6. Run **one** issue fully: Plan → RED → GREEN → contract outbound → sanitise → human push.

Detailed file list: [`cursor/README.md`](cursor/README.md).

---

## 6) MCP setup notes (Cursor-specific)

Cursor project MCP typically lives at **`.cursor/mcp.json`** (see `cursor/mcp.json.example`).

1. **CodeGraph** — prefer `codegraph serve --path <repo> --mcp` so `projectPath` is not required every call.
   Rebuild the index after large edits (`codegraph sync`). Do not commit `.codegraph/`.
2. **Serena** — same `uvx … serena start-mcp-server` pattern as Claude Code; activate the project if multi-root.
3. **Playwright** — `@playwright/mcp` for contract reproduction in the UI / status endpoint.
4. **Context7** — optional; use instead of training-cutoff guesses for external libs.
5. **Secrets** — never hardcode tokens; use env vars in the MCP `env` block.
6. After editing MCP config: **reload the Cursor window**.

Permission model differs from Claude’s hand-curated allowlist: Cursor prompts or auto-runs based on
user settings. Compensate with:

- lean always-applied **rules** (what to call, in what order),
- **hooks** that block irreversible shell (push/deploy),
- human approval on Plan and on external actions.

---

## 7) Context architecture in Cursor

Same lean-core discipline as [`TECHNICAL.md`](TECHNICAL.md) §6:

| Layer | What lives there | Cursor artifact |
|---|---|---|
| Always-loaded (small) | Architecture pointers, locked decisions, working gates, tool order | `.cursor/rules/*` `alwaysApply: true` — keep each rule focused and short |
| Live snapshot | In-flight work index | `data/changes/STATUS.md` |
| On-demand | Per-ticket writeups, playbooks, full policy | `data/changes/<id>/`, `PLAYBOOK.md`, … |
| Skills (loaded when relevant) | `/kg`-style procedures, sanitise, plan checklist | `.cursor/skills/*/SKILL.md` |

**Anti-pattern:** pasting the full STATUS changelog into an always-applied rule. Pay that token tax forever.
Write each record once; rules carry **pointers**.

---

## 8) Planning template (issue start)

Use this exact template when starting work (also in Copilot adaptation — keep one voice):

```text
Issue: <tracker-id> - <short title>

1) Contract confirmation
- Consumer-visible contract: <API/UI/event/artifact>
- Symptom reproduced there: <yes/no + evidence source>

2) Provenance
- Reproduced on pre-change baseline: <yes/no>
- Classification: <regression | pre-existing>

3) Root cause hypothesis
- Deterministic probe used: <probe>
- Result: <what proved the hypothesis>

4) Fix shape (general-case)
- Structural class addressed: <class>
- Why not instance-specific: <one sentence>

5) Verification plan
- RED test: <test id>
- Scoped suite: <command>
- Regression suite: <command>
- Contract output repro: <command/path>
- Runtime parity check: <where and how>

6) Handover outputs
- Change summary doc
- Acceptance criteria
- Open follow-ups
```

Run stages 1–4 and fill this **in Plan mode** before switching to Agent for implementation.

---

## 9) Governance policy (minimum)

Define once; keep in the working agreement + rules:

1. No merge/deploy/customer comms by the agent unless the human explicitly requests that action in-session.
2. No secrets or forbidden identifiers in committed artifacts.
3. No “fixed” claim without command-level evidence.
4. No silent dismissal of automated-review findings.
5. No prompt/rule/MCP changes that weaken gates without explicit acknowledgement.
6. Sanitise **added** staged lines before handoff every time.

---

## 10) Folder structure (target repo)

```text
.cursor/
  mcp.json                 # project MCP (from mcp.json.example)
  rules/
    00-methodology-core.mdc
    01-tool-prevalence.mdc
    02-gates-and-handoff.mdc
  skills/
    kg/SKILL.md
    kg-refresh/SKILL.md
    methodology-plan/SKILL.md
    sanitise-diff/SKILL.md
  hooks.json               # optional hard gates
  hooks/
    block-external-git.ps1
data/
  changes/
    STATUS.md
    FOLLOWUPS.md
    SHARP_EDGES.md
    ai-agent-methodology/   # this pack
    <issue-id>/
      <issue-id>.md
      _handover.md
      qa_acceptance_criteria.md
AGENTS.md                   # optional one-page pointer to rules + data/changes
```

Keep `data/` gitignored if your org policy matches the original setup; methodology *templates*
can stay in-repo for sharing.

---

## 11) 14-day rollout (Cursor)

### Days 1–2: Baseline

1. Bootstrap ledgers + Cursor pack.
2. Wire MCP (CodeGraph path, Serena, Playwright).
3. Define contract + 3–5 sharp edges.
4. Agree working agreement with the team.

### Days 3–5: First controlled ticket

1. Full 11-stage run on one real issue.
2. Enforce Plan gate + RED → GREEN + outbound contract.
3. Prove sanitise + human-owned push.

### Days 6–10: Stabilize

1. Add `kg` / graphify **or** harden STATUS fallback.
2. Tune hooks (block push/deploy) if the agent overreaches.
3. Measure reopen rate and time-to-verified-contract.

### Days 11–14: Harden

1. Port any remaining Claude skills you rely on.
2. Automate sanitise scan in a hook or CI.
3. Publish a one-page “how we run Cursor here” (link rules + agreement).

---

## 12) Success criteria

Same KPIs as Copilot adaptation:

1. Reopened defects per merged fix.
2. Time from first repro to verified contract fix.
3. % of fixes with explicit RED → GREEN trace.
4. % of handovers with actionable acceptance criteria.
5. Number of “pre-existing, not regression” findings proven early.

If reopen rate drops and verification quality rises, the methodology transferred correctly.

---

## 13) Honest gaps vs Claude Code

| Capability | Status in Cursor pack |
|---|---|
| 11 gates + durable trail | Full parity |
| CodeGraph / Serena / Playwright roles | Full parity (MCP) |
| Plan → agree → implement | Full parity (Plan mode) |
| Ticket graph query during orient | Parity if you port scripts + `kg` skill; else STATUS fallback |
| graphify refresh orchestration | Scripts portable; LLM extract step may still be run from Claude or adapted |
| Bit-identical Agent Teams / GSD plugin | Not required; use Cursor Task subagents where useful |
| `claude -p` Unix pipes | Use Cursor SDK/Automations only if you need headless compose |
| `~/.claude` memory tarball sync | Remap to your Cursor + `data/changes` sync story |

Aim for **methodology parity**, not product-clone parity.

---

## 14) Direct answer

Yes — this methodology is usable in Cursor at production quality.

1. Knowledge graph helps; it is not required on day one.
2. MCP tools map 1:1 in role and nearly 1:1 in config.
3. Rules + skills + hooks replace `CLAUDE.md` + Claude skills + allowlist.
4. The invariant gates stay the real source of quality.

Start with [`START_HERE.md`](START_HERE.md) (Cursor path) and [`cursor/README.md`](cursor/README.md).
