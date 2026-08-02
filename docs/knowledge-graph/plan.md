# Ticket Knowledge Graph (Phase 1: graphify spike) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a curated, reproducible markdown corpus of the ticket/lessons knowledge and run `graphify` over it to produce an internal-only knowledge graph, then judge whether off-the-shelf graphify is good enough (keep / extend / replace).

**Architecture:** Two small deterministic Python scripts — a **manifest builder** (enumerate the ~103 curated files per design §2) and a **stager** (copy them into a flat `_corpus/` with provenance-preserving names) — then invoke the `graphify` skill on `_corpus/`. All artifacts live under gitignored `data/knowledge-graph/`.

**Tech Stack:** Python 3.12 (repo `.venv`), the `graphify` skill. No new dependencies.

## Global Constraints

- **Everything under `data/knowledge-graph/` (gitignored). Nothing is committed** — so there are NO `git add/commit` steps; each task ends with a **verify** checkpoint instead. Client names must never leave `data/`.
- **Corpus = the manifest in design §2** (`data/changes/knowledge-graph/design.md`): per-ticket `sst-NNNN.md` (50) + largest-`.md` fallback for the 15 folders lacking one + 4 extractor `process.md` + 6 hubs + `CLAUDE.md` + `CODE_NAVIGATION.md` + 2 ops runbooks + 24 memory files ≈ **103**.
- **HARD EXCLUDE** any path containing `payload/` (stale workspace copy) and all `.png` / `.json` / `.docx`. The fallback picker also excludes `_handover_to_cursor.md`, `qa_acceptance_criteria.md`, `_diag_*.md`.
- Scripts are self-contained (stdlib only); tests live at `data/knowledge-graph/test_kg_corpus.py` (gitignored).
- Run all Python via the repo venv: `source .venv/bin/activate` (or `.venv-1`).

---

### Task 1: Manifest builder

**Files:**
- Create: `data/knowledge-graph/build_manifest.py`
- Test: `data/knowledge-graph/test_kg_corpus.py` (created here; extended in Task 2)

**Interfaces:**
- Produces: `collect() -> list[pathlib.Path]`, `largest_md(folder: Path) -> Path | None`, `is_excluded_path(p: Path) -> bool`; writing `data/knowledge-graph/manifest.txt` (one absolute path per line).

- [ ] **Step 1: Write the failing test** (pure-logic: fallback picker + exclusion guard)

```python
# data/knowledge-graph/test_kg_corpus.py
import importlib.util, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
def _load(mod):
    spec = importlib.util.spec_from_file_location(mod, _HERE / f"{mod}.py")
    m = importlib.util.module_from_spec(spec); sys.modules[mod] = m
    spec.loader.exec_module(m); return m

def test_largest_md_skips_operational(tmp_path):
    bm = _load("build_manifest")
    (tmp_path / "sst-9999.md").write_text("x" * 10)          # small primary-style
    (tmp_path / "_handover_to_cursor.md").write_text("y" * 999)  # big but excluded
    (tmp_path / "qa_acceptance_criteria.md").write_text("z" * 999)
    (tmp_path / "_diag_probe.md").write_text("d" * 999)
    (tmp_path / "notes.md").write_text("n" * 50)             # eligible, bigger than sst
    assert bm.largest_md(tmp_path).name == "notes.md"

def test_is_excluded_path_rejects_payload():
    bm = _load("build_manifest")
    assert bm.is_excluded_path(Path("/r/data/ils-to-main/payload/data/changes/STATUS.md"))
    assert not bm.is_excluded_path(Path("/r/data/changes/STATUS.md"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/d/ILS/document-parser-lambda && source .venv/bin/activate && python -m pytest data/knowledge-graph/test_kg_corpus.py -v`
Expected: FAIL — `build_manifest.py` does not exist (import error).

- [ ] **Step 3: Write minimal implementation**

```python
# data/knowledge-graph/build_manifest.py
"""Enumerate the curated knowledge-graph corpus into manifest.txt (design §2)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # data/knowledge-graph/ -> repo root
CHANGES = REPO / "data" / "changes"
MEMORY = Path.home() / ".claude" / "projects" / "-mnt-d-ILS" / "memory"

FALLBACK_EXCLUDE = ("_handover_to_cursor.md", "qa_acceptance_criteria.md")

def is_excluded_path(p: Path) -> bool:
    return "payload" in p.parts

def largest_md(folder: Path) -> Path | None:
    cands = [p for p in folder.glob("*.md")
             if p.name not in FALLBACK_EXCLUDE and not p.name.startswith("_diag_")]
    return max(cands, key=lambda p: p.stat().st_size) if cands else None

def collect() -> list[Path]:
    paths: list[Path] = []
    for folder in sorted(CHANGES.glob("sst-*")):
        if not folder.is_dir():
            continue
        primary = folder / f"{folder.name}.md"
        paths.append(primary if primary.exists() else largest_md(folder))
    for name in ("comment_memo", "doc", "pdf", "table"):
        paths.append(CHANGES / "extractors" / name / "process.md")
    for name in ("STATUS", "PLAYBOOK", "SHARP_EDGES", "FOLLOWUPS", "TICKETS", "CONVENTIONS"):
        paths.append(CHANGES / f"{name}.md")
    paths.append(REPO / "CLAUDE.md")
    paths.append(REPO / "data" / "docs" / "CODE_NAVIGATION.md")
    paths.append(REPO / "data" / "machine-sync" / "RUNBOOK.md")
    paths.append(REPO / "data" / "ils-to-main" / "INSTRUCTIONS.md")
    if MEMORY.exists():
        paths.extend(sorted(MEMORY.glob("*.md")))
    # drop missing + excluded, dedupe preserving order
    seen, out = set(), []
    for p in paths:
        if p and p.exists() and not is_excluded_path(p) and p not in seen:
            seen.add(p); out.append(p)
    return out

def main():
    paths = collect()
    out = REPO / "data" / "knowledge-graph" / "manifest.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(str(p) for p in paths) + "\n")
    assert not [p for p in paths if "payload" in p.parts], "payload leak"
    assert sum(p.name == "STATUS.md" for p in paths) == 1, "expected exactly one STATUS.md"
    print(f"manifest: {len(paths)} files -> {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest data/knowledge-graph/test_kg_corpus.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Generate + verify the real manifest**

Run: `python data/knowledge-graph/build_manifest.py`
Expected: prints `manifest: <N> files` with **N between 85 and 95** (actual: **88** = 39 primaries + 11 eligible fallbacks + 4 extractor + 6 hubs + 2 orient + 2 ops + 24 memory; the 4 folders sst-4526/4609/5030/5357 have no eligible knowledge doc and are correctly absent). Then verify no leaks/dupes:

```bash
grep -c payload data/knowledge-graph/manifest.txt        # expect 0
grep -c '/STATUS.md$' data/knowledge-graph/manifest.txt  # expect 1
sort data/knowledge-graph/manifest.txt | uniq -d         # expect empty (no dupes)
```
Expected: `0`, `1`, empty. (No commit — gitignored.)

---

### Task 2: Corpus staging

**Files:**
- Create: `data/knowledge-graph/stage_corpus.py`
- Modify: `data/knowledge-graph/test_kg_corpus.py` (add `flat_name` tests)

**Interfaces:**
- Consumes: `data/knowledge-graph/manifest.txt` (from Task 1).
- Produces: `flat_name(p: Path) -> str`; populates `data/knowledge-graph/_corpus/` with one flat copy per manifest entry; raises on name collision or `payload` path.

- [ ] **Step 1: Write the failing test** (append to `test_kg_corpus.py`)

```python
def test_flat_name_groups():
    sc = _load("stage_corpus")
    P = Path
    assert sc.flat_name(P("/r/data/changes/sst-5468/sst-5468.md")) == "sst-5468__sst-5468.md"
    assert sc.flat_name(P("/r/data/changes/extractors/doc/process.md")) == "extractor__doc__process.md"
    assert sc.flat_name(P("/r/data/changes/STATUS.md")) == "hub__STATUS.md"
    assert sc.flat_name(P("/r/CLAUDE.md")) == "orient__CLAUDE.md"
    assert sc.flat_name(P("/r/data/docs/CODE_NAVIGATION.md")) == "orient__CODE_NAVIGATION.md"
    assert sc.flat_name(P("/r/data/machine-sync/RUNBOOK.md")) == "ops__RUNBOOK.md"
    assert sc.flat_name(P("/h/.claude/projects/-mnt-d-ILS/memory/project_state.md")) == "memory__project_state.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest data/knowledge-graph/test_kg_corpus.py::test_flat_name_groups -v`
Expected: FAIL — `stage_corpus.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
# data/knowledge-graph/stage_corpus.py
"""Copy manifest files into _corpus/ with provenance-preserving flat names."""
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[2]
KG = REPO / "data" / "knowledge-graph"
CORPUS = KG / "_corpus"

def flat_name(p: Path) -> str:
    parts = p.parts
    if "memory" in parts and ".claude" in parts:
        return f"memory__{p.name}"
    if "extractors" in parts:
        variant = parts[parts.index("extractors") + 1]
        return f"extractor__{variant}__{p.name}"
    for part in parts:
        if part.startswith("sst-"):
            return f"{part}__{p.name}"
    if "machine-sync" in parts or "ils-to-main" in parts:
        return f"ops__{p.name}"
    if len(parts) >= 2 and parts[-2] == "changes":
        return f"hub__{p.name}"
    return f"orient__{p.name}"

def main():
    lines = [l.strip() for l in (KG / "manifest.txt").read_text().splitlines() if l.strip()]
    if CORPUS.exists():
        shutil.rmtree(CORPUS)
    CORPUS.mkdir(parents=True)
    seen: dict[str, str] = {}
    for line in lines:
        src = Path(line)
        assert "payload" not in src.parts, f"payload leak: {src}"
        name = flat_name(src)
        if name in seen:
            raise SystemExit(f"name collision: {name} <- {src} and {seen[name]}")
        seen[name] = line
        shutil.copy2(src, CORPUS / name)
    print(f"staged {len(seen)} files -> {CORPUS}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest data/knowledge-graph/test_kg_corpus.py -v`
Expected: PASS (3 tests total).

- [ ] **Step 5: Stage + verify the real corpus**

Run: `python data/knowledge-graph/stage_corpus.py`
Expected: `staged <N> files -> .../\_corpus` with N == the manifest count. Verify:

```bash
ls data/knowledge-graph/_corpus | wc -l                       # == manifest count
ls data/knowledge-graph/_corpus | grep -c payload             # 0
find data/knowledge-graph/_corpus -name '*.png' -o -name '*.json' -o -name '*.docx' | wc -l   # 0
ls data/knowledge-graph/_corpus | grep -E '^(sst-|hub__|extractor__|orient__|ops__|memory__)' | wc -l  # == count
```
Expected: count matches, `0`, `0`, count matches (every file mapped to a known group).

---

### Task 3: Run graphify + inspect against success criteria

**Files:**
- Create: `data/knowledge-graph/_findings.md` (the keep/extend/replace decision record)
- Output (generated): `data/knowledge-graph/output/` (graphify HTML + JSON + audit)

**Interfaces:**
- Consumes: `data/knowledge-graph/_corpus/` (from Task 2).

- [ ] **Step 1: Invoke graphify on the staged corpus**

Confirm the skill's input interface first (it may take a path or the current directory). Preferred:

```
/graphify data/knowledge-graph/_corpus
```
If it only builds from the current directory, run it from inside `_corpus/` and move the result:
```
cd data/knowledge-graph/_corpus && /graphify .
```
Direct the output/artifacts under `data/knowledge-graph/output/`. **Do not** let any artifact land outside `data/` (client names).
Expected: an HTML graph + JSON + audit report produced without error over ~103 files.

- [ ] **Step 2: Verify output location + confidentiality**

```bash
ls -R data/knowledge-graph/output | head
git -C /mnt/d/ILS/document-parser-lambda status --porcelain | grep -v '^?? data/' | grep -i knowledge && echo "!! LEAK outside data/" || echo "OK — contained in data/"
```
Expected: artifacts present under `data/knowledge-graph/output/`; the leak check prints `OK`.

- [ ] **Step 3: Cluster-fidelity inspection (design §5.1)**

Open the HTML graph. Confirm communities map to real knowledge clusters. Record in `_findings.md` whether each is present as a recognisable cluster:
- letter-end danger-zone (SST-4280 / 4940 / 5068 / 5072)
- title detection (5047 / 5091 / 5354 / 5466 / 5468)
- investor-name (5355 / 5518 / 5589)
- comment-memo (4415 / 4559 / 5069)
- PDF cascade (4743 / 4756 / 5582)
- env/infra (4804) + the ops/workspace island (machine-sync/ils-to-main)

- [ ] **Step 4: Query-usefulness inspection (design §5.2)**

Run three queries and record whether the returned tickets are the right ones and more useful than grep:
```
/graphify query "get_letter_end"
/graphify query "letter-end danger zone"
/graphify query "investor name determinism"
```
Expected recall (from known corpus): letter-end → 4280/4940/5068/5072; investor → 5355/5518/5589. Note hits/misses in `_findings.md`.

- [ ] **Step 5: Record the decision**

Write `data/knowledge-graph/_findings.md`: how many of the 3 success criteria held (cluster fidelity, query usefulness, legibility), and the verdict — **KEEP** (graphify sufficient → plan Phase 2 enrichment/share) / **EXTEND** (good skeleton, add the deterministic-edge layer) / **REPLACE** (pivot to deterministic-graph approach A). Include 1–2 concrete examples supporting the verdict.
Expected: a decision record that makes the Phase-2 go/no-go obvious. (No commit — gitignored.)

---

## Self-Review

**Spec coverage:**
- §1 goal (recall/relationships/onboarding) → validated by Task 3 Steps 3–4. ✓
- §2 corpus manifest (all 7 groups + fallback + exclusions) → Task 1 `collect()` + Task 2 staging. ✓
- §2 payload/`.png/.json/.docx` exclusions → Task 1 `is_excluded_path` + Task 2 assertion + Task 2 Step 5 checks. ✓
- §3 mechanism (manifest → stage → graphify → output under data/) → Tasks 1–3. ✓
- §4 confidentiality (contained in data/) → Task 3 Step 2 leak check. ✓
- §5 success criteria (cluster/query/legibility) → Task 3 Steps 3–5. ✓
- §6 out-of-scope (LLM edges, MCP recall, share, housekeeping) → not planned. ✓
- §7 Phase-2 candidates → captured as the verdict options in Task 3 Step 5. ✓

**Placeholder scan:** No TBD/TODO; all code shown in full; the one runtime unknown (graphify's exact input flag) is handled with an explicit fallback in Task 3 Step 1, not a placeholder. ✓

**Type consistency:** `collect`/`largest_md`/`is_excluded_path` (Task 1) and `flat_name` (Task 2) names/signatures are used identically in the tests and `main()`. Manifest is the only interface between Task 1 and Task 2. ✓
