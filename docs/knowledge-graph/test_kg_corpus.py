import importlib.util, sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(mod):
    spec = importlib.util.spec_from_file_location(mod, _HERE / f"{mod}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[mod] = m
    spec.loader.exec_module(m)
    return m


def test_largest_md_skips_operational(tmp_path):
    bm = _load("build_manifest")
    (tmp_path / "sst-9999.md").write_text("x" * 10)              # small primary-style
    (tmp_path / "_handover_to_cursor.md").write_text("y" * 999)  # big but excluded
    (tmp_path / "qa_acceptance_criteria.md").write_text("z" * 999)
    (tmp_path / "_diag_probe.md").write_text("d" * 999)
    (tmp_path / "notes.md").write_text("n" * 50)                 # eligible, bigger than sst
    assert bm.largest_md(tmp_path).name == "notes.md"


def test_is_excluded_path_rejects_payload():
    bm = _load("build_manifest")
    assert bm.is_excluded_path(Path("/r/data/ils-to-main/payload/data/changes/STATUS.md"))
    assert not bm.is_excluded_path(Path("/r/data/changes/STATUS.md"))


def test_flat_name_groups():
    sc = _load("stage_corpus")
    P = Path
    assert sc.flat_name(P("/r/data/changes/sst-5468/sst-5468.md")) == "sst-5468__sst-5468.md"
    assert sc.flat_name(P("/r/data/changes/extractors/doc/process.md")) == "extractor__doc__process.md"
    assert sc.flat_name(P("/r/data/changes/STATUS.md")) == "hub__STATUS.md"
    assert sc.flat_name(P("/r/CLAUDE.md")) == "orient__CLAUDE.md"
    assert sc.flat_name(P("/r/data/docs/CODE_NAVIGATION.md")) == "orient__CODE_NAVIGATION.md"
    assert sc.flat_name(P("/r/data/machine-sync/RUNBOOK.md")) == "ops__RUNBOOK.md"
    assert sc.flat_name(P("/h/.claude/projects/-mnt-d-ILS/memory/project_state.md")) == "memory__project_state.md"


def test_flat_name_sanitizes_whitespace():
    sc = _load("stage_corpus")
    # sst-5047's only eligible doc is "STB - Extraction Issues.md"
    assert sc.flat_name(Path("/r/data/changes/sst-5047/STB - Extraction Issues.md")) == \
        "sst-5047__STB_-_Extraction_Issues.md"
