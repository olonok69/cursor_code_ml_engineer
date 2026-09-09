# Cursor Confluence pack — adopt AI methodology + S3 shared record

**Generated** by `build_confluence_pack.py`. **Do not hand-edit** `html/` or `xhtml/` —
edit `sources/*.md` or `../TECHNICAL.md`, then regenerate.

```bash
cd docs/ai-agents-code-methodology/confluence_pack
python build_confluence_pack.py --self-test
python build_confluence_pack.py
```

## What this pack is

Company-facing Confluence pages for **Cursor-first** adoption:

| # | File | Audience | Role |
|---|---|---|---|
| 00 | `html/00-index.html` | Everyone | **Parent** page |
| 01 | `html/01-for-new-joiners.html` | **New joiner** | Hand them this |
| 02 | `html/02-onboarder.html` | **You (onboarder)** | Keep for yourself |
| 03 | `html/03-shared-record.html` | Everyone | S3 sync / IDENTITY / rules |
| 04–06 | diagnose / verify / context | Everyone | Methodology playbook |
| 07 | `html/07-human-gate.html` | Everyone | Human gate + checklist |

Titles all start with **`Cursor — AI methodology — …`**.

## How to upload (recommended: paste)

1. Open `html/00-index.html` in a browser → Select all → Copy.
2. Confluence → Create page → paste → title from the `<h1>` / table below.
3. Create each of `01`…`07` as a **child** of the index; paste the same way.
4. Re-point nav links to Confluence page titles (type `[` + title), or drop nav
   strips and add a **Children** macro on the index.

Alternative: POST each `xhtml/*.xhtml` as `body.storage.value` via REST.

## Suggested Confluence titles

| File | Title |
|---|---|
| 00-index | Cursor — AI methodology — adopt in Cursor |
| 01-for-new-joiners | Cursor — AI methodology — For new joiners (Cursor) |
| 02-onboarder | Cursor — AI methodology — Onboarder checklist (Cursor) |
| 03-shared-record | Cursor — AI methodology — Shared record (S3 sync) |
| 04-diagnose | Cursor — AI methodology — Diagnose before you spend |
| 05-verify | Cursor — AI methodology — Verify: the layered test battery |
| 06-context | Cursor — AI methodology — Context architecture |
| 07-human-gate | Cursor — AI methodology — Human gate, continuity, review, checklist |

## What else to complete the pack (outside this HTML)

Do these in the **product repo** (`document-parser-lambda`) so Cursor sessions actually load the rails — Confluence alone is not enough:

| Gap | Action |
|---|---|
| No lean `AGENTS.md` | Add one: points at `IDENTITY.md`, `data/changes/STATUS.md`, contract (`get-sl-upload-status`), human gate, Cursor > Claude |
| Thin `.cursor/rules` | Add methodology-core + gates (canary, machine role, append-only) — copy from `docs/ai-agents-code-methodology/cursor/rules/` |
| `kg` / `sanitise-diff` skills | Install project skills under `.cursor/skills/` so joiners’ Cursor matches the docs |
| `IDENTITY.md` pointer | After `./identity.sh --write`, ensure `AGENTS.md` links the machine-local file |
| Ops zip | Keep distributing `ils-s3-sync-YYYYMMDD.zip` for scripts/`mount-s3.deb` — Confluence does not replace the package |
| Publisher / go-live | Leave `PUBLISHER_RUNBOOK.md` + `GO_LIVE_CHECKLIST.md` in the zip (publisher-only); link from Confluence if useful |
| Old Claude Confluence | If you already published the Claude-sourced playbook, **replace or clearly supersede** it with this pack (page 04 there still said Claude Code / `CLAUDE.md`) |

## Audience split (do not mix)

- **Joiner reads:** 00 index → **01** → **03** → skim 04–07  
- **Onboarder reads:** 00 → **02** → **03** → runs acceptance on 02  
- **Everyone keeps:** 03 shared record + 07 checklist

## Notes

- Operational ILS details (account, bucket, SSO URL) are intentional for internal
  Confluence. Do not publish this pack to a public course site without sanitising.
- Sources for 01–03: `sources/`. Methodology 04–07: generated from `TECHNICAL.md`.
- Older generated set under `../confluence_pages/` is methodology-only; **prefer this pack** for company upload.
