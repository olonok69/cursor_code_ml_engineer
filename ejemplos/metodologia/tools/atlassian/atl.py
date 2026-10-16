#!/usr/bin/env python3
"""Read-only Atlassian (Jira + Confluence) client and CLI.

There is exactly one network function, Client._get, and it only sends GET. Adding any write is a deliberate code
change, not a flag. Credentials come from ~/.config/<org>/jira.env (chmod 600; override the path with
ATLASSIAN_ENV_FILE) and are never printed.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path(os.environ.get("ATLASSIAN_ENV_FILE", Path.home() / ".config" / "<org>" / "jira.env"))
REQUIRED = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
FIELDS = "summary,status,issuetype,resolution,assignee,parent,issuelinks,subtasks"
MIN_INTERVAL = 0.25
BATCH = 50


class CredentialsError(Exception):
    pass


class HttpError(Exception):
    def __init__(self, status: int, path: str):
        super().__init__(f"HTTP {status} on {path}")
        self.status, self.path = status, path


class NotFound(HttpError):
    pass


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        raise CredentialsError(f"missing {path}")
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.removeprefix("export ").split("=", 1)
        env[k.strip()] = v.strip().strip("'\"")
    missing = [k for k in REQUIRED if not env.get(k)]
    if missing:
        raise CredentialsError("missing " + ", ".join(missing))
    env["JIRA_BASE_URL"] = env["JIRA_BASE_URL"].rstrip("/")
    return {k: env[k] for k in REQUIRED}


class Client:
    def __init__(self, env: dict[str, str], opener=urllib.request.urlopen):
        self._base = env["JIRA_BASE_URL"]
        self._auth = "Basic " + base64.b64encode(f'{env["JIRA_EMAIL"]}:{env["JIRA_API_TOKEN"]}'.encode()).decode()
        self._open = opener
        self._last = 0.0

    def _get(self, path: str, params: dict | None = None, accept: str = "application/json") -> tuple[int, bytes]:
        wait = MIN_INTERVAL - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        url = self._base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(url, method="GET", headers={"Authorization": self._auth, "Accept": accept})
        try:
            with self._open(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def get_json(self, path: str, params: dict | None = None) -> dict:
        status, body = self._get(path, params)
        if status == 404:
            raise NotFound(status, path)
        if status != 200:
            raise HttpError(status, path)
        return json.loads(body)

    def issue(self, key: str, fields: str = FIELDS) -> dict:
        return self.get_json(f"/rest/api/3/issue/{key}", {"fields": fields})

    def search(self, keys: list[str], fields: str = FIELDS) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for i in range(0, len(keys), BATCH):
            batch = keys[i:i + BATCH]
            try:
                token = None
                while True:
                    q = {"jql": f"key in ({','.join(batch)})", "fields": fields, "maxResults": "100"}
                    if token:
                        q["nextPageToken"] = token
                    d = self.get_json("/rest/api/3/search/jql", q)
                    for iss in d.get("issues", []):
                        out[iss["key"]] = iss
                    token = d.get("nextPageToken")
                    if not token or d.get("isLast"):
                        break
            except HttpError as e:
                if e.status != 400:
                    raise
            for k in batch:  # unknown/moved keys fail the whole JQL batch: read them singly
                if k in out:
                    continue
                try:
                    iss = self.issue(k, fields)
                except NotFound:
                    continue
                out[k] = iss
                out[iss["key"]] = iss
        return out

    def issue_xml(self, key: str) -> bytes:
        status, body = self._get(f"/si/jira.issueviews:issue-xml/{key}/{key}.xml",
                                 accept="application/xml,text/xml,*/*")
        if status != 200:
            raise (NotFound if status == 404 else HttpError)(status, key)
        return body

    def comments(self, key: str) -> list[dict]:
        return self.get_json(f"/rest/api/3/issue/{key}/comment", {"maxResults": "100"}).get("comments", [])

    def confluence_page(self, page_id: str, body: bool = False) -> dict:
        params = {"body-format": "storage"} if body else None
        return self.get_json(f"/wiki/api/v2/pages/{page_id}", params)

    def confluence_search(self, cql: str, limit: int = 25) -> list[dict]:
        return self.get_json("/wiki/rest/api/search", {"cql": cql, "limit": str(limit)}).get("results", [])


def _adf_text(node) -> str:
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        sep = "\n" if node.get("type") in ("paragraph", "heading", "listItem") else ""
        return "".join(_adf_text(c) for c in node.get("content", [])) + sep
    if isinstance(node, list):
        return "".join(_adf_text(c) for c in node)
    return ""


def link_lines(iss: dict) -> list[str]:
    f = iss.get("fields", {})
    out = []
    for l in f.get("issuelinks", []):
        if "outwardIssue" in l:
            out.append(f'{l["type"]["outward"]}: {l["outwardIssue"]["key"]}')
        else:
            out.append(f'{l["type"]["inward"]}: {l["inwardIssue"]["key"]}')
    if f.get("parent"):
        out.append(f'parent: {f["parent"]["key"]}')
    out += [f'subtask: {s["key"]}' for s in f.get("subtasks", [])]
    return out


def _strip_html(s: str) -> str:
    s = re.sub(r"<(br|/p|/h\d|/li|/tr)[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return "\n".join(l.strip() for l in html.unescape(s).splitlines() if l.strip())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="atl.py", description="Read-only Jira/Confluence CLI")
    ap.add_argument("--json", action="store_true", help="raw JSON output")
    sub = ap.add_subparsers(dest="app", required=True)
    j = sub.add_parser("jira").add_subparsers(dest="cmd", required=True)
    j.add_parser("issue").add_argument("key")
    s = j.add_parser("search"); s.add_argument("jql"); s.add_argument("--fields", default=FIELDS)
    j.add_parser("links").add_argument("key")
    c = j.add_parser("comments"); c.add_argument("key"); c.add_argument("--last", type=int, default=5)
    x = j.add_parser("xml"); x.add_argument("key"); x.add_argument("--out", type=Path)
    cf = sub.add_parser("confluence").add_subparsers(dest="cmd", required=True)
    cf.add_parser("search").add_argument("cql")
    p = cf.add_parser("page"); p.add_argument("page_id"); p.add_argument("--body", action="store_true")
    d = cf.add_parser("diff"); d.add_argument("local", type=Path); d.add_argument("page_id")
    a = ap.parse_args(argv)
    try:
        cl = Client(load_env())
        if a.app == "jira" and a.cmd == "issue":
            iss = cl.issue(a.key)
            if a.json:
                print(json.dumps(iss, indent=1)); return 0
            f = iss["fields"]
            print(f'{iss["key"]} [{f["issuetype"]["name"]}] {f["status"]["name"]} — {f["summary"]}')
            print("assignee:", (f.get("assignee") or {}).get("displayName", "—"))
            for l in link_lines(iss):
                print("  " + l)
        elif a.app == "jira" and a.cmd == "search":
            d = cl.get_json("/rest/api/3/search/jql", {"jql": a.jql, "fields": a.fields, "maxResults": "100"})
            if a.json:
                print(json.dumps(d, indent=1)); return 0
            for iss in d.get("issues", []):
                f = iss["fields"]
                print(f'{iss["key"]}\t{f.get("status", {}).get("name", "")}\t{f.get("summary", "")}')
        elif a.app == "jira" and a.cmd == "links":
            print("\n".join(link_lines(cl.issue(a.key))))
        elif a.app == "jira" and a.cmd == "comments":
            for cm in cl.comments(a.key)[-a.last:]:
                print(f'--- {cm["author"]["displayName"]} {cm["created"][:16]}')
                print(_adf_text(cm["body"]).strip())
        elif a.app == "jira" and a.cmd == "xml":
            body = cl.issue_xml(a.key)
            if a.out:
                a.out.mkdir(parents=True, exist_ok=True)
                (a.out / f"{a.key}.xml").write_bytes(body)
                print(a.out / f"{a.key}.xml")
            else:
                sys.stdout.buffer.write(body)
        elif a.app == "confluence" and a.cmd == "search":
            for r in cl.confluence_search(a.cql):
                cnt = r.get("content", {})
                print(f'{cnt.get("id", "")}\t{cnt.get("type", "")}\t{r.get("title", "")}')
        elif a.app == "confluence" and a.cmd == "page":
            pg = cl.confluence_page(a.page_id, a.body)
            if a.json:
                print(json.dumps(pg, indent=1)); return 0
            print(f'{pg["id"]} v{pg["version"]["number"]} — {pg["title"]}')
            if a.body:
                print(_strip_html(pg["body"]["storage"]["value"]))
        elif a.app == "confluence" and a.cmd == "diff":
            pg = cl.confluence_page(a.page_id, True)
            remote = _strip_html(pg["body"]["storage"]["value"]).splitlines()
            raw = a.local.read_text(encoding="utf-8")
            local = (_strip_html(raw) if a.local.suffix in (".html", ".xhtml") else raw).splitlines()
            local = [l.strip() for l in local if l.strip()]
            diff = list(difflib.unified_diff(remote, local, f'confluence:{a.page_id}', str(a.local), lineterm=""))
            print("\n".join(diff) if diff else "identical (normalised text)")
        return 0
    except CredentialsError as e:
        print(f"atl: credentials: {e}", file=sys.stderr); return 2
    except NotFound as e:
        print(f"atl: {e}", file=sys.stderr); return 4
    except HttpError as e:
        print(f"atl: {e}", file=sys.stderr); return 3


if __name__ == "__main__":
    sys.exit(main())
