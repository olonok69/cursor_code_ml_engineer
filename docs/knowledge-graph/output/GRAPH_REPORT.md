# Graph Report - /home/olonok/.cache/ils-kg/_corpus  (2026-07-17)

## Corpus Check
- 116 files · ~196,224 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 507 nodes · 672 edges · 35 communities (27 shown, 8 thin omitted)
- Extraction: 92% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 49 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_ListSubsection Numbering Reconstruction|List/Subsection Numbering Reconstruction]]
- [[_COMMUNITY_EnvInfra & Confluence Rules|Env/Infra & Confluence Rules]]
- [[_COMMUNITY_Letter-End & Run-in Titles (STB)|Letter-End & Run-in Titles (STB)]]
- [[_COMMUNITY_Comment-Memo & Misc Fixes|Comment-Memo & Misc Fixes]]
- [[_COMMUNITY_Repo Conventions & Extractor Core|Repo Conventions & Extractor Core]]
- [[_COMMUNITY_Config Externalization & Architecture|Config Externalization & Architecture]]
- [[_COMMUNITY_Title Detection Failures|Title Detection Failures]]
- [[_COMMUNITY_Title Cleanup & Prompt Contract|Title Cleanup & Prompt Contract]]
- [[_COMMUNITY_HTML Formatting & Escaping|HTML Formatting & Escaping]]
- [[_COMMUNITY_Comment-Memo Boundaries & Investors|Comment-Memo Boundaries & Investors]]
- [[_COMMUNITY_Letter-End Markers|Letter-End Markers]]
- [[_COMMUNITY_Letter-End & Title Predicates|Letter-End & Title Predicates]]
- [[_COMMUNITY_Run-in Provision Detection (STB)|Run-in Provision Detection (STB)]]
- [[_COMMUNITY_Verification Lessons|Verification Lessons]]
- [[_COMMUNITY_Investor Name & S3 Offload|Investor Name & S3 Offload]]
- [[_COMMUNITY_Comment-Memo Chain Detection|Comment-Memo Chain Detection]]
- [[_COMMUNITY_Title Length & Excluded Phrases|Title Length & Excluded Phrases]]
- [[_COMMUNITY_Code Navigation & Docs Layout|Code Navigation & Docs Layout]]
- [[_COMMUNITY_Paragraph MSL (CR-341)|Paragraph MSL (CR-341)]]
- [[_COMMUNITY_DOCPDF Config Splits|DOC/PDF Config Splits]]
- [[_COMMUNITY_PDF HeaderFooter Clip|PDF Header/Footer Clip]]
- [[_COMMUNITY_PDF Extractor Cascade|PDF Extractor Cascade]]
- [[_COMMUNITY_Confidentiality Policy & KG|Confidentiality Policy & KG]]
- [[_COMMUNITY_HTML Ownership & Escaping|HTML Ownership & Escaping]]
- [[_COMMUNITY_A7 Run-in Taxonomy|A7 Run-in Taxonomy]]
- [[_COMMUNITY_Forward-Only Letter-End|Forward-Only Letter-End]]
- [[_COMMUNITY_Provision Similarity Perf|Provision Similarity Perf]]
- [[_COMMUNITY_Same-Style Run Boundary|Same-Style Run Boundary]]
- [[_COMMUNITY_Block-HTML Wrapping|Block-HTML Wrapping]]
- [[_COMMUNITY_BranchPR Conventions|Branch/PR Conventions]]
- [[_COMMUNITY_SST-5647 Strict-OOXML|SST-5647 Strict-OOXML]]
- [[_COMMUNITY_SST-5055 Letter-Start Floor|SST-5055 Letter-Start Floor]]
- [[_COMMUNITY_SST-5063 Bare Markers|SST-5063 Bare Markers]]
- [[_COMMUNITY_SST-4584 Alpha-Count Gate|SST-4584 Alpha-Count Gate]]
- [[_COMMUNITY_SST-5385 Batch Bg-Task|SST-5385 Batch Bg-Task]]

## God Nodes (most connected - your core abstractions)
1. `SST-5778 numbering start reset (w:start ignored)` - 23 edges
2. `SST-5750 run-in Heading-1 provisions repeat previous title` - 15 edges
3. `SST-5623 DOCX last provision truncated at soft binding clause` - 14 edges
4. `SST-5695 BE VIII subsection marker fidelity + provision-title casing` - 14 edges
5. `SST-5610 comment-memo chain boundaries on narrative memos` - 13 edges
6. `SST-5749 attached policy annex ingested as phantom provisions (letter-end not honoured)` - 13 edges
7. `SST-4940 letter-end structural look-ahead disambiguator` - 12 edges
8. `SST-5468 Covalent/Wafra numbered List Paragraph run-in titles not recognised` - 12 edges
9. `SST-5646 run-in letter-end marker missed (13-word window)` - 12 edges
10. `SST-4706 extraction format report (DOC/DOCX/PDF parity)` - 11 edges

## Surprising Connections (you probably didn't know these)
- `_resolve_letter_start_floor majority-locatable-title invariant` --semantically_similar_to--> `SST-5047 run-in sub-label / letter-start floor guard`  [INFERRED] [semantically similar]
  sst-5055__sst-5055.md → sst-5091__sst-5091.md
- `S3 claim-check: upload result JSON to S3, send only pointer over RPC` --semantically_similar_to--> `_s3_bucket_key_from_url derive bucket+key preserving sl_documents prefix`  [INFERRED] [semantically similar]
  sst-5385__sst-5385.md → sst-5357__sst-5357.md
- `snap-to-addressee (derive investor from To: block)` --semantically_similar_to--> `header-snap to deterministic LP core`  [INFERRED] [semantically similar]
  sst-5589__sst-5589.md → sst-5518__sst-5518.md
- `SST-5589 investor hallucination` --semantically_similar_to--> `SST-5518 comment-memo investor-name determinism`  [INFERRED] [semantically similar]
  memory__project_be_viii_and_covalent_preticket.md → memory__project_sst5518_cm_investor_name.md
- `_confirm_letter_end_via_lookahead rule 2 (soft defers to hard marker)` --semantically_similar_to--> `SST-4940 letter-end look-ahead veto`  [INFERRED] [semantically similar]
  memory__project_sst5132_soft_body_inclusion.md → memory__project_be_viii_and_covalent_preticket.md

## Import Cycles
- None detected.

## Communities (35 total, 8 thin omitted)

### Community 0 - "List/Subsection Numbering Reconstruction"
Cohesion: 0.06
Nodes (48): w:start / startOverride list numbering value, SST-4706 sub-clause rendering by nesting level, SST-5063 nested sub-clauses with bare-period markers render flat, Sharp edge: global allow_bare run gate residual false-positive risk, _has_bare_marker_run consecutive-sequence gate, _infer_subsection_layout / _format_provision_description shared renderer, _parse_numbering_xml does not resolve w:numStyleLink (style-linked numbering), _parse_bare_marker / _BARE_RE bare alpha-roman marker recognition (+40 more)

### Community 1 - "Env/Infra & Confluence Rules"
Cohesion: 0.05
Nodes (44): Governance gate: do not merge behaviour contradicting a pending-signoff card, SST-5541 CTO visualization contract, _detect_listtext_provisions deterministic detector, SST-5466 BE VIII style/list numbering, Three style-numbering regimes A/B/C, Dev env cutover eu-west-2 Lambda -> eu-central-1 EKS, helm-values#25 dev-tenant INVARIANT=0 override fix, DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 breaks Spire.Doc on DOC/DOCX (+36 more)

### Community 2 - "Letter-End & Run-in Titles (STB)"
Cohesion: 0.06
Nodes (40): _confirm_letter_end_via_lookahead, _detect_runin_provisions, _detect_two_tier_provisions, _is_real_provision_title, NewDocxEntityExtractor variant, _provision_title_head, SST-4500 DOCX table auto-route probe, SST-4940 letter-end structural look-ahead (+32 more)

### Community 3 - "Comment-Memo & Misc Fixes"
Cohesion: 0.06
Nodes (36): Invariant: letter-end/title scan uses first TITLE_LEN_MAX (13) words (matching-window invariant), SST-4415 deterministic paragraph chain-boundary approach, SST-4559 comment-memo header-from-preceding-table rescue, SST-4653 _wrap_html_paragraphs rich-text contract, SST-4665 empty titles / preceding-prose title guard, SST-4752 sign-off cut / full-pipeline reproduction lesson, SST-4778 soft-fallback for empty extractions, SST-4804 dev env cutover / DOTNET INVARIANT Spire failure (+28 more)

### Community 4 - "Repo Conventions & Extractor Core"
Cohesion: 0.07
Nodes (31): CodeGraph first, Serena for precision, grep/Read fallback, Land the laptop->main delta runbook (non-destructive), Machine-sync runbook main<->laptop (outbound full / inbound delta), Verify inside the deployed Lambda image (mandatory outbound gate), ExtractorVariant table (provisions/table_provisions/comment_memo/pdf), GitHub interaction is Cursor's territory (Claude never pushes/PRs), get-sl-upload-status is the output contract (repo black box), CLAUDE.md mandatory working rules (plan/history/black-box) (+23 more)

### Community 5 - "Config Externalization & Architecture"
Cohesion: 0.09
Nodes (27): SST-5016 rich-text Option A Phase 2 (html_paragraphs), extractor_lists.json unified lists + tuning_params, get_description_subsections empty-list IndexError guard, SST-4280 §7 letter_end DOC vs PDF list split, SST-4280 replace PDF extractor + config externalization, BaseEntityExtractor shared helper base class, What is Intentionally NOT Unified (binding table), re.IGNORECASE on get_numbering_format letter patterns (+19 more)

### Community 6 - "Title Detection Failures"
Cohesion: 0.09
Nodes (27): SST-4584 DAC 6 provision (PDF path), SST-4627 admin UI / hot-reloadable config lists, SST-5030 long underlined title length-gate bypass, SST-5047 run-in sub-label / letter-start floor guard, SST-5055 DOCX body dropped, only trailing notice/schedule extracted, get_letter_start mis-anchors on signature-block furniture, letter_start_short config drops by:/name:/title: signature labels, Rationale: by:/name:/title: are execution-block field labels, never letter openings (+19 more)

### Community 7 - "Title Cleanup & Prompt Contract"
Cohesion: 0.11
Nodes (26): >=2 alphanumeric guard on title-cleanup strips, byte-identity prompt contract (test_prompts_store.py), CHUNK_OVERLAP_DEFAULT=0; overlap>0 makes PDF extraction worse, letter_end_signature_page is a distinct hard tier (not interchangeable), zero-regression policy: ASF/Webster canonical baselines must stay green, Rationale: monolith->Lambda RPC is fire-and-forget; adopt async callback+poll, Rationale: between-chunk gap retry beats chunk overlap (overlap reverted), Rationale: hard-fail on empty extraction (soft-fallback broke bg_task response shape) (+18 more)

### Community 8 - "HTML Formatting & Escaping"
Cohesion: 0.14
Nodes (26): DOC vs PDF config/letter-end lists must stay split (132->119/120->20 regression), LLM non-determinism; temperature=0 not bit-reproducible, Rationale: DOC/DOCX canonical high-fidelity target; PDF best-effort, reactive, Rationale: escape what you produce; producer-boundary output encoding, Rationale: true same-style merger (Option B) kills the run-boundary class at root, Rationale: pin gpt-5 temperature=0 for deterministic extraction, SST-4280 DOC/PDF config split §7, SST-4559 rich-text contract analysis / column roles (+18 more)

### Community 9 - "Comment-Memo Boundaries & Investors"
Cohesion: 0.08
Nodes (25): _detect_listtext_runin_provisions, _should_override_with_runin LLM-dominance gate, SST-5466 subsection marker fidelity, SST-5468 run-in titles fix, SST-5646 Nautic run-in letter-end, _detect_runin_provisions, _is_signature_block_line (SST-5468 QA r1), _provision_title_head run-in head recovery (+17 more)

### Community 10 - "Letter-End Markers"
Cohesion: 0.12
Nodes (25): letter_end_signature_page config list, LETTER_END_SOFT_BODY config list (DOC-only), Invariant: letter-end check runs only past 40% of the document (guards against early false letter-ends), SST-4249 forward-only substring matching convention, SST-4280 DOC/PDF letter-end split (section 7), SST-4472 forward-only substring classifier convention, SST-4940 governing-law boilerplate letter-end look-ahead, _is_real_provision_title (SST-4940 look-ahead guard) title-head fix (+17 more)

### Community 11 - "Letter-End & Title Predicates"
Cohesion: 0.12
Nodes (23): TITLE_LEN_MAX = 13-word title gate, Rationale: SST-4940 needs both config generalisation AND structural look-ahead, SST-4804 long statute-citation title silently dropped, SST-4834 Authorized Signatory letter-end false positive, SST-4940 letter-end structural look-ahead disambiguator, SST-5047 STB extraction issues (subheadings extracted as headings), SST-5132 letter-end (STB batch, disjoint from SST-5778), _is_soft_body_letter_end + intervening-body discriminator (+15 more)

### Community 12 - "Run-in Provision Detection (STB)"
Cohesion: 0.13
Nodes (22): SST-5016 comment-memo HTML contract, Sharp edge: PDF title highlighting wired to extraction attempt 1 only, SST-5582 PDF provision titles not highlighted, SST-5583 comment-memo document preview clipped on the right (frontend), Disproven hypothesis: override-gate _should_override_with_runin misfire (kept for record), Root cause: _detect_listtext_provisions titled provisions with full p.text so run-in titles fail _is_acceptable_title, SST-5750 run-in Heading-1 provisions repeat previous title, SST-5752 first provision dropped when numbered in a different regime (+14 more)

### Community 13 - "Verification Lessons"
Cohesion: 0.12
Nodes (17): find_signoff_cut_idx, SST-4752 deterministic sign-off truncation, SST-4609 None-numbering guard in get_description_subsections, SST-4706 QA4 _strip_redundant_provision_numbering, SST-5072 signature-page hard letter-end + w:caps toggle casing, Durable data/test_issues.py outbound-gate harness, Lesson: termination signals in confidence tiers, hard vs soft (SST-5072), Lesson: reproduce through full pipeline, not the primitive (SST-4752) (+9 more)

### Community 14 - "Investor Name & S3 Offload"
Cohesion: 0.14
Nodes (15): comment_memo.entities prompt, SST-5222 InvestorNameCleaner (monolith MSL), SST-5385 oversized RPC result > SQS 1MB (big/formatted docs fail), S3 claim-check: upload result JSON to S3, send only pointer over RPC, _add_fileinfo_to_extracted_data two oversized sends (unprocessed_data + bg-task response), _used_channel_ids masking error hides real SQS failure as spinner, SST-5518 comment-memo investor-name determinism, header-snap to deterministic LP core (+7 more)

### Community 15 - "Comment-Memo Chain Detection"
Cohesion: 0.20
Nodes (10): CommentMemoExtractor variant, is_at_sentence_boundary shared predicate, SST-4415 Phase 2.1 three-rule Q/R segmentation, Rationale: try cheapest deterministic path first, escalate to LLM only when structurally impossible, Memo routing priority Table then styles then LLM, SST-5069 continuation-table role inheritance, SST-5610 narrative structural boundaries, SST-4415 triple-guard deterministic doc mode (+2 more)

### Community 16 - "Title Length & Excluded Phrases"
Cohesion: 0.33
Nodes (7): is_potential_title title gate, SST-5030 long underlined provision titles retained, TITLE_LEN_MAX word-length gate (13), SST-5354 PDF unanchored excluded-phrase follow-up, SST-5354 start-anchored excluded-phrase match, SST-5646 Nautic run-in signature block absorbed, SST-4349 BaseEntityExtractor + tuning_params

### Community 17 - "Code Navigation & Docs Layout"
Cohesion: 0.33
Nodes (6): document-parser-lambda CLAUDE.md is gitignored (local-only), CodeGraph CLI + MCP (indexed document-parser-lambda), Serena find_referencing_symbols precise pre-rename check, Verdict: CodeGraph + Serena are complementary not redundant, 2026-06-24 docs slim: lean always-loaded core + on-demand reference, Write each ticket record once in STATUS.md (anti-bloat rule)

### Community 18 - "Paragraph MSL (CR-341)"
Cohesion: 0.40
Nodes (6): CR-341 customer request paragraph-format MSL, PLAT46-48 export-service reusable paragraph layout (Paused), SST-4500 table MSL auto-route probe, SST-5444 / CR-341 alternative paragraph-format MSL analysis, Thread A: paragraph-format MSL export (frontend/monolith/export-service, PLAT46-48), Thread B: paragraph-form MSL upload parsing (Lambda; compendium + deduped shapes)

### Community 19 - "DOC/PDF Config Splits"
Cohesion: 0.33
Nodes (6): CHUNK_SIZE_DOC 3500 (do not unify), SST-4280 deliberate DOC/PDF LETTER_END list split, CHUNK_SIZE_PDF 2000 (do not unify), SST-4280 centralised extractor_lists.json + LETTER_END split, SST-4416 6-phase architecture (prompts/ai_config/providers/reload), SST-4627 admin UI for prompts + AI config (planning)

### Community 20 - "PDF Header/Footer Clip"
Cohesion: 0.33
Nodes (6): _extend_footer_detection, get_headers_and_footers geometric clip, SST-4743 page-edge header/footer clip guards, Lesson: LLM variance is a hypothesis of last resort, Lesson: walk PDF pipeline stages in order, SST-4756 QA1 three deterministic bugs (temp pin/footer/duplicate)

### Community 21 - "PDF Extractor Cascade"
Cohesion: 0.40
Nodes (5): PDF three-implementation cascade (OpenAI/Textract/Bedrock), OpenAIPDFEntityExtractor variant, _s3_bucket_key_from_url, SST-5357 Textract S3 bucket+key from file_url, Sharp edge: eager Textract client needs AWS_S3_REGION

### Community 22 - "Confidentiality Policy & KG"
Cohesion: 0.50
Nodes (5): Policy: no client names in committed artifacts, Policy: no ticket IDs in committed code/config, Rationale: ticket IDs rot; rationale belongs in data/changes/<TICKET>/, Feedback: confirmed working conventions (TDD, generic, one-ticket), Ticket knowledge graph over data/changes markdown

### Community 23 - "HTML Ownership & Escaping"
Cohesion: 0.50
Nodes (4): Principle: escape what you produce (producer-escape thesis), Option A: Lambda-owns-HTML production (3 phases), SST-4653 memo _wrap_html_paragraphs (Phase 1), SST-4995 output-handling escaping at ExtractorBase

### Community 24 - "A7 Run-in Taxonomy"
Cohesion: 0.67
Nodes (3): A7 run-in regime taxonomy (A7-i/ii/iii), _detect_listtext_provisions run-in gate, Webster is the A7-ii guardrail not a distinct class

### Community 25 - "Forward-Only Letter-End"
Cohesion: 1.00
Nodes (3): SST-4472 forward-only letter-end substring match, SST-4249 forward-only letter-end match (PDF), Invariant: letter-end matching forward-only, never reverse

### Community 26 - "Provision Similarity Perf"
Cohesion: 0.67
Nodes (3): provision_database_similarity O(n^2) rapidfuzz perf issue, Recall harness is the gate (trigram != fuzz.ratio risk), Thomas redesign: raise store floor + trigram blocking + pair table

## Ambiguous Edges - Review These
- `NewDocxEntityExtractor.get_letter_end forward-only fix` → `SST-5354 excluded-phrase anchoring (DOC path)`  [AMBIGUOUS]
  memory__project_state.md · relation: conceptually_related_to
- `SST-5354 excluded-phrase anchoring (PDF twin bug)` → `SST-5354 excluded-phrase anchoring (DOC path)`  [AMBIGUOUS]
  memory__project_state.md · relation: relates_to
- `SST-4766 MSL upload failure analysis (not a Lambda issue)` → `SST-4995 XSS escape user-controlled text in produced HTML`  [AMBIGUOUS]
  sst-4766__analysis.md · relation: conceptually_related_to

## Knowledge Gaps
- **181 isolated node(s):** `SST-5610 narrative structural boundaries`, `SST-5069 continuation-table role inheritance`, `SST-4869 same-style run-boundary span merger`, `_wrap_html_paragraphs universal HTML wrap`, `find_signoff_cut_idx` (+176 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `NewDocxEntityExtractor.get_letter_end forward-only fix` and `SST-5354 excluded-phrase anchoring (DOC path)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `SST-5354 excluded-phrase anchoring (PDF twin bug)` and `SST-5354 excluded-phrase anchoring (DOC path)`?**
  _Edge tagged AMBIGUOUS (relation: relates_to) - confidence is low._
- **What is the exact relationship between `SST-4766 MSL upload failure analysis (not a Lambda issue)` and `SST-4995 XSS escape user-controlled text in produced HTML`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `SST-5778 numbering start reset (w:start ignored)` connect `List/Subsection Numbering Reconstruction` to `Repo Conventions & Extractor Core`, `HTML Formatting & Escaping`, `Letter-End Markers`, `Letter-End & Title Predicates`, `Run-in Provision Detection (STB)`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `SST-4940 letter-end structural look-ahead disambiguator` connect `Letter-End & Title Predicates` to `HTML Formatting & Escaping`, `Letter-End Markers`, `Repo Conventions & Extractor Core`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `SST-5623 soft-body letter-end truncation` connect `Letter-End & Title Predicates` to `Repo Conventions & Extractor Core`, `Config Externalization & Architecture`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **What connects `SST-5610 narrative structural boundaries`, `SST-5069 continuation-table role inheritance`, `SST-4869 same-style run-boundary span merger` to the rest of the system?**
  _188 weakly-connected nodes found - possible documentation gaps or missing edges._