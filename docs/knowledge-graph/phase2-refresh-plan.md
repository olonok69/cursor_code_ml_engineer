# Ticket KG Phase 2 Step 1 — Refresh wrapper + /kg-refresh skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the hand-run KG refresh recipe into a repeatable `kg_refresh.sh prepare|finalize` script (deterministic bookends) plus a user-level `/kg-refresh` skill that orchestrates `prepare → /graphify → finalize` as one command.

**Architecture:** graphify's semantic extraction is subagent-driven (Claude-in-the-loop), so a pure shell script can only automate the bookends. `kg_refresh.sh` does the deterministic, testable work (manifest → stage → out-of-repo scratch; then copy artifacts back + sync the in-place query copy + leak-check). The `/kg-refresh` skill wraps the two subcommands around a `/graphify` call it invokes itself.

**Tech Stack:** Bash (`set -euo pipefail`, stdlib only), Python 3.12 for the existing `build_manifest.py`/`stage_corpus.py` (reused unchanged) and for pytest guard tests, the installed `graphify` skill.

## Global Constraints

- **Everything under `data/knowledge-graph/` is gitignored — NOTHING is committed.** No `git add/commit` steps; each task ends with a **verify** checkpoint. (The `/kg-refresh` SKILL.md lives at user-level `~/.claude/skills/`, also outside the repo.) Client names must never leave `data/`.
- **Reuse `build_manifest.py` and `stage_corpus.py` as-is** — do not change their logic. The manifest count simply grows as new `sst-*` folders exist.
- **Scratch dir:** out-of-repo, default `~/.cache/ils-kg`, overridable via `KG_SCRATCH`. Required because graphify's `detect()` respects `.gitignore` and all of `data/` is gitignored → in-place detect finds 0 files.
- **`finalize` MUST write `graph.json` to BOTH `output/` AND the in-place `graphify-out/`** — `/graphify query` reads the in-place copy; skipping it leaves queries stale after a refresh.
- **Repo root + KG dir are derived from the script's own path** (`BASH_SOURCE`), so the script runs from any CWD.
- Rebuild strategy is **full rebuild** (not graphify `--update`).
- Run Python via the repo venv when present: prefer `.venv/bin/python`, else `.venv-1/bin/python`, else `python3`.

---

### Task 1: `kg_refresh.sh prepare` + its guard test

**Files:**
- Create: `data/knowledge-graph/kg_refresh.sh`
- Test: `data/knowledge-graph/test_kg_refresh.py` (created here; extended in Task 2)

**Interfaces:**
- Produces: an executable `kg_refresh.sh` whose first arg is a subcommand. `prepare` regenerates `manifest.txt` + `_corpus/`, guards against leak-shaped files, stages `_corpus/` into `$KG_SCRATCH/_corpus`, and prints the next-step line `Next: run  /graphify $KG_SCRATCH/_corpus  then  bash <path>/kg_refresh.sh finalize`.
- Consumes: `build_manifest.py`, `stage_corpus.py` (existing, unchanged).

- [ ] **Step 1: Write the failing test**

```python
# data/knowledge-graph/test_kg_refresh.py
"""Offline guard tests for kg_refresh.sh. No network, no graphify."""
import os, shutil, subprocess
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE / "kg_refresh.sh"


def _run(subcmd, scratch, extra_env=None):
    env = dict(os.environ, KG_SCRATCH=str(scratch))
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(_SCRIPT), subcmd],
        capture_output=True, text=True, env=env,
    )


def test_prepare_stages_corpus_into_scratch(tmp_path):
    scratch = tmp_path / "scratch"
    r = _run("prepare", scratch)
    assert r.returncode == 0, r.stderr
    staged = scratch / "_corpus"
    assert staged.is_dir()
    files = list(staged.iterdir())
    assert len(files) > 50, f"expected the real ~90-file corpus, got {len(files)}"
    # leak-shape guard: no forbidden extensions / payload names slipped through
    assert not [p for p in files if p.suffix in {".png", ".json", ".docx"}]
    assert not [p for p in files if "payload" in p.name]


def test_unknown_subcommand_errors(tmp_path):
    r = _run("frobnicate", tmp_path / "s")
    assert r.returncode == 2
    assert "usage" in (r.stdout + r.stderr).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/ILS/document-parser-lambda && source .venv/bin/activate && python -m pytest data/knowledge-graph/test_kg_refresh.py -v`
Expected: FAIL — `kg_refresh.sh` does not exist (bash exits non-zero / "No such file").

- [ ] **Step 3: Write minimal implementation**

```bash
#!/usr/bin/env bash
# data/knowledge-graph/kg_refresh.sh
# Repeatable refresh of the ticket knowledge graph. Deterministic bookends only;
# the /graphify semantic-extraction step in the middle is a Claude step (subagents).
set -euo pipefail

KG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$KG_DIR/../.." && pwd)"
SCRATCH="${KG_SCRATCH:-$HOME/.cache/ils-kg}"
CORPUS="$KG_DIR/_corpus"

# --- resolve python: prefer repo venv, else python3 -------------------------
pick_python() {
  if [ -n "${VIRTUAL_ENV:-}" ]; then echo "python"; return; fi
  for p in "$REPO/.venv/bin/python" "$REPO/.venv-1/bin/python"; do
    [ -x "$p" ] && { echo "$p"; return; }
  done
  echo "python3"
}
PY="$(pick_python)"

usage() {
  cat >&2 <<EOF
usage: kg_refresh.sh {prepare|finalize}
  prepare   build manifest -> stage _corpus/ -> copy to \$KG_SCRATCH ($SCRATCH)
            then run:  /graphify \$KG_SCRATCH/_corpus
  finalize  copy graphify-out artifacts back into data/knowledge-graph/ + leak-check
EOF
  exit 2
}

cmd_prepare() {
  cd "$KG_DIR"
  "$PY" build_manifest.py
  "$PY" stage_corpus.py
  # belt-and-braces leak guard on the staged corpus (stage_corpus already excludes these)
  local bad
  bad="$(find "$CORPUS" -maxdepth 1 \( -name '*.png' -o -name '*.json' -o -name '*.docx' -o -name '*payload*' \) -print)"
  if [ -n "$bad" ]; then
    echo "ABORT: leak-shaped file(s) staged into _corpus/:" >&2
    echo "$bad" >&2
    exit 1
  fi
  rm -rf "$SCRATCH"
  mkdir -p "$SCRATCH"
  cp -r "$CORPUS" "$SCRATCH/_corpus"
  local n
  n="$(find "$SCRATCH/_corpus" -maxdepth 1 -type f | wc -l | tr -d ' ')"
  echo "prepared: $n files staged -> $SCRATCH/_corpus"
  echo "Next: run  /graphify $SCRATCH/_corpus  then  bash $KG_DIR/kg_refresh.sh finalize"
}

main() {
  [ $# -ge 1 ] || usage
  case "$1" in
    prepare)  cmd_prepare ;;
    finalize) cmd_finalize ;;   # defined in Task 2
    *)        usage ;;
  esac
}
main "$@"
```

Note: `cmd_finalize` is referenced but not yet defined — Task 2 adds it. To keep Task 1 runnable, add a temporary stub directly below `cmd_prepare` for now:

```bash
cmd_finalize() { echo "finalize: not yet implemented" >&2; exit 3; }
```

Then make it executable:

```bash
chmod +x data/knowledge-graph/kg_refresh.sh
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest data/knowledge-graph/test_kg_refresh.py -v`
Expected: PASS (2 tests). `test_prepare_stages_corpus_into_scratch` builds the real corpus into a `tmp_path` scratch; `test_unknown_subcommand_errors` gets exit 2 + usage.

- [ ] **Step 5: Verify no leak + real run**

Run:
```bash
cd /mnt/d/ILS/document-parser-lambda
KG_SCRATCH=~/.cache/ils-kg bash data/knowledge-graph/kg_refresh.sh prepare
ls ~/.cache/ils-kg/_corpus | wc -l                                  # ~90
ls ~/.cache/ils-kg/_corpus | grep -Ec 'payload|\.png$|\.json$|\.docx$'   # 0
git status --porcelain | grep -v '^?? data/' | grep -i knowledge && echo "LEAK" || echo "OK"
```
Expected: ~90 files, `0`, `OK`. (No commit — gitignored.)

---

### Task 2: `kg_refresh.sh finalize` (copy-back + in-place sync + leak-check)

**Files:**
- Modify: `data/knowledge-graph/kg_refresh.sh` (replace the `cmd_finalize` stub)
- Modify: `data/knowledge-graph/test_kg_refresh.py` (add finalize guard tests)

**Interfaces:**
- Consumes: `$KG_SCRATCH/graphify-out/{graph.html,graph.json,GRAPH_REPORT.md}` (produced by the `/graphify` run).
- Produces: refreshed `data/knowledge-graph/output/{graph.html,graph.json,GRAPH_REPORT.md}` AND an updated in-place `data/knowledge-graph/graphify-out/graph.json` (so `/graphify query` reads the new graph). Exits non-zero if the `/graphify` run hasn't happened (missing `graph.json`).

- [ ] **Step 1: Write the failing tests** (append to `test_kg_refresh.py`)

```python
def _fake_graphify_out(scratch):
    """Simulate what /graphify leaves behind, so finalize can be tested offline."""
    out = scratch / "graphify-out"
    out.mkdir(parents=True)
    (out / "graph.json").write_text('{"nodes":[],"links":[]}')
    (out / "graph.html").write_text("<html>graph</html>")
    (out / "GRAPH_REPORT.md").write_text("# Report\n\nGraph: 5 nodes, 4 edges, 2 communities\n")
    return out


def test_finalize_without_graphify_run_errors(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    r = _run("finalize", scratch)
    assert r.returncode != 0
    assert "graph.json" in (r.stdout + r.stderr)


def test_finalize_syncs_both_output_and_inplace(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    _fake_graphify_out(scratch)
    r = _run("finalize", scratch)
    assert r.returncode == 0, r.stderr
    kg = _HERE
    # deliverable in output/
    assert (kg / "output" / "graph.json").read_text() == '{"nodes":[],"links":[]}'
    assert (kg / "output" / "graph.html").exists()
    assert (kg / "output" / "GRAPH_REPORT.md").exists()
    # in-place copy for /graphify query MUST also be updated (the §3 regression guard)
    assert (kg / "graphify-out" / "graph.json").read_text() == '{"nodes":[],"links":[]}'
```

> **Test-safety note:** these two tests write into the REAL `data/knowledge-graph/output/` and `graphify-out/`. Before running, the executor snapshots those two `graph.json` files and restores them after (a pytest fixture), OR runs the suite knowing the very next real `/kg-refresh` overwrites them anyway. Simplest: add an autouse fixture that backs up `output/graph.json` + `graphify-out/graph.json` to `tmp_path` and restores on teardown. Include it:

```python
import pytest

@pytest.fixture(autouse=True)
def _preserve_real_artifacts(tmp_path_factory):
    kg = _HERE
    saves = {}
    for rel in ("output/graph.json", "graphify-out/graph.json",
                "output/graph.html", "output/GRAPH_REPORT.md"):
        p = kg / rel
        if p.exists():
            b = tmp_path_factory.mktemp("bak") / p.name
            shutil.copy2(p, b); saves[p] = b
    yield
    for p, b in saves.items():
        shutil.copy2(b, p)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest data/knowledge-graph/test_kg_refresh.py -v`
Expected: `test_finalize_without_graphify_run_errors` — currently the stub exits 3 with no "graph.json" in output → FAIL on the message assert. `test_finalize_syncs_both_output_and_inplace` — stub exits 3 → FAIL.

- [ ] **Step 3: Replace the `cmd_finalize` stub with the real implementation**

Delete the stub line `cmd_finalize() { echo "finalize: not yet implemented" >&2; exit 3; }` and add:

```bash
cmd_finalize() {
  local gout="$SCRATCH/graphify-out"
  if [ ! -f "$gout/graph.json" ]; then
    echo "ABORT: $gout/graph.json not found." >&2
    echo "Run  /graphify $SCRATCH/_corpus  before finalize (did prepare run?)." >&2
    exit 1
  fi
  mkdir -p "$KG_DIR/output" "$KG_DIR/graphify-out"
  # deliverable trio -> output/
  cp "$gout/graph.html"      "$KG_DIR/output/graph.html"
  cp "$gout/graph.json"      "$KG_DIR/output/graph.json"
  cp "$gout/GRAPH_REPORT.md" "$KG_DIR/output/GRAPH_REPORT.md"
  # in-place graph.json keeps /graphify query fresh (reads data/knowledge-graph/graphify-out/)
  cp "$gout/graph.json" "$KG_DIR/graphify-out/graph.json"
  # ensure the interpreter marker exists for in-place query
  if [ ! -f "$KG_DIR/graphify-out/.graphify_python" ] && [ -f "$gout/.graphify_python" ]; then
    cp "$gout/.graphify_python" "$KG_DIR/graphify-out/.graphify_python"
  fi
  # leak check: nothing knowledge-graph landed outside data/
  if git -C "$REPO" status --porcelain 2>/dev/null | grep -v '^?? data/' | grep -qi knowledge; then
    echo "ABORT: a knowledge-graph artifact landed OUTSIDE data/ — investigate:" >&2
    git -C "$REPO" status --porcelain | grep -v '^?? data/' | grep -i knowledge >&2
    exit 1
  fi
  local summary
  summary="$(grep -m1 -E 'Graph: .*nodes' "$KG_DIR/output/GRAPH_REPORT.md" || true)"
  echo "finalized -> $KG_DIR/output/  (${summary:-report copied})"
  echo "Open: $KG_DIR/output/graph.html"
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest data/knowledge-graph/test_kg_refresh.py -v`
Expected: PASS (4 tests). The autouse fixture restores the real `output/`/`graphify-out/` `graph.json` afterward.

- [ ] **Step 5: Verify the full script surface**

Run:
```bash
cd /mnt/d/ILS/document-parser-lambda
bash data/knowledge-graph/kg_refresh.sh            # no arg -> usage, exit 2
bash data/knowledge-graph/kg_refresh.sh finalize   # before a run -> ABORT missing graph.json, exit 1
echo "exit: $?"
```
Expected: usage text then, for the second call, the "graph.json not found" abort with exit 1. (No commit — gitignored.)

---

### Task 3: `/kg-refresh` orchestration skill (user-level)

**Files:**
- Create: `~/.claude/skills/kg-refresh/SKILL.md`

**Interfaces:**
- Consumes: `kg_refresh.sh` (Tasks 1–2) + the installed `/graphify` skill.
- Produces: a `/kg-refresh` slash command that runs `prepare → /graphify $KG_SCRATCH/_corpus → finalize` and reports.

- [ ] **Step 1: Write the skill file**

```markdown
---
name: kg-refresh
description: Rebuild the document-parser-lambda ticket knowledge graph — runs the deterministic prepare/finalize bookends around a /graphify semantic-extraction pass. Use when tickets have landed and the KG under data/knowledge-graph/ is stale.
trigger: /kg-refresh
---

# /kg-refresh

Refresh the internal ticket/lessons knowledge graph in one command. The KG lives under the gitignored
`data/knowledge-graph/` of the `document-parser-lambda` repo. Full design: that folder's
`../changes/knowledge-graph/phase2-refresh-design.md`.

## What this does

`kg_refresh.sh prepare` (manifest → stage → out-of-repo scratch, dodging the `.gitignore`-detect gotcha)
→ `/graphify` on the scratch corpus (detect → subagent extraction → cluster → label → HTML)
→ `kg_refresh.sh finalize` (copy artifacts to `output/`, sync the in-place `graphify-out/graph.json` so
`/graphify query` stays fresh, leak-check that nothing escaped `data/`).

## Steps — do these in order, do not skip

### Step 1 — locate the script
From the current working directory, find the repo by walking up for `data/knowledge-graph/kg_refresh.sh`:

\`\`\`bash
KG=""
d="$PWD"
while [ "$d" != "/" ]; do
  if [ -f "$d/data/knowledge-graph/kg_refresh.sh" ]; then KG="$d/data/knowledge-graph"; break; fi
  d="$(dirname "$d")"
done
if [ -z "$KG" ]; then echo "No knowledge graph in this repo (data/knowledge-graph/kg_refresh.sh not found)."; fi
echo "KG=$KG"
\`\`\`

If `KG` is empty, tell the user this repo has no knowledge graph and STOP.

### Step 2 — prepare
Run `bash "$KG/kg_refresh.sh" prepare`. Read the printed `Next: run /graphify <path>` line and capture the
scratch corpus path (`$KG_SCRATCH/_corpus`, default `~/.cache/ils-kg/_corpus`).

### Step 3 — graphify
Invoke the **graphify** skill (Skill tool, name `graphify`) with that scratch corpus path as its argument, e.g.
`/graphify ~/.cache/ils-kg/_corpus`. Let it run its full pipeline unchanged — including dispatching
`general-purpose` extraction subagents (this is why /kg-refresh is a skill, not a shell script). Do NOT
re-implement graphify's steps here.

### Step 4 — finalize
Run `bash "$KG/kg_refresh.sh" finalize`. If it aborts saying `graph.json` is missing, the graphify run in
Step 3 didn't complete — fix that and re-run finalize.

### Step 5 — report
Tell the user:
- node / edge / community counts (from the `Graph: … nodes` line finalize echoed, or `output/GRAPH_REPORT.md`)
- the path `<KG>/output/graph.html`
- (best-effort) any `sst-*` node labels present in the new `output/graph.json` that weren't in the prior graph —
  i.e. what this refresh added. Skip if you don't have the prior graph handy.

## Notes
- Everything stays under gitignored `data/` (client names in node labels → internal only). Never move artifacts
  outside `data/`; finalize's leak-check enforces this.
- Full rebuild each run (not `--update`). Scratch is auto-wiped by `prepare`.
- To just QUERY the existing graph without refreshing: `cd <KG> && /graphify query "…"`.
```

- [ ] **Step 2: Verify the skill is discoverable**

Run:
```bash
ls ~/.claude/skills/kg-refresh/SKILL.md
head -5 ~/.claude/skills/kg-refresh/SKILL.md
```
Expected: file exists; frontmatter shows `name: kg-refresh` + `trigger: /kg-refresh`. (Skill discovery refreshes on the next session / skill re-scan; no commit — it's user-level, outside the repo.)

- [ ] **Step 3: End-to-end dry check of Steps 1–2 of the skill**

Run the skill's Step 1 locator + Step 2 prepare manually to confirm the wiring:
```bash
cd /mnt/d/ILS/document-parser-lambda
d="$PWD"; while [ "$d" != "/" ]; do [ -f "$d/data/knowledge-graph/kg_refresh.sh" ] && { echo "$d/data/knowledge-graph"; break; }; d="$(dirname "$d")"; done
bash data/knowledge-graph/kg_refresh.sh prepare
```
Expected: prints the KG path, then `prepared: ~90 files …` + the `Next: run /graphify …` line. (The actual `/graphify` + `finalize` are exercised in Task 4.)

---

### Task 4: First real refresh + doc/memory updates

**Files:**
- Modify: `data/knowledge-graph/_findings.md` (point refresh section at `kg_refresh.sh` / `/kg-refresh`)
- Modify: `~/.claude/projects/-mnt-d-ILS/memory/project_ticket_knowledge_graph.md` (new refresh recipe + in-place-sync fix)
- Generated (not committed): refreshed `data/knowledge-graph/output/*` + `graphify-out/graph.json`

**Interfaces:**
- Consumes: the full flow from Tasks 1–3.

- [ ] **Step 1: Run the real end-to-end refresh**

Preferred (via skill): invoke `/kg-refresh`.
Fallback (by hand, same script):
```bash
cd /mnt/d/ILS/document-parser-lambda && source .venv/bin/activate
bash data/knowledge-graph/kg_refresh.sh prepare
# then, as a Claude step:
/graphify ~/.cache/ils-kg/_corpus
bash data/knowledge-graph/kg_refresh.sh finalize
```
Expected: `finalize` prints a `Graph: N nodes, M edges, K communities` summary and `output/graph.html`. Node count ≥ the prior 231 (SST-5623/5357 + any memory/STATUS growth since 2026-07-07).

- [ ] **Step 2: Verify the refresh landed + query hits the NEW graph**

Run:
```bash
cd /mnt/d/ILS/document-parser-lambda/data/knowledge-graph
ls -la output/graph.html output/graph.json output/GRAPH_REPORT.md graphify-out/graph.json   # all mtimes "now"
git -C /mnt/d/ILS/document-parser-lambda status --porcelain | grep -v '^?? data/' | grep -i knowledge && echo "LEAK" || echo "OK"
cd /mnt/d/ILS/document-parser-lambda/data/knowledge-graph && /graphify query "soft body letter end truncation"
```
Expected: fresh mtimes on all four; `OK`; the query surfaces **SST-5623** (proves the in-place `graphify-out/graph.json` sync worked — this ticket did not exist in the 2026-07-07 graph).

- [ ] **Step 3: Update `_findings.md` refresh section**

Replace the "How to reproduce / refresh" fenced block near the bottom of `data/knowledge-graph/_findings.md` so it leads with the new flow and keeps the raw recipe as a fallback:

```markdown
## How to refresh
One command (recommended): **`/kg-refresh`** — runs prepare → /graphify → finalize, syncs the in-place query
copy, and leak-checks. See `../changes/knowledge-graph/phase2-refresh-design.md`.

By hand (same script):
​```bash
cd /mnt/d/ILS/document-parser-lambda && source .venv/bin/activate
bash data/knowledge-graph/kg_refresh.sh prepare      # manifest -> _corpus/ -> ~/.cache/ils-kg
/graphify ~/.cache/ils-kg/_corpus                    # Claude step (subagent extraction)
bash data/knowledge-graph/kg_refresh.sh finalize     # copy back + sync graphify-out/graph.json + leak-check
​```
Open `data/knowledge-graph/output/graph.html`. (The pre-2026-07-08 8-line manual recipe is superseded; the
key fix is that finalize now also refreshes the in-place `graphify-out/graph.json` that `/graphify query` reads.)
```

- [ ] **Step 4: Update the project memory**

In `~/.claude/projects/-mnt-d-ILS/memory/project_ticket_knowledge_graph.md`, replace the "**Refresh recipe (until wrapper exists):**" paragraph with:

```markdown
**Refresh (wrapper EXISTS as of 2026-07-08):** `/kg-refresh` skill (user-level `~/.claude/skills/kg-refresh/`)
orchestrates `kg_refresh.sh prepare` → `/graphify ~/.cache/ils-kg/_corpus` → `kg_refresh.sh finalize`. The script
lives at `data/knowledge-graph/kg_refresh.sh`; guards + leak-check + the in-place `graphify-out/graph.json` sync
(so `/graphify query` isn't left stale) all live in it. Full rebuild each run; scratch `~/.cache/ils-kg`
(override `KG_SCRATCH`). Design/plan: `data/changes/knowledge-graph/phase2-refresh-{design,plan}.md`. Remaining
Phase-2 steps: query-during-work surface, sanitised external share, LLM edge-typing.
```

- [ ] **Step 5: Final verification checkpoint**

Run:
```bash
cd /mnt/d/ILS/document-parser-lambda && source .venv/bin/activate
python -m pytest data/knowledge-graph/test_kg_corpus.py data/knowledge-graph/test_kg_refresh.py -v
git status --porcelain | grep -v '^?? data/' | grep -iE 'knowledge|kg_refresh' && echo "LEAK" || echo "OK — nothing outside data/"
```
Expected: all tests green (Phase-1 corpus tests + the 4 new refresh guard tests); `OK — nothing outside data/`. (No commit — everything is gitignored / user-level.)

---

## Self-Review

**Spec coverage:**
- §1 goal (repeatable two-command + skill) → Tasks 1–3. ✓
- §2 constraint (subagent extraction ⇒ skill not pure script) → Task 3 skill Step 3 + plan Architecture. ✓
- §3 in-place `graphify-out/graph.json` sync (the recipe bug) → Task 2 `cmd_finalize` cp + `test_finalize_syncs_both_output_and_inplace` + Task 4 Step 2 query-hits-new-graph proof. ✓
- §4.1 script prepare/finalize (scratch, venv resolution, guards, leak-check) → Tasks 1–2. ✓
- §4.2 three guard tests → Task 1 (`prepare` leak-shape) + Task 2 (`finalize` missing-json, both-targets). ✓ (The `prepare` leak-shape guard is exercised by `test_prepare_stages_corpus_into_scratch`'s forbidden-extension assert on the staged corpus.)
- §4.3 user-level `/kg-refresh` skill → Task 3. ✓
- §4.4 docs (`_findings.md` + memory) → Task 4 Steps 3–4. ✓
- §5 data flow (both copy-back arrows) → Task 2. ✓
- §6 error handling (usage/exit2, guard abort, missing-json abort, leak abort) → Task 1 usage + Task 2 aborts. ✓
- §7 testing (offline guards + manual E2E) → Tasks 1–2 tests + Task 4 Step 1–2. ✓
- §8 out-of-scope (no `--update`, no other Phase-2 steps, no manifest/stage edits) → respected; Task 4 memory note lists remaining steps. ✓

**Placeholder scan:** No TBD/TODO. The one forward reference (`cmd_finalize` in Task 1) is handled with an explicit runnable stub, replaced in Task 2. All bash + python shown in full. ✓

**Type/name consistency:** `KG_SCRATCH`/`SCRATCH`, `cmd_prepare`/`cmd_finalize`, `$KG_DIR/output`, `$KG_DIR/graphify-out`, `$SCRATCH/graphify-out` used identically across script, tests, and skill. The `_run(subcmd, scratch)` test helper and the `_preserve_real_artifacts` fixture are defined once and reused. ✓
