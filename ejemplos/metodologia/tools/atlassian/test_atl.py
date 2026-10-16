import io, json, urllib.error
import pytest
from atlassian import atl

atl.MIN_INTERVAL = 0  # no rate-limit sleeps in tests

ENV = {"JIRA_BASE_URL": "https://example.atlassian.net", "JIRA_EMAIL": "a@b.c", "JIRA_API_TOKEN": "SECRET-TOKEN"}


class FakeResp(io.BytesIO):
    def __init__(self, status, body):
        super().__init__(body); self.status = status
    def __enter__(self): return self
    def __exit__(self, *a): return False


def make_opener(routes, seen):
    def opener(req, timeout=60):
        seen.append(req)
        for frag, (status, body) in routes.items():
            if frag in req.full_url:
                if status != 200:
                    raise urllib.error.HTTPError(req.full_url, status, "x", {}, io.BytesIO(body))
                return FakeResp(status, body)
        raise AssertionError("unrouted " + req.full_url)
    return opener


def test_only_get_is_ever_sent():
    seen = []
    c = atl.Client(ENV, opener=make_opener({"/myself": (200, b"{}")}, seen))
    c.get_json("/rest/api/3/myself")
    assert [r.get_method() for r in seen] == ["GET"]
    assert not any(hasattr(c, n) for n in ("post", "put", "delete", "_post", "_put", "_request"))


def test_token_never_in_error_text():
    seen = []
    c = atl.Client(ENV, opener=make_opener({"/x": (500, b"boom")}, seen))
    with pytest.raises(atl.HttpError) as e:
        c.get_json("/x")
    assert "SECRET-TOKEN" not in str(e.value) and "500" in str(e.value)


def test_load_env_missing_var(tmp_path):
    p = tmp_path / "jira.env"; p.write_text("JIRA_BASE_URL=https://x\nJIRA_EMAIL=a@b.c\n")
    with pytest.raises(atl.CredentialsError):
        atl.load_env(p)


def test_load_env_parses_quotes_and_export(tmp_path):
    p = tmp_path / "jira.env"
    p.write_text('export JIRA_BASE_URL="https://x/"\nJIRA_EMAIL=a@b.c\nJIRA_API_TOKEN=\'t\'\n# c\n')
    assert atl.load_env(p) == {"JIRA_BASE_URL": "https://x", "JIRA_EMAIL": "a@b.c", "JIRA_API_TOKEN": "t"}


def test_search_falls_back_to_single_reads():
    moved = {"key": "PROJ-9", "fields": {"summary": "m"}}
    routes = {"/search/jql": (400, b'{"errorMessages":["An issue with key PROJ-1 does not exist"]}'),
              "/issue/PROJ-1?": (200, json.dumps(moved).encode()),
              "/issue/PROJ-2?": (200, json.dumps({"key": "PROJ-2", "fields": {}}).encode())}
    c = atl.Client(ENV, opener=make_opener(routes, []))
    out = c.search(["PROJ-1", "PROJ-2"])
    assert out["PROJ-1"]["key"] == "PROJ-9" and out["PROJ-9"]["key"] == "PROJ-9" and "PROJ-2" in out


def test_search_batches_of_50():
    seen = []
    body = json.dumps({"issues": [], "isLast": True}).encode()
    c = atl.Client(ENV, opener=make_opener({"/search/jql": (200, body), "/issue/": (404, b"{}")}, seen))
    c.search([f"PROJ-{i}" for i in range(120)])
    assert sum("/search/jql" in r.full_url for r in seen) == 3
