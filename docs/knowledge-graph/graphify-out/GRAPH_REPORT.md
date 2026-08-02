# Graph Report - _corpus  (2026-07-07)

## Corpus Check
- 88 files · ~153,547 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 231 nodes · 476 edges · 17 communities (12 shown, 5 thin omitted)
- Extraction: 94% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 26 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Numbering & List Reconstruction|Numbering & List Reconstruction]]
- [[_COMMUNITY_DOCX Provisions & Title Pipeline|DOCX Provisions & Title Pipeline]]
- [[_COMMUNITY_Letter-End Detection Danger-Zone|Letter-End Detection Danger-Zone]]
- [[_COMMUNITY_Title Detection & Run-in Titles|Title Detection & Run-in Titles]]
- [[_COMMUNITY_Prompts & AI-Config Externalisation|Prompts & AI-Config Externalisation]]
- [[_COMMUNITY_Comment-Memo Path & Debug Playbook|Comment-Memo Path & Debug Playbook]]
- [[_COMMUNITY_PDF Extractor & OCR Fallback|PDF Extractor & OCR Fallback]]
- [[_COMMUNITY_Investor-Name Determinism|Investor-Name Determinism]]
- [[_COMMUNITY_Orientation, Infra & Output Contract|Orientation, Infra & Output Contract]]
- [[_COMMUNITY_Rich-Text HTML Contract|Rich-Text HTML Contract]]
- [[_COMMUNITY_Runtime Env & Docker (libicuSpire)|Runtime Env & Docker (libicu/Spire)]]
- [[_COMMUNITY_DOCPDF Config Splits|DOC/PDF Config Splits]]
- [[_COMMUNITY_BranchPR & Handover Conventions|Branch/PR & Handover Conventions]]
- [[_COMMUNITY_Confidentiality Conventions|Confidentiality Conventions]]
- [[_COMMUNITY_TDD Discipline|TDD Discipline]]
- [[_COMMUNITY_Generic-Solutions Rule|Generic-Solutions Rule]]
- [[_COMMUNITY_Letter-End Danger-Zone (marker)|Letter-End Danger-Zone (marker)]]

## God Nodes (most connected - your core abstractions)
1. `DOC/DOCX Provisions Extractor (NewDocxEntityExtractor)` - 19 edges
2. `TKT-108 (prompts.json/ai_config.json externalisation; providers; reload)` - 18 edges
3. `TKT-130 (block-HTML contract; Option A Phase 2)` - 18 edges
4. `TKT-115 (glued-title reconciliation gate; >=2 alphanumeric guard)` - 17 edges
5. `get_letter_end (forward-only substring match)` - 16 edges
6. `is_potential_title (title-validity gate)` - 15 edges
7. `TKT-101 (new PDF extractor; LETTER_END DOC/PDF split; centralised lists)` - 15 edges
8. `TKT-113 (Admin UI for prompts + AI config; planning)` - 15 edges
9. `TKT-106 (BaseEntityExtractor; CHUNK_SIZE/threshold splits)` - 14 edges
10. `TKT-107 (comment-memo deterministic doc path; triple-guard; Phase 2.1)` - 13 edges

## Surprising Connections (you probably didn't know these)
- `is_potential_title (title-validity gate)` --depends_on--> `BaseEntityExtractor (shared base class)`  [INFERRED]
  extractor__doc__process.md → tkt-106__tkt-106.md
- `Memory: MSL all-or-nothing save bug` --conceptually_related_to--> `TKT-113 (Admin UI for prompts + AI config; planning)`  [AMBIGUOUS]
  memory__project_msl_allornothing_save.md → hub__FOLLOWUPS.md
- `extractor_lists.json is import-time only, NOT hot-reloadable` --references--> `src/config/extractor_lists.json`  [EXTRACTED]
  hub__PLAYBOOK.md → extractor__doc__process.md
- `TKT-128 (letter-end structural look-ahead veto)` --rationale_for--> `_confirm_letter_end_via_lookahead (8-para veto)`  [EXTRACTED]
  hub__TICKETS.md → hub__SHARP_EDGES.md
- `TKT-107 (comment-memo deterministic doc path; triple-guard; Phase 2.1)` --conceptually_related_to--> `paragraph_levels.find_signoff_cut_idx`  [INFERRED]
  hub__TICKETS.md → hub__SHARP_EDGES.md

## Hyperedges (group relationships)
- **Letter-end / boundary danger zone (tickets sharing the forward-only + gated look-ahead flow)** — ticket_tkt_105, ticket_tkt_101, ticket_tkt_109, ticket_tkt_128, ticket_tkt_134, ticket_tkt_136, ticket_tkt_132 [EXTRACTED 0.85]
- **Tickets sharing the _provision_title_head helper (single copy on merge)** — ticket_tkt_131, ticket_tkt_134, ticket_tkt_103 [EXTRACTED 0.90]
- **Rich-text Option A block-HTML contract (wrap_block_html across variants)** — ticket_tkt_114, ticket_tkt_130, sym_wrap_block_html, sym_normalize_rich_text_fields [EXTRACTED 0.85]
- **Config-externalization trajectory: lists → scalars → AI provider/prompts** — ticket_tkt_101, ticket_tkt_106, ticket_tkt_108 [EXTRACTED 0.90]
- **Forward-only letter-end matching invariant lineage** — ticket_tkt_105, ticket_tkt_109, inv_forward_only_substring, sym_get_letter_end [EXTRACTED 0.90]
- **Deliberate DOC≠PDF split invariants** — inv_letter_end_doc_pdf_split, inv_spacy_model_split, inv_chunk_size_split, inv_title_threshold_split [EXTRACTED 0.85]
- **TKT-108 AI provider + hot-reload subsystem** — sym_ai_provider_registry, sym_ai_config_store, sym_prompt_store, sym_reload_configuration [EXTRACTED 0.90]
- **DOCX spinner root cause: INVARIANT/env cutover** — ticket_tkt_124, inv_globalization_invariant, cfg_helm_lambda_patcher, env_new_dev_eucentral1 [EXTRACTED 0.90]
- **Letter-end detection: substring match gated by structural look-ahead over config lists** — symbol_get_letter_end, symbol_confirm_letter_end_lookahead, config_extractor_lists_json, ticket_tkt_128 [EXTRACTED 0.90]
- **Option A rich-text HTML ownership: memo Phase 1 then all-extractor Phase 2 plus security escape stage** — contract_option_a_html_ownership, symbol_wrap_html_paragraphs, ticket_tkt_114, ticket_tkt_130, ticket_tkt_129 [EXTRACTED 0.85]
- **PDF title silent-drop family: alpha gate, between-chunk gap, footer over-extension, duplicate-title** — ticket_tkt_112, ticket_tkt_118, ticket_tkt_120, variant_pdf_extractor [EXTRACTED 0.85]
- **get_titles structural provision-detector chain (two-tier → style-level → ListText → run-in → LLM)** — sym_detect_two_tier_provisions, sym_detect_style_level_provisions, sym_detect_listtext_provisions, sym_detect_runin_provisions, sym_get_titles [EXTRACTED 0.90]
- **Style-linked / list-linked numbering reconstruction lineage** — ticket_tkt_140, ticket_tkt_137, ticket_tkt_102, ticket_tkt_149 [EXTRACTED 0.85]
- **Glued/underlined title anchoring & demotion defect class** — ticket_tkt_134, ticket_tkt_138, ticket_tkt_144, ticket_tkt_168 [EXTRACTED 0.85]

## Communities (17 total, 5 thin omitted)

### Community 0 - "Numbering & List Reconstruction"
Cohesion: 0.11
Nodes (30): Convention: GitHub ops are Cursor's, not Claude's, Convention: no client names in committed artifacts, Convention: subagents must not run git push / gh, Document class: ClientU ClientV / ClientZ V style-linked-numbering side-letter family, Ops: laptop→main delta landing runbook, Ops: machine-sync runbook (main⇄laptop), src/services/extractor_wrappers/base.py, Invariant: LETTER_END_* changes stay forward-only substring + DOC≠PDF split + re-run ClientN/ClientP (+22 more)

### Community 1 - "DOCX Provisions & Title Pipeline"
Cohesion: 0.12
Nodes (28): Soft-fallback: empty extraction -> [Manual review required] (introduced TKT-115 PR#50), Memory: TKT-121 GA chart follow-up, Memory: TKT-151 Confluence extraction rules, Memory: title-less side letters (TKT-142), DOCX provisions extractor (NewDocxEntityExtractor), Table extractor (TableDocxEntityExtractor), DOC/DOCX Provisions Extractor (NewDocxEntityExtractor), Table DOCX Extractor (TableDocxEntityExtractor) (+20 more)

### Community 2 - "Letter-End Detection Danger-Zone"
Cohesion: 0.14
Nodes (26): src/config/extractor_lists.json, src/config/extractor_lists.json, Orientation: CODE_NAVIGATION.md, TKT-105 writeup, TKT-101 writeup, TKT-109 writeup, src/config/extractor_config.py, Invariant: end-of-letter substring is forward-only (+18 more)

### Community 3 - "Title Detection & Run-in Titles"
Cohesion: 0.17
Nodes (22): Convention: generic solutions only (fix the class, not the case), src/data_extractors/doc_extractor.py, src/config/extractor_lists.json, Regression gate: canonical ClientN + ClientP integration battery, Outbound quality gate at get-sl-upload-status shape (full pipeline), _confirm_letter_end_via_lookahead (8-para veto), _detect_runin_provisions (run-in title detector), get_letter_start / letter-start floor (+14 more)

### Community 4 - "Prompts & AI-Config Externalisation"
Cohesion: 0.16
Nodes (18): src/config/ai_config.json, src/config/prompts.json, src/config/prompts.json (PromptStore, byte-identity contract), Memory: HTML ownership/security/admin, Memory: MSL all-or-nothing save bug, TKT-108 writeup, Invariant: byte-identity contract for 16 prompts, Invariant: byte-identity prompt contract (test_prompts_store.py) (+10 more)

### Community 5 - "Comment-Memo Path & Debug Playbook"
Cohesion: 0.12
Nodes (18): Convention: get-sl-upload-status is the output contract, TKT-107 writeup, Sign-off cut applied at 3 sites, NOT fed to boundary/sentinel pass, TKT-107 triple-guard is load-bearing (Path 2 gate), Playbook: separate PROVEN from INFERRED in debugging, Playbook: temperature=0 is not bit-reproducible; one green run is not a pass, Playbook: LLM variance is a hypothesis of last resort, Playbook: reproduce at output-contract shape, not one primitive (+10 more)

### Community 6 - "PDF Extractor & OCR Fallback"
Cohesion: 0.15
Nodes (17): Between-chunk numbering-gap retry (echo-back + numbering guards), Duplicate-titled provision recovery via synthetic title_idx_tpl, src/config/ai_config.json (AIConfigStore, provider routing), Decision: pin gpt-5.4 temperature to 0.0 for deterministic extraction, PDF Provisions Extractor (OpenAIPDFEntityExtractor), src/data_extractors/pdf_extractor.py, Sharp edge: LLM non-determinism (temp=0 not bit-reproducible), Playbook: walk the PDF pipeline in order, never jump to the LLM (+9 more)

### Community 7 - "Investor-Name Determinism"
Cohesion: 0.17
Nodes (16): Document class: ClientC/ClientQ run-in numbered List Paragraph titles, Memory: TKT-150 CM investor-name determinism, src/data_extractors/comment_memo_extractor.py, src/config/prompts.json, Lesson: temperature=0 not bit-reproducible; one green run ≠ pass; fix sensitivity not variance, _canonical_investor_name / normalize_investor_lp_name (header-snap), get_entities / normalize_investor_lp_name (CM investor normaliser), get_table_data (continuation-table inheritance) (+8 more)

### Community 8 - "Orientation, Infra & Output Contract"
Cohesion: 0.16
Nodes (14): Cursor owns push/PR/merge; Claude analysis-only, DOC/DOCX canonical, PDF best-effort strategy, get-sl-upload-status output contract, Memory: docs/memory layout post-slim, Memory: extraction format strategy, Memory: project state snapshot, Memory: user profile, Orientation: sample-service CLAUDE.md (+6 more)

### Community 9 - "Rich-Text HTML Contract"
Cohesion: 0.30
Nodes (14): Option A: Lambda owns rich-text HTML contract (<p>-wrapped), Comment Memo Extractor (CommentMemoExtractor), Rationale: escape what you produce (strip!=escape; producer boundary), ExtractorBase._normalize_rich_text_fields, src/html_paragraphs.py::wrap_block_html, BaseEntityExtractor / ExtractorBase (shared base), escape_non_allowlisted_html (allowlist escaper), get_qr_d (comment-memo q/r factory) (+6 more)

### Community 10 - "Runtime Env & Docker (libicu/Spire)"
Cohesion: 0.24
Nodes (12): helm-values lambda-patcher.yaml, DOTNET_SYSTEM_GLOBALIZATION_INVARIANT env var (Spire.Doc culture mode), Dockerfile (Lambda runtime image, libicu), Memory: dev SL Lambda AWS env cutover, Memory: local emulation goal, New dev env <account-id> / eu-central-1, Old dev env <account-id> / eu-west-2, Config: DOTNET_SYSTEM_GLOBALIZATION_INVARIANT (+4 more)

### Community 11 - "DOC/PDF Config Splits"
Cohesion: 0.25
Nodes (9): TKT-106 writeup, Invariant: CHUNK_SIZE_DOC 3500 ≠ PDF 2000, Invariant: spaCy sm(DOC) ≠ md(PDF), Invariant: title-match threshold DOC 85 ≠ PDF 95, CHUNK_SIZE_DOC=3500 vs CHUNK_SIZE_PDF=2000 (do not unify), Spacy model DOC=sm vs PDF=md (intentional divergence), title_match_threshold DOC=85 vs PDF=95 (do not unify), BaseEntityExtractor (shared base class) (+1 more)

## Ambiguous Edges - Review These
- `TKT-113 (Admin UI for prompts + AI config; planning)` → `Memory: MSL all-or-nothing save bug`  [AMBIGUOUS]
  memory__project_msl_allornothing_save.md · relation: conceptually_related_to

## Knowledge Gaps
- **65 isolated node(s):** `_is_prefix_of_longer_word (whole-word title gate)`, `_is_signature_page_marker (hard letter-end)`, `_strip_redundant_provision_numbering`, `_canonical_investor_name / normalize_investor_lp_name (header-snap)`, `CHUNK_SIZE_DOC=3500 vs CHUNK_SIZE_PDF=2000 (do not unify)` (+60 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `TKT-113 (Admin UI for prompts + AI config; planning)` and `Memory: MSL all-or-nothing save bug`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `DOC/DOCX Provisions Extractor (NewDocxEntityExtractor)` connect `DOCX Provisions & Title Pipeline` to `Numbering & List Reconstruction`, `Letter-End Detection Danger-Zone`, `Title Detection & Run-in Titles`, `Investor-Name Determinism`, `Rich-Text HTML Contract`, `DOC/PDF Config Splits`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `TKT-130 (block-HTML contract; Option A Phase 2)` connect `Rich-Text HTML Contract` to `Numbering & List Reconstruction`, `DOCX Provisions & Title Pipeline`, `PDF Extractor & OCR Fallback`, `Investor-Name Determinism`, `Orientation, Infra & Output Contract`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `TKT-115 (glued-title reconciliation gate; >=2 alphanumeric guard)` connect `DOCX Provisions & Title Pipeline` to `Title Detection & Run-in Titles`, `Letter-End Detection Danger-Zone`, `Runtime Env & Docker (libicu/Spire)`, `Comment-Memo Path & Debug Playbook`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **What connects `_is_prefix_of_longer_word (whole-word title gate)`, `_is_signature_page_marker (hard letter-end)`, `_strip_redundant_provision_numbering` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Numbering & List Reconstruction` be split into smaller, more focused modules?**
  _Cohesion score 0.10574712643678161 - nodes in this community are weakly interconnected._
- **Should `DOCX Provisions & Title Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.11904761904761904 - nodes in this community are weakly interconnected._