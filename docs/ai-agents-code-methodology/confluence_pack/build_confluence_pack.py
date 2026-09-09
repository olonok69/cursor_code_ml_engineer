#!/usr/bin/env python3
"""Build the full Cursor Confluence pack: joiners + S3 + methodology.

Sources:
  confluence_pack/sources/*.md     — Cursor-adapted onboarding / shared record
  docs/.../TECHNICAL.md            — methodology sections
Emits:
  confluence_pack/html/            — paste into Confluence
  confluence_pack/xhtml/           — REST storage format

  python build_confluence_pack.py --self-test
  python build_confluence_pack.py
"""
import os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
# Repo root (…/cursor_code_ml_engineer); override with COURSE_REPO if needed
COURSE = os.environ.get(
    "COURSE_REPO",
    os.path.abspath(os.path.join(HERE, "..", "..", "..")),
)
SRC = os.path.join(HERE, "sources")
TECH = os.path.join(COURSE, "docs", "ai-agents-code-methodology", "TECHNICAL.md")

PAGE_TITLE_PREFIX = "Cursor — AI methodology"

# ---------------------------------------------------------------- markdown ---
_INLINE = [
    (re.compile(r"`([^`]+)`"),                lambda m: "<code>%s</code>" % html.escape(m.group(1))),
    (re.compile(r"\*\*([^*]+)\*\*"),          lambda m: "<strong>%s</strong>" % m.group(1)),
    (re.compile(r"(?<![*\w])\*([^*\n]+)\*"),  lambda m: "<em>%s</em>" % m.group(1)),
    (re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),  lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), m.group(1))),
]

def inline(text):
    out = html.escape(text)
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
    list_stack = []

    def close_lists(to_indent=-1):
        while list_stack and list_stack[-1][1] > to_indent:
            out.append("</%s>" % list_stack.pop()[0])

    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

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

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i+1].strip()):
            close_lists()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells); i += 1
            out.append(_table(rows, storage))
            continue

        if stripped.startswith(">"):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append("<blockquote>%s</blockquote>" % md_to_html("\n".join(buf), storage))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_lists()
            lvl = min(len(m.group(1)) + 1, 6)
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1; continue

        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            close_lists(); out.append("<hr/>"); i += 1; continue

        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", ln)
        if m:
            indent = len(m.group(1))
            tag = "ul" if m.group(2) in "-*+" else "ol"
            while list_stack and list_stack[-1][1] > indent:
                out.append("</%s>" % list_stack.pop()[0])
            if not list_stack or list_stack[-1][1] < indent:
                list_stack.append((tag, indent)); out.append("<%s>" % tag)
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

        close_lists()
        buf = [stripped]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*(#{1,6}\s|[-*+]\s|\d+\.\s|>|\||```|-{3,}$)", lines[i]):
            buf.append(lines[i].strip()); i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    close_lists()
    return "\n".join(out)

def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()

def sections(md):
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

# stem, short title, how to build body, index blurb
# kind: ("file", relative) | ("tech", [prefixes])
PAGES = [
    ("01-for-new-joiners", "For new joiners (Cursor)",
     ("file", "01-for-new-joiners.md"),
     "Second-person onboarding: Cursor Day 0, AWS access, shared-record setup, "
     "the five rules, confidentiality, and the work loop. Hand this to the new person."),
    ("02-onboarder", "Onboarder checklist (Cursor)",
     ("file", "02-onboarder.md"),
     "Your side of onboarding — IAM gate, Cursor posture, round-trip acceptance test, "
     "methodology adoption checks. Do not hand this to the joiner."),
    ("03-shared-record", "Shared record (S3 sync)",
     ("file", "03-shared-record.md"),
     "Bucket, roles, identity for Cursor (AGENTS.md → IDENTITY.md), daily pull/push, "
     "behavioural rules (30-day recovery, append-only, store wins), troubleshooting."),
    ("04-diagnose", "Diagnose before you spend",
     ("tech", ["0.", "1.", "2.", "3."]),
     "Contract-first triage, free deterministic oracle, canaries, provenance."),
    ("05-verify", "Verify: the layered test battery",
     ("tech", ["4.", "5."]),
     "Layered gates, RED-first, composition vs counts, deployed artifact + config."),
    ("06-context", "Context architecture",
     ("tech", ["6."]),
     "Lean AGENTS.md / rules; write-once; session continuity for the next Cursor chat."),
    ("07-human-gate", "Human gate, continuity, review, checklist",
     ("tech", ["8.", "9.", "Per-task checklist", "Technical anti-patterns"]),
     "One tool (Cursor): session continuity + human gate; sanitise; review loop; "
     "compressed checklist and anti-patterns."),
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
"""

def wrap_html(title, body, nav):
    return ("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
            "<title>%s</title><style>%s</style></head><body>\n"
            "<h1>%s</h1>\n%s\n%s\n</body></html>\n"
            % (html.escape(title), CSS, html.escape(title), nav, body))

def build():
    tech = read(TECH)
    secs = sections(tech)
    os.makedirs(os.path.join(OUT, "html"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "xhtml"), exist_ok=True)

    titles = {stem: "%s — %s" % (PAGE_TITLE_PREFIX, t) for stem, t, _k, _d in PAGES}
    index_title = "%s — adopt in Cursor" % PAGE_TITLE_PREFIX

    used = set()
    made = []
    for stem, short, kind, _desc in PAGES:
        if kind[0] == "file":
            md = read(os.path.join(SRC, kind[1]))
            n = 1
        else:
            chosen = []
            for head, body in secs:
                if any(head.startswith(p) for p in kind[1]):
                    chosen.append(body); used.add(head)
            md = "\n\n".join(chosen)
            n = len(chosen)
        nav_items = " · ".join(
            ('<a href="%s.html">%s</a>' % (s, t) if s != stem else "<strong>%s</strong>" % t)
            for s, t, _k, _d in PAGES)
        nav = '<div class="nav"><a href="00-index.html">Index</a> · %s</div>' % nav_items
        with open(os.path.join(OUT, "html", stem + ".html"), "w", encoding="utf-8") as fh:
            fh.write(wrap_html(titles[stem], md_to_html(md, False), nav))
        with open(os.path.join(OUT, "xhtml", stem + ".xhtml"), "w", encoding="utf-8") as fh:
            fh.write(md_to_html(md, True) + "\n")
        made.append((stem, titles[stem], n))

    unused = [h for h, _ in secs if h not in used]
    # §7 lives inside shared-record source — mark as intentionally covered
    unused = [h for h in unused if not h.startswith("7.")]

    idx = ["# " + index_title, "",
           "> **Joiners start here in Cursor.** Open `document-parser-lambda` in the "
           "Cursor IDE from day one so `AGENTS.md` and `.cursor/` load. Your lead also "
           "gives you `ils-s3-sync-YYYYMMDD.zip` for pull/push scripts — Confluence + zip + "
           "repo are one onboarding path, not alternatives.", "",
           "> These pages are **generated** — edit `confluence_pack/sources/*.md` and "
           "`TECHNICAL.md`, then regenerate; do not hand-edit the HTML.", "",
           "> **Upload order:** create this index as the **parent**, then each child below. "
           "After paste, re-point nav links to Confluence page titles (or use a children macro).", "",
           "| Page | Audience | What it covers |",
           "|---|---|---|"]
    for stem, short, _k, desc in PAGES:
        audience = "Joiner" if stem.startswith("01") else (
            "Onboarder" if stem.startswith("02") else (
            "Everyone" if stem.startswith("03") else "Everyone (playbook)"))
        idx.append("| **[%s](%s.html)** | %s | %s |" % (short, stem, audience, desc))
    idx += ["", "---", "",
            "## Joiner path (Cursor from day one)", "",
            "1. Read **For new joiners** — install Cursor, open the lambda repo.", "",
            "2. Get AWS access + **`ils-s3-sync-YYYYMMDD.zip`** from your lead; complete **Shared record** → `MACHINE READY`.", "",
            "3. Skim Diagnose → Verify → Context → Human gate; use the checklist on the last page.", "",
            "4. Onboarder (not you): runs the acceptance loop on **Onboarder checklist**.", "",
            "---", "",
            "## The one thing to take away", "",
            "A measurement can look entirely plausible and still be wrong. "
            "**Before you believe a check, prove it can fail** on a known-answer case."]
    with open(os.path.join(OUT, "html", "00-index.html"), "w", encoding="utf-8") as fh:
        fh.write(wrap_html(index_title, md_to_html("\n".join(idx)), ""))
    with open(os.path.join(OUT, "xhtml", "00-index.xhtml"), "w", encoding="utf-8") as fh:
        fh.write(md_to_html("\n".join(idx), True) + "\n")

    return made, unused, index_title

def self_test():
    ok = True
    def chk(name, cond):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name)
        ok = ok and cond
    h = md_to_html("**bold** and *it* and `c<d`")
    chk("bold/italic/code", "<strong>bold</strong>" in h and "<em>it</em>" in h)
    chk("code escaped", "<code>c&lt;d</code>" in h)
    chk("neg asterisks", "*" not in h)
    h = md_to_html("| a | b |\n|---|---|\n| 1 | 2 |")
    chk("table", "<th>a</th>" in h and "<td>2</td>" in h)
    h = md_to_html("```py\nx = 1\n```")
    chk("code html", "<pre class=\"code\">" in h)
    s = md_to_html("```py\nx = 1\n```", True)
    chk("code storage", 'ac:name="code"' in s)
    h = md_to_html("- one\n- two")
    chk("list", h.count("<li>") == 2)
    h = md_to_html("> quoted **x**")
    chk("blockquote", "<blockquote>" in h and "<strong>x</strong>" in h)
    h = md_to_html("## Heading")
    chk("heading demote", "<h3>Heading</h3>" in h)
    chk("run-on para", md_to_html("a\nb\nc").count("<p>") == 1)
    src = "\n\n".join("para %d" % n for n in range(50))
    chk("no drop", md_to_html(src).count("<p>") == 50)
    chk("neg drop", md_to_html("\n\n".join(src.split("\n\n")[:49])).count("<p>") != 50)
    rendered = md_to_html(src)
    chk("text survives", all(("para %d" % n) in rendered for n in range(50)))
    return ok

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("converter self-test:")
        sys.exit(0 if self_test() else 1)
    made, unused, _ = build()
    print("built %d pages + index in %s" % (len(made), OUT))
    for stem, title, n in made:
        print("  %-22s %s  (%s)" % (stem, title, n))
    if unused:
        print("\n!! TECH SECTIONS NOT ON ANY PAGE:")
        for u in unused:
            print("   -", u)
        sys.exit(2)
    print("\nall technical sections accounted for (incl. §7 via shared-record source)")
