# Design — Ticket Knowledge Graph (Phase 1: graphify spike)

> **Date:** 2026-07-07. **Status:** design approved (brainstorming), pending spec review → implementation plan.
> **Location rationale:** kept under gitignored `data/` (not `docs/superpowers/specs/`) because the corpus and
> the graph output are saturated with client names — nothing here may be committed to the remote.

## 1. Goal

A visual, queryable **knowledge graph over the curated ticket + lessons-learned markdown** — internal-only — to:
- **Recall during work:** when starting a bug/ticket, find the relevant prior tickets, playbook lessons, and sharp-edges faster than grepping 540 files.
- **Relationships:** see how tickets, invariants/danger-zones, and lessons connect (citation chains, shared subsystems).
- **Onboarding map:** a navigable overview a new engineer (or Cursor) can orient from.

Phase 1 deliberately validates whether **off-the-shelf `graphify`** is good enough *before* investing in custom deterministic-edge extraction, an LLM enrichment pass, or a CodeGraph-style query-during-work surface. It is a **spike with a keep/extend/replace decision at the end**, not a committed product.

## 2. Corpus (the manifest)

A reviewable manifest file (`data/knowledge-graph/manifest.txt`) lists every included path, so the corpus is explicit and reproducible — not a wildcard that silently changes. Membership rules:

| Group | Rule | ~count |
|---|---|---|
| Per-ticket primary | `data/changes/sst-*/sst-*.md` | 50 |
| Per-ticket fallback | For the **15** `sst-*/` folders with **no** `sst-NNNN.md`, include the **single largest `.md`** in that folder (deterministic). Excludes `_handover_to_cursor.md`, `qa_acceptance_criteria.md`, `_diag_*.md` from the fallback pick. | ~15 |
| Extractor current-state | `data/changes/extractors/{comment_memo,doc,pdf,table}/process.md` | 4 |
| Hubs | `data/changes/{STATUS,PLAYBOOK,SHARP_EDGES,FOLLOWUPS,TICKETS,CONVENTIONS}.md` | 6 |
| Orientation | `CLAUDE.md`, `data/docs/CODE_NAVIGATION.md` | 2 |
| Ops / workspace | `data/machine-sync/RUNBOOK.md`, `data/ils-to-main/INSTRUCTIONS.md` | 2 |
| Memory | `~/.claude/projects/-mnt-d-ILS/memory/*.md` | 24 |
| **Total** | | **~103** |

The two ops files are a different domain (workspace portability / laptop setup) from extraction, but are genuine self-contained lessons-learned; expect them to form their own "workspace/env" island — a useful check on the clustering rather than a pollutant.

**Explicitly excluded** (noise, duplication, or *stale copies*):
- All `.png` / `.json` / `.docx`; `_handover_to_cursor.md` (restates the ticket doc for Cursor); `qa_acceptance_criteria.md`; `_diag_*.md` write-ups; `render_harness/` docs; `_pending/` scratch. Density without distinct knowledge.
- **`data/ils-to-main/payload/**` — HARD EXCLUDE.** It is a **stale partial copy of the workspace** (a travel-delta tarball's contents): a duplicate ~11.5k-word `STATUS.md` and duplicate copies of ticket docs (e.g. sst-5404). Including it would create duplicate/conflicting/stale nodes and corrupt the graph. The staging script must guard against *any* nested `data/changes/` or `payload/` copy, not just this one path.

## 3. Mechanism

1. **Build the manifest** — a small script enumerates the rules in §2 and writes `data/knowledge-graph/manifest.txt` (one path per line). Re-runnable; the manifest is diffable so corpus changes are visible.
2. **Stage** — copy each manifest entry into `data/knowledge-graph/_corpus/` with a **provenance-preserving flat name** so graphify sees a clean single directory and every node traces back to its source:
   - `sst-5468__sst-5468.md`, `extractor__doc__process.md`, `hub__STATUS.md`, `orient__CODE_NAVIGATION.md`, `memory__project_state.md`.
3. **Run graphify** — `/graphify` (or `/graphify .` from inside `_corpus/`) to build the graph. Confirm its exact input interface at run time; if it accepts a directory, point it at `_corpus/`.
4. **Output** — graphify's HTML + JSON + audit report land under `data/knowledge-graph/` (e.g. `data/knowledge-graph/output/`). **Everything stays under gitignored `data/`.**

The manifest + staging are a thin, deterministic, re-runnable wrapper. Refreshing the graph after new tickets = re-run steps 1–3 (cheap).

## 4. Confidentiality (load-bearing)

The corpus and therefore the graph output contain client names (Covalent, Wafra, Avista, ASF, Webster, CalPERS, …). This is fine **internally** because it never leaves gitignored `data/`. Consequences:
- The `data/knowledge-graph/` tree must remain under `data/` (already gitignored) — never move it to a committed path.
- **External sharing is a separate, gated Phase 2+ deliverable** requiring a client-name → role sanitisation pass. Not attempted in Phase 1.

## 5. Success criteria (inspected after the run)

1. **Cluster fidelity** — communities map to real knowledge clusters: letter-end danger-zone (SST-4280 §7 / 4940 / 5068 / 5072), title detection, investor-name (5355/5518/5589), comment-memo, PDF cascade, env/infra (4804).
2. **Query usefulness** — `/graphify query "get_letter_end"` (and "letter-end danger zone", "investor name") returns the right tickets, and does so more usefully than grep.
3. **Legibility** — the rendered graph is coherent enough to be worth using for onboarding / relationship reasoning.

If ≥2 of these hold → keep + plan Phase 2. If not → the spike told us graphify isn't the right substrate, and we pivot to the deterministic-edge approach (A) cheaply, having lost only the spike.

## 6. Out of scope (Phase 1)

- LLM edge-typing (fixes / regresses / supersedes / depends-on as typed relations).
- CodeGraph-style **query-during-work MCP/CLI** recall surface (Claude auto-surfacing lessons mid-bug).
- The **sanitised external-shareable** graph.
- Auto-derived **housekeeping** (STATUS / FOLLOWUPS / SHARP_EDGES as graph projections).
- Any non-markdown input.

Each is a candidate Phase 2, chosen based on what the spike shows.

## 7. Phase 2+ candidates (recorded, not committed)

- **Deterministic-edge layer** — parse the 3,714 `SST-NNNN` citations + the CLAUDE.md invariant→origin table into typed nodes/edges; a free, always-fresh backbone independent of graphify.
- **Retrieval surface** — index the corpus for query-during-work recall (the true CodeGraph analog), possibly via claude-mem or a small MCP.
- **Sanitised share** — client→role pass to produce an externally-shareable knowledge graph.
- **Housekeeping projections** — generate the hub files from the graph instead of hand-maintaining them.
