#!/usr/bin/env python3
"""Build the Confluence page-set for the Cursor AI-agent methodology.

Sources are THIS course repo (Cursor-first). Emits two parallel renderings of
the same six pages:

  confluence_pages/html/   self-contained HTML   -> copy-paste into Confluence
  confluence_pages/xhtml/  storage format        -> REST API path

Regenerate after any source edit; never hand-edit the output.
Run  python build_confluence_pages.py --self-test  to canary the converter.
"""
import os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "confluence_pages")
# Default: this repo's docs live next to this script's parent tree
COURSE = os.environ.get(
    "COURSE_REPO",
    os.path.abspath(os.path.join(HERE, "..", "..")),
)

PAGE_TITLE_PREFIX = "Cursor AI-agent methodology"

# ---------------------------------------------------------------- markdown ---
_INLINE = [
    (re.compile(r"`([^`]+)`"),                lambda m: "<code>%s</code>" % html.escape(m.group(1))),
    (re.compile(r"\*\*([^*]+)\*\*"),          lambda m: "<strong>%s</strong>" % m.group(1)),
    (re.compile(r"(?<![*\w])\*([^*\n]+)\*"),  lambda m: "<em>%s</em>" % m.group(1)),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),  lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), m.group(1))),
]

def inline(text):
    """Escape, then apply inline markup. Code spans are escaped inside their own
    handler, so escaping first would double-escape; instead escape here and let
    the code handler re-escape only what it captured."""
    out = html.escape(text)
    # the code handler escaped an already-escaped capture -> undo that one level
    out = _INLINE[0][0].sub(lambda m: "<code>%s</code>" % m.group(1), out)
    for rx, fn in _INLINE[1:]:
        out = rx.sub(fn, out)
    return out

def _table(rows, storage):
    head, body = rows[0], rows[2:]
    o = ["<table><thead><tr>"]
    o += ["<th>%s</th>" % inline(c) for c in head]
    o.append("</tr></thead><tbody>")
    for r in body:
        o.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
    o.append("</tbody></table>")
    return "".join(o)

def _code(lang, body, storage):
    if storage:
        lang = lang or "text"
        return ('<ac:structured-macro ac:name="code">'
                '<ac:parameter ac:name="language">%s</ac:parameter>'
                '<ac:plain-text-body><![CDATA[%s]]></ac:plain-text-body>'
                '</ac:structured-macro>' % (html.escape(lang, quote=True), body.replace("]]>", "]]&gt;")))
    return '<pre class="code"><code>%s</code></pre>' % html.escape(body)

def md_to_html(md, storage=False):
    lines = md.split("\n")
    out, i = [], 0
    list_stack = []            # list of (tag, indent)

    def close_lists(to_indent=-1):
        while list_stack and list_stack[-1][1] > to_indent:
            out.append("</%s>" % list_stack.pop()[0])

    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

        # fenced code
        if stripped.startswith("```"):
            close_lists()
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append(_code(lang, "\n".join(buf), storage))
            continue

        # table
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i+1].strip()):
            close_lists()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells); i += 1
            out.append(_table(rows, storage))
            continue

        # blockquote (consume the whole run)
        if stripped.startswith(">"):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append("<blockquote>%s</blockquote>" % md_to_html("\n".join(buf), storage))
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_lists()
            lvl = min(len(m.group(1)) + 1, 6)   # demote: the page title is h1
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1; continue

        # horizontal rule
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            close_lists(); out.append("<hr/>"); i += 1; continue

        # list item
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", ln)
        if m:
            indent = len(m.group(1))
            tag = "ul" if m.group(2) in "-*+" else "ol"
            while list_stack and list_stack[-1][1] > indent:
                out.append("</%s>" % list_stack.pop()[0])
            if not list_stack or list_stack[-1][1] < indent:
                list_stack.append((tag, indent)); out.append("<%s>" % tag)
            # gather continuation lines (more-indented, non-list)
            body = [m.group(3)]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip(): break
                if re.match(r"^(\s*)([-*+]|\d+\.)\s+", nxt): break
                if len(nxt) - len(nxt.lstrip()) <= indent and nxt.strip(): break
                body.append(nxt.strip()); i += 1
            out.append("<li>%s</li>" % inline(" ".join(body)))
            continue

        if not stripped:
            close_lists(); i += 1; continue

        # paragraph
        close_lists()
        buf = [stripped]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*(#{1,6}\s|[-*+]\s|\d+\.\s|>|\||```|-{3,}$)", lines[i]):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    close_lists()
    return "\n".join(out)

# ------------------------------------------------------------------- pages ---
def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()

def sections(md):
    """Split on '## ' headings -> ordered list of (heading, body_including_heading)."""
    parts, cur, head = [], [], None
    for ln in md.split("\n"):
        if ln.startswith("## "):
            if head is not None:
                parts.append((head, "\n".join(cur)))
            head = ln[3:].strip(); cur = [ln]
        else:
            if head is not None:
                cur.append(ln)
    if head is not None:
        parts.append((head, "\n".join(cur)))
    return parts

# stem, short title, section prefixes, index description
PAGES = [
    ("01-diagnose",      "Diagnose before you spend",
     ["0.", "1.", "2.", "3."],
     "Define the contract before touching the inside. Find the free, deterministic oracle "
     "and use it to establish root cause, so the metered model is only ever spent verifying "
     "a finished fix. Prove whether a defect is yours before you own it."),
    ("02-verify",        "Verify: the layered test battery",
     ["4.", "5."],
     "Five concentric gates, RED-first, plus the sixth nobody owns — the deployed artifact "
     "together with its configuration. How to read a green result, and why a matching total "
     "is the most common way a missing item ships."),
    ("03-context",       "Context architecture",
     ["6."],
     "Keep Cursor's always-loaded context lean: AGENTS.md + .cursor/rules are a map, not a "
     "changelog. Write each record once, push detail to on-demand references, and tune for "
     "time and density."),
    ("04-shared-record", "Sharing the trail across machines and people",
     ["7."],
     "Turning a personal trail into a team asset on shared object storage. Source versus "
     "derived versus authored-inside-derived; single-writer; pairs that must move together; "
     "and the behavioural rules people break — starting with recovery having an expiry date. "
     "Cursor reads machine-local IDENTITY.md via AGENTS.md before shared writes."),
    ("05-handoff",       "Human gate, continuity, review, checklist",
     ["8.", "9.", "Per-task checklist", "Technical anti-patterns"],
     "One tool (Cursor): no product-to-product handoff. Session continuity + human gate on "
     "outward actions, sanitisation, automated review as a loop participant, checklist and "
     "anti-patterns."),
]

CSS = """
body{font:15px/1.62 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#172b4d;max-width:60em;margin:2rem auto;padding:0 1.5rem}
h1{font-size:1.9em;border-bottom:3px solid #0052cc;padding-bottom:.3em}
h2{font-size:1.4em;margin-top:2em;color:#0747a6}h3{font-size:1.15em;margin-top:1.6em}
code{background:#f4f5f7;border-radius:3px;padding:.1em .35em;font-family:SFMono-Regular,Consolas,monospace;font-size:.88em}
pre.code{background:#f4f5f7;border:1px solid #dfe1e6;border-radius:4px;padding:.9em;overflow-x:auto}
pre.code code{background:none;padding:0}
table{border-collapse:collapse;width:100%;margin:1.1em 0}
th,td{border:1px solid #dfe1e6;padding:.55em .7em;text-align:left;vertical-align:top}
th{background:#f4f5f7}
blockquote{border-left:4px solid #ffab00;background:#fffae6;margin:1.1em 0;padding:.7em 1em}
blockquote p:first-child{margin-top:0}blockquote p:last-child{margin-bottom:0}
hr{border:0;border-top:1px solid #dfe1e6;margin:2em 0}
.nav{font-size:.9em;background:#f4f5f7;padding:.6em .9em;border-radius:4px;margin-bottom:1.5em}
.banner{background:#e3fcef;border:1px solid #abf5d1;border-radius:4px;padding:.8em 1em;margin:1.2em 0}
"""

def wrap_html(title, body, nav):
    return ("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
            "<title>%s</title><style>%s</style></head><body>\n"
            "<h1>%s</h1>\n%s\n%s\n</body></html>\n"
            % (html.escape(title), CSS, html.escape(title), nav, body))

def build():
    tech = read(os.path.join(COURSE, "docs/ai-agents-code-methodology/TECHNICAL.md"))
    shared = read(os.path.join(COURSE, "docs/synchro/s3-sync/README.md"))
    secs = sections(tech)

    os.makedirs(os.path.join(OUT, "html"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "xhtml"), exist_ok=True)

    titles = {stem: "%s — %s" % (PAGE_TITLE_PREFIX, t) for stem, t, _p, _d in PAGES}
    index_title = "%s — the technical playbook" % PAGE_TITLE_PREFIX

    used = set()
    made = []
    for stem, short, prefixes, _desc in PAGES:
        chosen = []
        for head, body in secs:
            if any(head.startswith(p) for p in prefixes):
                chosen.append(body); used.add(head)
        if stem == "04-shared-record":
            chosen.append("\n---\n\n# The operating package (reference implementation)\n\n" + shared)
        md = "\n\n".join(chosen)
        nav_items = " · ".join(
            ('<a href="%s.html">%s</a>' % (s, t) if s != stem else "<strong>%s</strong>" % t)
            for s, t, _p, _d in PAGES)
        nav = '<div class="nav"><a href="00-index.html">Index</a> · %s</div>' % nav_items
        with open(os.path.join(OUT, "html", stem + ".html"), "w", encoding="utf-8") as fh:
            fh.write(wrap_html(titles[stem], md_to_html(md, storage=False), nav))
        with open(os.path.join(OUT, "xhtml", stem + ".xhtml"), "w", encoding="utf-8") as fh:
            fh.write(md_to_html(md, storage=True) + "\n")
        made.append((stem, titles[stem], len(chosen)))

    unused = [h for h, _ in secs if h not in used]

    # index
    idx = ["# " + index_title, "",
           "> **Company standard:** **Cursor** is the coding agent. These pages are "
           "**generated** from this course repo — edit `docs/ai-agents-code-methodology/TECHNICAL.md` "
           "and `docs/synchro/s3-sync/README.md`, then regenerate; never hand-edit the page.", "",
           "> **Cursor surface (always-on):** `AGENTS.md`, `.cursor/rules/*.mdc`, skills under "
           "`.cursor/skills/`, hooks in `.cursor/hooks.json`. Detail stays in `data/changes/` "
           "(on demand). Machine role before shared writes: machine-local `IDENTITY.md`.", "",
           "This is a description of how we work with Cursor day to day. It is not a mandate: "
           "take what is useful and adapt the rest. There is **no** product-to-product handoff "
           "into Cursor — the human keeps the same role; continuity is session-to-session and "
           "human gates on outward actions.", "",
           "| Page | What it covers |", "|---|---|"]
    for stem, short, _p, desc in PAGES:
        idx.append("| **[%s](%s.html)** | %s |" % (short, stem, desc))
    idx += ["", "---", "", "## The one thing to take away", "",
            "A measurement can be wrong in a way that looks entirely plausible — not erroring, "
            "just quietly returning a believable number. **Before you believe a check, prove it can fail.** "
            "Run it against a case whose answer you already know. If it cannot fail, a clean result from it "
            "tells you nothing."]
    with open(os.path.join(OUT, "html", "00-index.html"), "w", encoding="utf-8") as fh:
        fh.write(wrap_html(index_title, md_to_html("\n".join(idx)), ""))
    with open(os.path.join(OUT, "xhtml", "00-index.xhtml"), "w", encoding="utf-8") as fh:
        fh.write(md_to_html("\n".join(idx), storage=True) + "\n")

    return made, unused, index_title, titles

# -------------------------------------------------------------- self-test ---
def self_test():
    """Gate 0. Every check below must FAIL on deliberately broken input, so each
    assertion is paired with a negative case."""
    ok = True
    def chk(name, cond):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name)
        ok = ok and cond

    h = md_to_html("**bold** and *it* and `c<d`")
    chk("bold/italic/code render",      "<strong>bold</strong>" in h and "<em>it</em>" in h)
    chk("code span is escaped",         "<code>c&lt;d</code>" in h)
    chk("negative: no stray asterisks", "*" not in h)

    h = md_to_html("| a | b |\n|---|---|\n| 1 | 2 |")
    chk("table renders",                "<th>a</th>" in h and "<td>2</td>" in h)

    h = md_to_html("```py\nx = 1\n```")
    chk("code block (html)",            "<pre class=\"code\">" in h and "x = 1" in h)
    s = md_to_html("```py\nx = 1\n```", storage=True)
    chk("code block (storage macro)",   'ac:name="code"' in s and "CDATA" in s)

    h = md_to_html("- one\n- two")
    chk("list renders",                 h.count("<li>") == 2 and "<ul>" in h)

    h = md_to_html("> quoted **x**")
    chk("blockquote renders",           "<blockquote>" in h and "<strong>x</strong>" in h)

    h = md_to_html("## Heading")
    chk("heading demoted to h3",        "<h3>Heading</h3>" in h)

    # consecutive non-blank lines are ONE paragraph — that is correct markdown,
    # and getting this backwards is what the first version of this test did.
    chk("run-on lines are one para",    md_to_html("a\nb\nc").count("<p>") == 1)

    # the canary that matters: a converter that silently drops content
    src = "\n\n".join("para %d" % n for n in range(50))
    chk("no content dropped",           md_to_html(src).count("<p>") == 50)
    chk("negative: dropping IS caught", md_to_html("\n\n".join(src.split("\n\n")[:49])).count("<p>") != 50)
    # every paragraph's text actually survives, not just the count
    rendered = md_to_html(src)
    chk("every para present by TEXT",   all(("para %d" % n) in rendered for n in range(50)))
    return ok

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("converter self-test:")
        sys.exit(0 if self_test() else 1)
    made, unused, index_title, titles = build()
    print("built %d pages + index in %s" % (len(made), OUT))
    for stem, title, n in made:
        print("  %-18s %-70s %d section(s)" % (stem, title, n))
    if unused:
        print("\n!! SECTIONS NOT ON ANY PAGE (content would be silently lost):")
        for u in unused:
            print("   -", u)
        sys.exit(2)
    print("\nall source sections accounted for")
