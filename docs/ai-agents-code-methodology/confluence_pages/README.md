# Cursor AI-agent methodology — Confluence page-set

**Generated** by `../build_confluence_pages.py`. **Do not hand-edit these files** —
edit the source and regenerate, or the next build silently reverts your change.

## Source of truth

This **Cursor** course repository:

| Page content | Source file |
|---|---|
| §0–§9, checklist, anti-patterns | `docs/ai-agents-code-methodology/TECHNICAL.md` |
| The operating package on page 04 | `docs/synchro/s3-sync/README.md` |

Company standard assumed throughout: **Cursor** is the coding agent. There is no
Claude-Code→Cursor (or other product-to-product) handoff — page 05 reframes
“handoff” as **session continuity** + **human gate on outward actions**.

Regenerate from `docs/ai-agents-code-methodology/`:

```bash
python build_confluence_pages.py --self-test   # 13 checks, each with a negative case
python build_confluence_pages.py
```

Override the repo root with `COURSE_REPO=...` only if you must.

## Structure — one parent, five children

| Browser page (paste) | Storage format (REST) | Page title |
|---|---|---|
| `html/00-index.html` | `xhtml/00-index.xhtml` | Cursor AI-agent methodology — the technical playbook |
| `html/01-diagnose.html` | `xhtml/01-diagnose.xhtml` | Cursor AI-agent methodology — Diagnose before you spend |
| `html/02-verify.html` | `xhtml/02-verify.xhtml` | Cursor AI-agent methodology — Verify: the layered test battery |
| `html/03-context.html` | `xhtml/03-context.xhtml` | Cursor AI-agent methodology — Context architecture |
| `html/04-shared-record.html` | `xhtml/04-shared-record.xhtml` | Cursor AI-agent methodology — Sharing the trail across machines and people |
| `html/05-handoff.html` | `xhtml/05-handoff.xhtml` | Cursor AI-agent methodology — Human gate, continuity, review, checklist |

Publish the index as the **parent**, the other five as its **children**.

## RECOMMENDED — copy-paste (browser + page edit rights only)

No API token needed. Confluence Cloud's editor ingests pasted HTML.

1. Open `html/00-index.html` in a browser, select all (Ctrl/Cmd-A), copy. In Confluence,
   **Create** a page, click in the body, paste. Title it from the table above.
2. For each of `html/01-…` … `html/05-…`: create a **child** page of the index and paste the
   same way. Headings, tables, code blocks and blockquotes all survive.
3. **Fix the navigation links.** The files link to each other by filename
   (`01-diagnose.html`), which means nothing inside Confluence. Once all six pages exist,
   re-point the links in the index table and each page's nav strip (type `[` + the page
   title). Alternatively delete the nav strips and put a `children` macro on the index.

## Alternative — REST API (needs a token)

For each `xhtml/` page: `POST /wiki/rest/api/content` with the file contents as
`body.storage.value` and `representation: storage`. No attachments — these pages carry no
images, so there is no second upload step and cross-page links resolve by title.

## What is deliberately NOT here

- **No client names, no ticket IDs.** Re-check after any regeneration.
- **No images.** The one diagram lives in the course deck.
- **Spanish course guides** (`GUIA_TECNICA.md`, `GUIA_PRESENTACION.md`) are training
  talk-track, not this company reference pack.
- **No Claude Code surface.** Orientation is `AGENTS.md` + `.cursor/rules`; skills and
  hooks are Cursor’s. Sibling Copilot notes stay in `COPILOT_ADAPTATION.md` only.

## Cursor surface (quick map)

| Role | Where |
|---|---|
| Always-on orientation | `AGENTS.md`, `.cursor/rules/*.mdc` |
| On-demand detail | `data/changes/**` |
| Sanitise / kg skills | `.cursor/skills/` |
| Hard gates | `.cursor/hooks.json` |
| Machine role (shared trail) | machine-local `IDENTITY.md` (gitignored) |

## s3-sync status

`docs/synchro/s3-sync/README.md` is **Cursor-adapted**: behavioural rules (recovery
expiry, append-only ledgers, shared store wins), authored-inside-derived, and
`AGENTS.md` / `.cursor/rules` for identity — no dual Claude pointer. Travel/bring-up
docs under `docs/synchro/machine-sync/` may still describe older Claude laptop
bundles; they are a separate transport story, not this Confluence pack.
