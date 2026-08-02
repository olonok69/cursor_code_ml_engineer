# Ticket Knowledge Graph — Phase 1 spike findings & verdict

> **▶ Phase 1 COMPLETE (2026-07-07). Phase 2 Step 1 (refresh wrapper) DONE 2026-07-08.
> Phase 2 Step 2 (query-during-work surface) DONE 2026-07-09.**
> **RESUME HERE:** remaining Phase-2 = (3) sanitised external share, (4) optional LLM edge-typing / housekeeping
> projections. To *query* the graph: **`/kg <ticket-or-topic>`** (neighbours), `/kg <A> <B>` (path),
> `/kg find <substr>` (node names) — deterministic, no LLM, via `kg_query.sh` (graphify `explain`/`path`; the
> installed graphify 0.9.8 has NO `--mcp`). Also: open `output/graph.html`. To *refresh* after new tickets:
> **`/kg-refresh`**. Last refresh **2026-07-09**: 99 files → **278 nodes / 628 edges / 14 communities**,
> 30.4×/query (SST-5646/5647 now nodes). Memory: [[project_ticket_knowledge_graph]].
>
> **Date:** 2026-07-07. **Verdict: KEEP + plan Phase 2.** graphify is a good enough substrate;
> the graph delivered recall + relationship value on the first run.

## What was run
- Corpus: **88 curated markdown files** (design §2 manifest) staged into `_corpus/` with flat provenance names.
- Extraction: 4 parallel `general-purpose` subagents (22 files each) → **231 unique nodes, 476 edges, 14 hyperedges**, **0 dangling edges** (stable-id convergence worked).
- Clustering: **17 communities**; the ~12 substantive ones map cleanly to real knowledge domains.
- Outputs (in `output/`, gitignored): `graph.html` (interactive), `graph.json` (GraphRAG), `GRAPH_REPORT.md` (audit).
- Token benchmark: **21.2× reduction** per query (204k naive tokens → ~9.6k/query).

## Environment gotcha (load-bearing for any re-run)
**graphify's `detect()` respects `.gitignore`.** Our entire `data/` tree is gitignored, so running graphify
in place returns **0 files**. Workaround used: stage `_corpus/` into an out-of-repo scratch dir, run graphify
there, copy the 3 artifacts back into `data/knowledge-graph/output/`. All intermediate + final artifacts stay
local-only (scratch is ephemeral; `output/` is gitignored) → confidentiality preserved.

## Success criteria (design §5) — all met
1. **Cluster fidelity — PASS.** Communities matched the expected domains without prompting:
   - C2 Letter-End Danger-Zone (SST-4280/4472/4940/5072/5068/4249), C3 Title Detection & Run-in (5047/5068/5354/5468/5091),
     C7 Investor-Name (5355/5518/5589/5069/5222), C6 PDF Extractor (4743/4756/5582), C0 Numbering (5152/5466/5084/4706/5404),
     C10 Runtime Env/Docker (4804/4773 + env cutover), C4 Prompts/AI-Config (4416/4627/4559), C9 Rich-Text HTML (5016/4653/4736).
2. **Query usefulness — PASS (exceeded).** BFS recall:
   - "get_letter_end / danger zone" → 4249/4280/4472/4940/5055/5068/5072 **plus SST-4834** (remove 'authorized signatory' from LETTER_END_LONG) — a real letter-end ticket not in working memory.
   - "investor name determinism" → 5518/5355/5069 **plus SST-5222** (InvestorNameCleaner).
   - "run-in title numbered list paragraph" → 5468/5047 + title-pipeline neighbours.
   Surfacing 4834/5222 unprompted is the cross-document-recall payoff — better than grep.
3. **Legibility — PASS.** God nodes are the true load-bearing abstractions (`NewDocxEntityExtractor`, `get_letter_end`,
   `is_potential_title`, SST-4416/4280/4665); betweenness correctly flags `NewDocxEntityExtractor` as the cross-domain hub.

## Verdict: KEEP → Phase 2
graphify is sufficient as the graph substrate. Recommended Phase-2 order (from design §7):
1. **Refresh workflow** — a one-command wrapper (`build_manifest → stage_corpus → scratch-run → copy back`) so the graph
   stays current as tickets land. (The `.gitignore` workaround must be baked in.)
2. **Query-during-work surface** — wire `graph.json` into a query path (graphify `--mcp` server, or a thin lookup) so
   recall happens mid-bug, not just by opening the HTML. This is the true CodeGraph analog and the highest-value next step.
3. **Sanitised external share** — client→role pass on node labels to produce a shareable version (labels currently carry
   client names e.g. "Covalent/Wafra run-in").
4. **(Optional) LLM edge-typing / housekeeping projections** — lower priority; the current EXTRACTED/INFERRED edges already
   answer relationship questions.

## How to refresh (Phase-2 wrapper EXISTS as of 2026-07-08)

**One command (recommended):** `/kg-refresh` — the user-level skill (`~/.claude/skills/kg-refresh/`)
orchestrates prepare → /graphify → finalize, syncs the in-place query copy, and leak-checks. Design/plan:
`../changes/knowledge-graph/phase2-refresh-{design,plan}.md`.

**By hand (same `kg_refresh.sh` script the skill drives):**
```bash
cd /mnt/d/ILS/document-parser-lambda && source .venv/bin/activate
bash data/knowledge-graph/kg_refresh.sh prepare      # manifest -> _corpus/ -> ~/.cache/ils-kg (override KG_SCRATCH)
/graphify ~/.cache/ils-kg/_corpus                    # Claude step: detect -> subagents -> cluster -> label -> html
bash data/knowledge-graph/kg_refresh.sh finalize     # copy back + sync graphify-out/graph.json + leak-check
```
Open `data/knowledge-graph/output/graph.html` (self-contained, no server).

**Why the wrapper beats the old 8-line recipe:** `finalize` also refreshes the in-place
`data/knowledge-graph/graphify-out/graph.json` that `/graphify query` reads — the old recipe only touched
`output/`, so post-refresh queries silently ran against the STALE graph. Guards + the `.gitignore`-scratch
workaround + the leak-check now live in the script, not in your memory.

> **Refresh run 2026-07-08:** corpus 88→**96 files**; graph **231→345 nodes / 476→640 edges / 17→14 communities**;
> **79.2×** token reduction/query (was 21.2×). New tickets now in the graph incl. SST-5623/5357/5589/5610/5466;
> a `/graphify query "soft body letter end"` correctly walks SST-5623 → 4249/4280/4472/4940/5068 danger zone.

### Original Phase-1 recipe (superseded — kept for reference)
```bash
# python build_manifest.py && python stage_corpus.py
# SCRATCH=<out-of-repo>/kg; rm -rf "$SCRATCH"; cp -r _corpus "$SCRATCH/_corpus"
# cd "$SCRATCH" && /graphify _corpus
# cp graphify-out/{graph.html,graph.json,GRAPH_REPORT.md} .../data/knowledge-graph/output/   # <-- missed graphify-out/ sync
```
