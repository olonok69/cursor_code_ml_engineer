#!/usr/bin/env python3
"""Update ONE existing Confluence page, safely. The only write path in tools/atlassian/.

    python3 confluence_write.py pull  PAGE_ID [--out DIR]                       # save the live body to edit
    python3 confluence_write.py plan  PAGE_ID NEW_BODY.xhtml --root ROOT_ID     # backup + diff + confirm token
    python3 confluence_write.py apply DIR/PAGE_ID.plan.json --confirm TOKEN     # write, then read back

Guarantees (each one is tested):
- updates only: there is no create, delete, archive, move or permission path in this module;
- only pages at or under --root (ancestry read from Confluence, not trusted from the caller);
- the live body is backed up before anything else, and the diff is shown before any write;
- apply refuses unless the token printed by plan is given back, the body file is byte-identical to the planned one,
  and the live page is still at the planned version (an edit made on Confluence meanwhile is never overwritten);
- the write sends version N+1, so Confluence itself rejects a concurrent edit (409) — reported, never retried;
- after the write the page is read back and compared with what was sent.
Credentials: the same jira.env as atl.py, via atl.load_env(); never printed.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from atlassian import atl  # noqa: E402

DEFAULT_OUT = Path.home() / ".cache" / "confluence-write"
_NS = 'xmlns:ac="http://atlassian.com/content" xmlns:ri="http://atlassian.com/resource/identifier"'


class Refused(Exception):
    pass


def visible_text(body: str) -> str:
    """What a reader sees, for diffs and the read-back check.

    Macro settings (<ac:parameter>) are dropped: Confluence re-orders them on save, which made a correct write read
    back as a mismatch (measured on the first real write). Code-block contents (CDATA) are KEPT — a plain tag strip deletes them, so a
    change inside a code block would have gone unnoticed.
    """
    import re
    body = re.sub(r"<ac:parameter\b[^>]*>.*?</ac:parameter>", "", body, flags=re.S)
    body = re.sub(r"<!\[CDATA\[(.*?)\]\]>", lambda m: m.group(1).replace("<", "&lt;").replace(">", "&gt;"), body, flags=re.S)
    return atl._strip_html(body)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_storage_xhtml(body: str) -> None:
    """Storage format is XML with ac:/ri: prefixes and HTML entities; refuse anything that does not parse."""
    import html.entities
    ents = "".join(f'<!ENTITY {n} "&#{c};">' for n, c in html.entities.name2codepoint.items()
                   if n not in ("amp", "lt", "gt", "quot", "apos"))
    doc = f'<!DOCTYPE r [{ents}]><r {_NS}>{body}</r>'
    try:
        ET.fromstring(doc)
    except ET.ParseError as e:
        raise Refused(f"new body is not well-formed storage XHTML: {e}") from None


class Writer:
    def __init__(self, env: dict[str, str], opener=urllib.request.urlopen):
        self.reader = atl.Client(env, opener=opener)
        self._open = opener
        self._base = env["JIRA_BASE_URL"].rstrip("/")
        self._auth = self.reader._auth

    # -- reads (via the GET-only client) --
    def live(self, page_id: str) -> dict:
        p = self.reader.confluence_page(page_id, body=True)
        return {"id": p["id"], "title": p["title"], "version": p["version"]["number"],
                "body": p["body"]["storage"]["value"]}

    def under_root(self, page_id: str, root: str) -> bool:
        if page_id == root:
            return True
        anc = self.reader.get_json(f"/wiki/api/v2/pages/{page_id}/ancestors", {"limit": "250"})
        return root in {a["id"] for a in anc.get("results", [])}

    # -- the single write --
    def _put_page(self, page_id: str, payload: dict) -> None:
        req = urllib.request.Request(self._base + f"/wiki/api/v2/pages/{page_id}", method="PUT",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Authorization": self._auth, "Accept": "application/json",
                                              "Content-Type": "application/json"})
        try:
            with self._open(req, timeout=60) as r:
                r.read()
        except urllib.error.HTTPError as e:
            raise atl.HttpError(e.code, f"PUT /wiki/api/v2/pages/{page_id}") from None

    # -- workflow --
    def pull(self, page_id: str, out: Path) -> Path:
        p = self.live(page_id)
        out.mkdir(parents=True, exist_ok=True)
        f = out / f"{page_id}.v{p['version']}.xhtml"
        f.write_text(p["body"], encoding="utf-8")
        return f

    def plan(self, page_id: str, new_file: Path, root: str, out: Path) -> dict:
        new = Path(new_file).read_text(encoding="utf-8")
        check_storage_xhtml(new)
        if not self.under_root(page_id, root):
            raise Refused(f"page {page_id} is not under the allowed root {root}")
        p = self.live(page_id)
        if p["body"] == new:
            raise Refused("new body is identical to the live page — nothing to do")
        out.mkdir(parents=True, exist_ok=True)
        backup = out / f"{page_id}.v{p['version']}.xhtml"
        backup.write_text(p["body"], encoding="utf-8")
        token = _sha(f"{page_id}:{p['version']}:{_sha(new)}")[:10]
        plan = {"page_id": page_id, "title": p["title"], "root": root, "base_version": p["version"],
                "new_file": str(Path(new_file).resolve()), "new_sha256": _sha(new), "backup": str(backup),
                "token": token}
        (out / f"{page_id}.plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
        plan["diff"] = "\n".join(difflib.unified_diff(
            visible_text(p["body"]).splitlines(), visible_text(new).splitlines(),
            f"live v{p['version']}", "proposed", lineterm=""))
        return plan

    def apply(self, plan_file: Path, token: str, message: str = "") -> dict:
        plan = json.loads(Path(plan_file).read_text(encoding="utf-8"))
        if token != plan["token"]:
            raise Refused("confirmation token does not match the plan — run plan again and read its diff")
        new = Path(plan["new_file"]).read_text(encoding="utf-8")
        if _sha(new) != plan["new_sha256"]:
            raise Refused("the body file changed after the plan — run plan again")
        if not self.under_root(plan["page_id"], plan["root"]):
            raise Refused(f"page {plan['page_id']} is not under the allowed root {plan['root']}")
        p = self.live(plan["page_id"])
        if p["version"] != plan["base_version"]:
            raise Refused(f"page changed since the plan (v{plan['base_version']} → v{p['version']}) — "
                          "someone edited it on Confluence; pull, re-apply your change, plan again")
        payload = {"id": plan["page_id"], "status": "current", "title": p["title"],
                   "body": {"representation": "storage", "value": new},
                   "version": {"number": plan["base_version"] + 1, "message": message or "updated via review"}}
        self._put_page(plan["page_id"], payload)
        after = self.live(plan["page_id"])
        same = visible_text(after["body"]) == visible_text(new)
        return {"page_id": plan["page_id"], "version": after["version"], "text_matches": same,
                "backup": plan["backup"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="confluence_write.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    pu = sub.add_parser("pull"); pu.add_argument("page_id"); pu.add_argument("--out", type=Path, default=DEFAULT_OUT)
    pl = sub.add_parser("plan"); pl.add_argument("page_id"); pl.add_argument("new_body", type=Path)
    pl.add_argument("--root", required=True); pl.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap_ = sub.add_parser("apply"); ap_.add_argument("plan_file", type=Path); ap_.add_argument("--confirm", required=True)
    ap_.add_argument("--message", default="")
    a = ap.parse_args(argv)
    try:
        w = Writer(atl.load_env())
        if a.cmd == "pull":
            print(w.pull(a.page_id, a.out))
        elif a.cmd == "plan":
            p = w.plan(a.page_id, a.new_body, a.root, a.out)
            print(p["diff"] or "(markup-only change: text identical)")
            print(f"\npage {p['page_id']} '{p['title']}' at v{p['base_version']}; backup {p['backup']}")
            print(f"to write it:  confluence_write.py apply {a.out}/{p['page_id']}.plan.json --confirm {p['token']}")
        else:
            r = w.apply(a.plan_file, a.confirm, a.message)
            print(f"written: page {r['page_id']} now v{r['version']}; read-back text matches: {r['text_matches']}; "
                  f"backup {r['backup']}")
            return 0 if r["text_matches"] else 8
        return 0
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr); return 3
    except atl.CredentialsError as e:
        print(f"credentials: {e}", file=sys.stderr); return 2
    except atl.HttpError as e:
        hint = " (someone edited the page — pull and plan again)" if e.status == 409 else ""
        print(f"{e}{hint}", file=sys.stderr); return 4


if __name__ == "__main__":
    sys.exit(main())
