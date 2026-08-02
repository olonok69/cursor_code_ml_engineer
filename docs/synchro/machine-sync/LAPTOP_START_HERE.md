# ▶ LAPTOP START HERE — bring-up + continue working the same as on main

**You are the laptop-side Claude agent.** You've been handed the travel bundle (a full copy of the
`/mnt/d/ILS` workspace + `~/.claude`). This doc is your entry point: (A) finish setup from scratch,
(B) work exactly the way the main-machine agent does, (C) send an increment back when the trip ends.
It is gitignored (under `data/`) — machine/ops content, never ships to the remote.

> Detailed procedures live in siblings; this doc is the **orchestrator** (the exact command order).
> - OS/tooling restore: `data/machine-sync/RUNBOOK.md`
> - KG-specific travel: `data/changes/knowledge-graph/TRAVEL_SYNC.md`
> - Inbound delta pattern: `data/ils-to-main/INSTRUCTIONS.md`

---

## A. From-scratch setup on this laptop (nothing was here before)

The bundle already carries the workspace, `~/.claude` (skills + memory + CLAUDE.md), `.aws`, `.ssh`.
Do these in order — every step is idempotent and safe to re-run.

1. **Restore the bundle** — `RUNBOOK.md` §"Step 3" (extract the tarball to the workspace root +
   `~/.claude .aws .ssh`). Park any existing workspace first (rename, never delete).
2. **Per-repo runtimes** — `RUNBOOK.md` §"Step 4": for each repo you'll run,
   `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`; `npm install`
   in `frontend`. Extractor runs also need `tesseract` + `libreoffice` on PATH.
3. **AWS CLI** — `RUNBOOK.md` §"Step 4b" (the config travels; the binary doesn't — install + `aws sso login`).
4. **CodeGraph + GSD** — `RUNBOOK.md` §"Step 4c": `bash data/machine-sync/target-setup.sh` (installs the
   `codegraph` CLI, fixes the MCP `--path` to this laptop's repo, rebuilds the index).
5. **Ticket knowledge graph (the /kg workflow)** — one command:
   ```bash
   bash <WS>/document-parser-lambda/data/knowledge-graph/kg_refresh.sh bootstrap
   ```
   It installs `graphifyy` into an interpreter, pins `graphify-out/.graphify_python`, and smoke-tests
   `/kg SST-5623`. (The built graph itself already came in the bundle under
   `data/knowledge-graph/output/` — no rebuild needed to start querying.)
6. **Restart Claude Code**, then confirm you're whole:
   ```bash
   cd <WS>/document-parser-lambda
   git log --oneline -3                                   # main's commits present
   bash data/knowledge-graph/kg_query.sh SST-5623         # /kg works (deterministic)
   codegraph status                                       # code index up to date
   # a bare  codegraph_explore "get_letter_end"  resolves in a session (no projectPath)
   ```

**Interpreter-marker gotcha:** if this laptop's username / miniconda path differs from main, the pinned
`data/knowledge-graph/graphify-out/.graphify_python` may point at a path that doesn't exist. `kg_refresh.sh
bootstrap` re-pins it; or just delete that one-line file and the `/graphify` skill re-resolves.

---

## B. Work exactly the same as on main

Everything that makes the main-machine agent behave the way it does travelled in `~/.claude` and the repo.
Nothing to reconfigure — just **use it**:

- **Read the rules first.** `~/.claude/CLAUDE.md` (global working rules + auto-use integrations) and
  `<WS>/document-parser-lambda/CLAUDE.md` (repo orientation, mandatory working rules, conventions,
  sharp edges). These are the contract. The repo CLAUDE.md is gitignored/local — it came in the bundle.
- **Skills are auto-discovered** from `~/.claude/skills/`: `/kg`, `/kg-refresh`, `/graphify`, GSD, the
  superpowers set, etc. Same names, same behaviour as main.
- **History-first on every fix:** run **`/kg <ticket-or-topic>`** *before* grepping `data/changes/` — it
  surfaces the related tickets + danger-zone cluster to read (CLAUDE.md rule #2). Then read the ticket
  doc under `data/changes/<ticket>/` and the SHARP_EDGES entry.
- **The ledger + history** are all present: `data/changes/STATUS.md` (in-flight state), `data/changes/<ticket>/`
  (per-ticket writeups), `~/.claude/projects/-mnt-d-ILS/memory/*.md` (cross-session memory). Update STATUS.md
  and the per-ticket doc as part of "done", exactly as on main.
- **Non-negotiable working rules** (full list in the repo CLAUDE.md): plan → agree → TDD; zero-regression
  (`pytest -q` at the current count + canonical ASF/Webster battery for DOC/PDF); **Claude does NOT
  push/commit/PR or touch GitHub — Cursor does**; **no client names / ticket IDs / AI attribution in
  committed code or PR text** (everything confidential stays under gitignored `data/`); branch off
  `origin/development`, squash-merge.
- **When you write a memory note** (`~/.claude/projects/-mnt-d-ILS/memory/`), remember it will NOT ride the
  inbound delta by itself — you snapshot it in step C. Add the one-line pointer in `MEMORY.md` as usual.

---

## C. Send the increment back to main (laptop → main) — DELTA ONLY

Never full-copy back (you'd clobber whatever main did). Send only what changed. On the laptop, when the
trip ends:

1. **Code** → commit + push as normal PR branches. Main picks them up read-only with `git fetch origin`.
   (Cursor handles the actual push per the working rules; you author + write handover docs.)
2. **Snapshot your memory edits** (they are excluded from the delta otherwise):
   ```bash
   bash <WS>/document-parser-lambda/data/knowledge-graph/kg_refresh.sh snapshot-memory
   ```
   → copies `~/.claude/.../memory/*.md` into `data/knowledge-graph/_memory_snapshot/` (under `data/`, so it
   rides the delta).
3. **Build the delta tarball** (repo-relative, per `data/ils-to-main/INSTRUCTIONS.md`):
   ```bash
   cd <WS>/document-parser-lambda
   tar -czf ~/ils-delta-$(date +%Y%m%d).tar.gz \
     data/changes/<new-or-changed-ticket-dirs> \
     data/knowledge-graph/_memory_snapshot \
     data/<other-changed-paths>
   ```
   Write a short `INSTRUCTIONS.md` + `MANIFEST.txt` beside it (copy the shape of `data/ils-to-main/`),
   noting the STATUS.md-reconciliation step.

### On MAIN, landing the delta (for the main-machine agent)
1. `git fetch origin` (code is already on GitHub).
2. Extract the delta over `data/` **non-destructively** (back up `data/changes/STATUS.md` first, diff,
   reconcile — see `data/ils-to-main/INSTRUCTIONS.md`).
3. **Fold the travelled memory back in:**
   ```bash
   bash data/knowledge-graph/kg_refresh.sh restore-memory   # merges _memory_snapshot -> ~/.claude memory, backs up
   ```
4. **Rebuild the graph** with the travelled tickets + memory:
   ```bash
   /kg-refresh
   ```
5. **Verify:** `/kg <a-ticket-you-worked-while-travelling>` returns it; the finalize leak-check is clean.
   Then delete the consumed transport snapshot: `rm -rf data/knowledge-graph/_memory_snapshot`.

---

## The model in one line

**Outbound = full copy (everything travels, `bootstrap` on arrival). Inbound = increment only (code via
git, ticket docs + memory-snapshot via a small `data/` tarball, then `restore-memory` + `/kg-refresh` on
main).** The graph is a *derived* artifact — it never travels back; whichever machine holds the current
corpus rebuilds it.
