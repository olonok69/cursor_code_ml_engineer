# Design — Ticket Knowledge Graph Phase 2, Step 1: Refresh wrapper

> **Date:** 2026-07-08. **Status:** design approved in chat (brainstorming) → pending spec review → plan.
> **Predecessor:** Phase 1 spike (`design.md` + `plan.md` + `_findings.md`) — verdict **KEEP**.
> This is Phase-2 candidate #1 from `_findings.md` "Verdict: KEEP → Phase 2".
> **Location rationale:** stays under gitignored `data/changes/knowledge-graph/` (client-name confidentiality),
> NOT the brainstorming skill's default `docs/superpowers/specs/`.

## 1. Goal

Make refreshing the knowledge graph a **repeatable two-command flow** (plus one Claude `/graphify` run) instead
of the current 8-line hand-copied recipe at the bottom of `_findings.md`. The graph goes stale as tickets land
(e.g. SST-5623/5357 shipped after the 2026-07-07 build); a low-friction refresh keeps it current and removes the
foot-guns (forgetting the `.gitignore`-scratch workaround, forgetting to sync the in-place `query` copy, leaking
an artifact outside `data/`).

## 2. Load-bearing constraint (why this isn't one autonomous script)

graphify's **Step 3 semantic extraction** (`~/.claude/skills/graphify/SKILL.md` L233–352) **mandates the Agent
tool** — it dispatches `general-purpose` subagents to read the docs and emit graph fragments, then merges them.
Our corpus is **100 % markdown** (no code → the AST path yields nothing), so LLM subagent extraction is
unavoidable and **inherently Claude-in-the-loop**. Community labelling (Step 5) likewise needs Claude.

**Consequence:** the deterministic *bookends* live in a bash script; the `/graphify` run in the middle is a
Claude step. A thin **`/kg-refresh` skill** (§4.3) wraps all three so the user types one command — the skill can
do the Claude-in-the-loop middle step that a pure bash script cannot. Shape:

```
kg_refresh.sh prepare   →   [Claude runs /graphify $SCRATCH/_corpus]   →   kg_refresh.sh finalize
                        └──────────────── all three orchestrated by /kg-refresh ─────────────────┘
```

The bash script remains the source of truth for the deterministic work (and the by-hand fallback); the skill is
only orchestration. Running the script's two subcommands manually with a hand-run `/graphify` between them stays
fully supported.

## 3. The second `.gitignore` gotcha the original recipe missed

graphify writes `graphify-out/` **relative to CWD**. The Phase-1 recipe ran `/graphify _corpus` from inside the
scratch dir, so `graphify-out/` landed in scratch, and copied only 3 artifacts to `output/`. But
`/graphify query` runs **in place** from `data/knowledge-graph/` and reads
`data/knowledge-graph/graphify-out/graph.json`. If a refresh updates `output/graph.json` but not the in-place
`graphify-out/graph.json`, **every subsequent `query` runs against the stale graph**. `finalize` MUST sync both.

## 4. Components

### 4.1 `data/knowledge-graph/kg_refresh.sh` (new)

A stdlib-only bash script (`set -euo pipefail`) with two subcommands. Repo root and KG dir derived from the
script's own path (`$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)`), so it runs from anywhere. Scratch dir
overridable via `KG_SCRATCH` env (default `~/.cache/ils-kg`).

**`kg_refresh.sh prepare`**
1. `python build_manifest.py` — regenerate `manifest.txt` from the *current* tree (picks up new tickets).
2. `python stage_corpus.py` — populate `_corpus/` with flat provenance names.
3. Guard: assert `_corpus/` is non-empty and contains no `payload`/`.png`/`.json`/`.docx` (belt-and-braces —
   `stage_corpus.py` already excludes these, but the wrapper re-checks so a script regression can't leak).
4. `rm -rf "$KG_SCRATCH" && mkdir -p "$KG_SCRATCH" && cp -r _corpus "$KG_SCRATCH/_corpus"` — stage into the
   **out-of-repo** scratch so graphify's `detect()` (which respects `.gitignore`) actually sees the files.
5. Print the exact next step for Claude, verbatim and copy-pasteable:
   `Next: run  /graphify $KG_SCRATCH/_corpus  then  kg_refresh.sh finalize`.

   Python is invoked via the repo venv if `VIRTUAL_ENV` is unset: prefer `.venv/bin/python`, else `.venv-1/bin/python`,
   else `python3`. (Manifest/stage scripts are stdlib-only, so any 3.12 works — but stay consistent with the repo.)

**`kg_refresh.sh finalize`**
6. Assert `$KG_SCRATCH/graphify-out/graph.json` exists (else: "run /graphify first" and exit non-zero).
7. Copy `graph.html`, `graph.json`, `GRAPH_REPORT.md` from `$KG_SCRATCH/graphify-out/` → `output/`.
8. **Also** copy `graph.json` (+ ensure `.graphify_python`) into `data/knowledge-graph/graphify-out/` so in-place
   `/graphify query` reflects the refresh (§3).
9. Leak check: `git -C <repo> status --porcelain | grep -v '^?? data/' | grep -i knowledge` must be empty →
   print `OK — contained in data/`, else fail loudly.
10. Print a one-line summary (node/edge/community counts parsed from `GRAPH_REPORT.md`, best-effort) + the
    `output/graph.html` path.

### 4.2 `data/knowledge-graph/test_kg_refresh.py` (new)

Pure-logic tests for the extraction-order-independent bits, mirroring the Phase-1 `test_kg_corpus.py` style
(`importlib` load, no network, no graphify). Because the script is bash, the testable pure logic is thin;
tests target the **guards** by shelling out to the script in a `tmp` sandbox with a fake repo layout:
- `prepare` refuses to proceed if staging produced a `payload`-named or `.json`/`.png`/`.docx` file in `_corpus/`.
- `finalize` refuses (non-zero exit) when `$KG_SCRATCH/graphify-out/graph.json` is absent.
- `finalize` writes `graph.json` to **both** `output/` and `graphify-out/` (the §3 regression guard).

Scratch/`KG_SCRATCH` pointed at a `tmp_path` subdir in tests so nothing touches `~/.cache` or the real corpus.

### 4.3 `~/.claude/skills/kg-refresh/SKILL.md` (new, user-level)

A thin orchestration skill (trigger `/kg-refresh`) so the whole refresh is one command. **User-level**
(`~/.claude/skills/`, alongside `graphify`/`gsd-graphify`) — keeps the KG entirely out of the repo, consistent
with the local-only stance; it simply no-ops in other repos where `kg_refresh.sh` doesn't exist. Contains **no
client names** (pure orchestration). Steps it instructs Claude to run:

1. Resolve `KG=<repo>/data/knowledge-graph`. If `kg_refresh.sh` isn't found there, tell the user this repo has no
   knowledge graph and stop. (Repo located by looking for `data/knowledge-graph/kg_refresh.sh` from CWD upward.)
2. `bash "$KG/kg_refresh.sh" prepare` — capture the printed `$KG_SCRATCH` path.
3. Invoke the **`/graphify`** skill (via the Skill tool) on `$KG_SCRATCH/_corpus` — this reuses graphify's own
   detect → subagent-extract → cluster → label → HTML pipeline unchanged (DRY; we do not re-implement it).
4. `bash "$KG/kg_refresh.sh" finalize`.
5. Report: node/edge/community counts from `GRAPH_REPORT.md`, the `output/graph.html` path, and — nice-to-have —
   any `sst-*` nodes now present that weren't in the prior `output/graph.json` (surfaces "what this refresh added").

The skill is orchestration only: all file movement, guards, and leak checks stay in `kg_refresh.sh` so they're
testable and identical whether run via the skill or by hand.

### 4.4 Docs

- Update `_findings.md`'s "How to reproduce / refresh" block to point at `kg_refresh.sh` (keep the raw recipe
  as a fallback/appendix).
- Update the `project_ticket_knowledge_graph` memory: refresh recipe → `kg_refresh.sh prepare|finalize`; note
  the in-place-`graphify-out` sync fix.

## 5. Data flow

```
current data/changes tree + memory
    │  build_manifest.py
    ▼
manifest.txt ──stage_corpus.py──▶ _corpus/ (flat names)
    │  cp -r  (dodges .gitignore)
    ▼
$KG_SCRATCH/_corpus/ ──[Claude: /graphify]──▶ $KG_SCRATCH/graphify-out/{graph.html,graph.json,GRAPH_REPORT.md}
    │  finalize: copy back
    ├──▶ data/knowledge-graph/output/{graph.html,graph.json,GRAPH_REPORT.md}   (the deliverable)
    └──▶ data/knowledge-graph/graphify-out/graph.json                          (keeps /graphify query fresh)
```

## 6. Error handling

- `set -euo pipefail`; every external step's failure aborts with a clear message.
- Unknown/missing subcommand → usage string, exit 2.
- `prepare` guard trips (leak-shaped file in `_corpus/`) → abort before touching scratch.
- `finalize` before a graphify run → detected via missing `graph.json`, exit non-zero with the fix instruction.
- Leak check failing in `finalize` → abort; the artifacts already in `data/` are fine, but surface the stray path.

## 7. Testing

- `python -m pytest data/knowledge-graph/test_kg_refresh.py -v` — the three guard tests above, all offline.
- Existing `test_kg_corpus.py` stays green (manifest/stage unchanged in behaviour).
- **End-to-end** (manual, once) via the skill: run `/kg-refresh`; confirm it ran prepare → /graphify → finalize,
  `output/` refreshed, `graphify-out/graph.json` updated, leak check `OK`, and a
  `/graphify query "letter-end danger zone"` returns the expected tickets against the NEW graph (should now also
  surface SST-5623). The by-hand path (`prepare` → manual `/graphify` → `finalize`) is the same script, so the
  guard tests cover both.
- The `/kg-refresh` skill is orchestration-only (no branching logic of its own) → validated by the E2E run, not
  a unit test.

## 8. Out of scope (this step)

- Incremental `--update` (deferred — full rebuild of ~90 tiny files is cheap and robust; revisit if cost grows).
- Query-during-work surface (Phase-2 step 2), sanitised external share (step 3), LLM edge-typing (step 4).
- Any change to `build_manifest.py` / `stage_corpus.py` logic — they are reused as-is. (The manifest count will
  simply grow as new `sst-*` folders exist; no code change needed.)

## 9. Self-review

- **Placeholders:** none; scratch default, venv resolution, and the copy targets are all concrete.
- **Consistency:** §3 gotcha ↔ §4.1 step 8 ↔ §4.2 regression test ↔ §5 second arrow — all reference the same
  in-place `graphify-out/graph.json` sync.
- **Scope:** single script + one test file + two doc updates → one implementation plan. Focused.
- **Ambiguity:** "full rebuild" (not `--update`) and scratch `~/.cache/ils-kg` are pinned per the approved
  brainstorming decisions.
