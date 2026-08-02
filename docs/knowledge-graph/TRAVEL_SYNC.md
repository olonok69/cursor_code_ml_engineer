# Ticket KG — travel sync (main ⇄ laptop)

> **Status: BUILT + tested (2026-07-09).** The memory-gap fix and from-scratch bootstrap are implemented as
> `kg_refresh.sh` subcommands (`snapshot-memory` / `restore-memory` / `bootstrap`; guard tests in
> `test_kg_refresh.py`). The single hand-to-the-laptop-agent entry point is
> **`data/machine-sync/LAPTOP_START_HERE.md`** — read that first; this doc is the KG-specific design rationale.
> Plugs into `data/machine-sync/RUNBOOK.md` (outbound = full copy, inbound = delta) + `data/ils-to-main/INSTRUCTIONS.md`.
> Related: [[project_ticket_knowledge_graph]] memory; design/plan `phase2-refresh-{design,plan}.md`.

## TL;DR

- **Outbound (main → laptop): nothing extra to do.** The full-copy tarball already carries `~/.claude`
  (`tar -C /home/$USER .claude …`, RUNBOOK L60) → the **built graph** (`data/knowledge-graph/output/*`), the
  **scripts** (`kg_refresh.sh`, `build_manifest.py`, `stage_corpus.py`), the **`/kg-refresh` + `/graphify`
  skills** (`~/.claude/skills/`), and the **memory corpus** (`~/.claude/projects/-mnt-d-ILS/memory/*.md`) all
  come across. On the laptop the graph is immediately usable — no rebuild needed.
- **Inbound (laptop → main): rebuild, don't ship the graph.** The graph is a *derived* artifact — never carry
  `graph.html/json` back. Bring back only the **source markdown you changed** (ticket docs travel in the delta
  automatically; **memory files do NOT — see the gap below**), then run **`/kg-refresh`** on main. Your
  instinct — "take the increment from the laptop and refresh the KB" — is exactly right, modulo the memory gap.

## Why the graph is a derived artifact (the load-bearing idea)

The graph is a pure function of the corpus (96 curated markdown files) + the `/graphify` extraction. So it never
needs to travel *back*: whatever machine has the current corpus can rebuild it in ~5 subagents. This keeps the
travel payload tiny (source markdown only) and avoids merge-conflicting two built graphs.

## Outbound — main → laptop (before you travel)

The RUNBOOK's full copy does the heavy lifting. KG-specific checklist on the **laptop** after arrival:

1. **One-command bring-up:** `bash data/knowledge-graph/kg_refresh.sh bootstrap` — installs `graphifyy`
   into an interpreter, (re-)pins `graphify-out/.graphify_python`, and smoke-tests `/kg SST-5623`. Handles the
   from-scratch case (graphify not installed) and the interpreter-path-differs case in one idempotent pass.
2. **(what bootstrap fixes for you)** The interpreter marker `graphify-out/.graphify_python` on main pins
   `/home/olonok/miniconda3/bin/python3`; if the laptop's username / miniconda path differs, `bootstrap`
   re-pins it (or delete that one-line file and the `/graphify` skill re-resolves).
3. **Use it read-only:** open `data/knowledge-graph/output/graph.html`, or
   `cd data/knowledge-graph && /graphify query "…"`. No rebuild required — the graph is current as shipped.
4. **Only if you want to rebuild on the laptop** (e.g. you worked tickets there and want a fresh graph before
   coming home): run `/kg-refresh`. Not necessary — main will rebuild on return anyway.

## Inbound — laptop → main (when you get home)

1. **Ticket docs travel automatically.** New/changed `data/changes/sst-*/` come back in the delta `data/`
   tarball (per `ils-to-main/INSTRUCTIONS.md`) → already in the corpus manifest on next build.
2. **MEMORY — now handled by two subcommands (was the manual gap).** `ils-to-main/INSTRUCTIONS.md` L116
   excludes `~/.claude` memory from the delta, so memory edits don't travel by themselves. Fix:
   - **On the laptop, before building the delta:** `bash data/knowledge-graph/kg_refresh.sh snapshot-memory`
     → copies `~/.claude/.../memory/*.md` into `data/knowledge-graph/_memory_snapshot/` (under `data/`, so it
     rides the delta tarball). Include that dir in the tar.
   - **On main, after extracting the delta:** `bash data/knowledge-graph/kg_refresh.sh restore-memory`
     → merges the snapshot back into `~/.claude/.../memory/` (adds new files, overwrites changed ones **after
     backing up main's prior version** into `_memory_snapshot/.main_memory_bak_<ts>/`; identical files = no-op).
     `~/.claude/.../memory` stays the single source of truth; the snapshot is pure transport, delete after.
3. **Rebuild on main:** `/kg-refresh`. Picks up the travelled tickets (+ restored memory) → current graph.
4. **Verify:** `git -C … status` leak check is `OK` (finalize enforces); a `/kg <ticket>` for a ticket you
   worked while travelling returns it. Then `rm -rf data/knowledge-graph/_memory_snapshot`.

## Open questions (to decide on return)

1. **How should laptop memory changes come back? — RESOLVED 2026-07-09, built as a variant of (c).**
   `kg_refresh.sh snapshot-memory` parks `memory/*.md` under `data/knowledge-graph/_memory_snapshot/` (rides the
   delta); `kg_refresh.sh restore-memory` folds it back into `~/.claude/.../memory` on arrival. Chosen over the
   originally-sketched "build_manifest.py prefers the snapshot" because a **transport-then-restore** model keeps
   `~/.claude/.../memory` the single source of truth (no stale snapshot silently overriding future edits) and is
   non-destructive (backs up any overwritten file). No edit to the shared travel procedure; guard tests cover
   add / update+backup / no-op / nothing-to-restore.
2. **Ship the built graph outbound, or rebuild on the laptop?** Recommendation: **ship it** (already happens via
   full copy) — instant use, and you rarely need a laptop rebuild.
3. **A `/kg-refresh --check` that reports staleness** (corpus changed since last build?) so you know whether a
   rebuild is worth the tokens — nice-to-have, not required.

## What plugs where (summary table)

| Direction | Carries the graph? | Carries scripts+skills? | Carries ticket docs? | Carries memory? | Action on arrival |
|---|---|---|---|---|---|
| **Out (main→laptop)** | ✅ full copy | ✅ full copy | ✅ full copy | ✅ full copy (`~/.claude`) | `kg_refresh.sh bootstrap`; then use read-only |
| **In (laptop→main)** | ❌ (rebuild) | n/a (already on main) | ✅ delta tarball | ✅ via `snapshot-memory` → `_memory_snapshot/` in delta | `restore-memory` → `/kg-refresh` |
