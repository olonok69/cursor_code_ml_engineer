import io
import json
import urllib.error

import pytest

from atlassian import atl
from atlassian import confluence_write as cw

atl.MIN_INTERVAL = 0
ENV = {"JIRA_BASE_URL": "https://example.atlassian.net", "JIRA_EMAIL": "a@b.c", "JIRA_API_TOKEN": "SECRET-TOKEN"}
ROOT, PAGE = "100", "200"
BODY_V3 = "<p>Old text</p>"
NEW = "<p>New text</p>"


class Resp(io.BytesIO):
    def __init__(self, status, body):
        super().__init__(body); self.status = status
    def __enter__(self): return self
    def __exit__(self, *a): return False


class FakeConfluence:
    """In-memory Confluence: one page under ROOT, version 3. Records every request."""
    def __init__(self, ancestors=(ROOT,), put_status=200, version=3):
        self.version, self.body, self.title = version, BODY_V3, "Page"
        self.ancestors, self.put_status, self.seen = list(ancestors), put_status, []

    def __call__(self, req, timeout=60):
        self.seen.append((req.get_method(), req.full_url, req.data))
        url, m = req.full_url, req.get_method()
        if m == "GET" and f"/pages/{PAGE}/ancestors" in url:
            return Resp(200, json.dumps({"results": [{"id": a} for a in self.ancestors]}).encode())
        if m == "GET" and f"/pages/{PAGE}" in url:
            return Resp(200, json.dumps({"id": PAGE, "title": self.title, "status": "current",
                                         "version": {"number": self.version},
                                         "body": {"storage": {"value": self.body}}}).encode())
        if m == "PUT" and url.endswith(f"/pages/{PAGE}"):
            if self.put_status != 200:
                raise urllib.error.HTTPError(url, self.put_status, "x", {}, io.BytesIO(b"{}"))
            d = json.loads(req.data)
            self.version, self.body = d["version"]["number"], d["body"]["value"]
            return Resp(200, b"{}")
        raise AssertionError(f"unexpected {m} {url}")


def writer(fake):
    return cw.Writer(ENV, opener=fake)


def test_plan_then_apply_writes_once_with_next_version(tmp_path):
    f = FakeConfluence(); w = writer(f)
    (tmp_path / "new.xhtml").write_text(NEW)
    plan = w.plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)
    assert plan["base_version"] == 3 and (tmp_path / f"{PAGE}.v3.xhtml").read_text() == BODY_V3  # backup
    res = w.apply(tmp_path / f"{PAGE}.plan.json", plan["token"])
    puts = [s for s in f.seen if s[0] == "PUT"]
    assert len(puts) == 1 and json.loads(puts[0][2])["version"]["number"] == 4
    assert res["version"] == 4 and f.body == NEW
    assert {s[0] for s in f.seen} <= {"GET", "PUT"}


def test_refuses_page_outside_allowed_tree(tmp_path):
    f = FakeConfluence(ancestors=("999",)); (tmp_path / "new.xhtml").write_text(NEW)
    with pytest.raises(cw.Refused, match="not under"):
        writer(f).plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)


def test_refuses_wrong_token(tmp_path):
    f = FakeConfluence(); w = writer(f); (tmp_path / "new.xhtml").write_text(NEW)
    w.plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)
    with pytest.raises(cw.Refused, match="token"):
        w.apply(tmp_path / f"{PAGE}.plan.json", "wrong")
    assert not [s for s in f.seen if s[0] == "PUT"]


def test_refuses_when_page_changed_since_plan(tmp_path):
    f = FakeConfluence(); w = writer(f); (tmp_path / "new.xhtml").write_text(NEW)
    plan = w.plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)
    f.version = 4  # someone edited it on Confluence meanwhile
    with pytest.raises(cw.Refused, match="changed since the plan"):
        w.apply(tmp_path / f"{PAGE}.plan.json", plan["token"])
    assert not [s for s in f.seen if s[0] == "PUT"]


def test_refuses_if_body_file_edited_after_plan(tmp_path):
    f = FakeConfluence(); w = writer(f); (tmp_path / "new.xhtml").write_text(NEW)
    plan = w.plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)
    (tmp_path / "new.xhtml").write_text("<p>sneaky</p>")
    with pytest.raises(cw.Refused, match="changed after the plan"):
        w.apply(tmp_path / f"{PAGE}.plan.json", plan["token"])


def test_refuses_malformed_storage_xhtml(tmp_path):
    f = FakeConfluence(); (tmp_path / "new.xhtml").write_text("<p>unclosed")
    with pytest.raises(cw.Refused, match="well-formed"):
        writer(f).plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)


def test_accepts_confluence_macros_namespaces(tmp_path):
    f = FakeConfluence()
    (tmp_path / "new.xhtml").write_text('<ac:structured-macro ac:name="info"><ac:rich-text-body><p>x</p>'
                                        '</ac:rich-text-body></ac:structured-macro><p><ri:page ri:content-title="T"/></p>')
    assert writer(f).plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)["base_version"] == 3


def test_conflict_409_is_reported_not_retried(tmp_path):
    f = FakeConfluence(put_status=409); w = writer(f); (tmp_path / "new.xhtml").write_text(NEW)
    plan = w.plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)
    with pytest.raises(atl.HttpError) as e:
        w.apply(tmp_path / f"{PAGE}.plan.json", plan["token"])
    assert e.value.status == 409 and len([s for s in f.seen if s[0] == "PUT"]) == 1


def test_no_op_plan_refused(tmp_path):
    f = FakeConfluence(); (tmp_path / "new.xhtml").write_text(BODY_V3)
    with pytest.raises(cw.Refused, match="identical"):
        writer(f).plan(PAGE, tmp_path / "new.xhtml", ROOT, tmp_path)


def test_module_has_no_create_delete_or_permission_paths():
    import inspect
    src = inspect.getsource(cw)
    for verb in ('"POST"', '"DELETE"', "restrictions", "/archive", "/content/"):
        assert verb not in src, verb


def test_visible_text_ignores_macro_parameter_order():
    a = ('<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">bash</ac:parameter>'
         '<ac:parameter ac:name="breakoutMode">wide</ac:parameter><ac:plain-text-body><![CDATA[ls]]></ac:plain-text-body>'
         '</ac:structured-macro><p>Text</p>')
    b = ('<ac:structured-macro ac:name="code"><ac:parameter ac:name="breakoutMode">wide</ac:parameter>'
         '<ac:parameter ac:name="language">bash</ac:parameter><ac:plain-text-body><![CDATA[ls]]></ac:plain-text-body>'
         '</ac:structured-macro><p>Text</p>')
    assert cw.visible_text(a) == cw.visible_text(b)
    assert cw.visible_text(a) != cw.visible_text(a.replace("<p>Text</p>", "<p>Other</p>"))
    assert cw.visible_text(a) != cw.visible_text(a.replace("[ls]", "[rm -rf]"))   # code-block content still counts
