"""Offline guard tests for kg_refresh.sh. No network, no graphify."""
import os, shutil, subprocess
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE / "kg_refresh.sh"


@pytest.fixture(autouse=True)
def _preserve_real_artifacts(tmp_path_factory):
    kg = _HERE
    saves = {}
    for rel in ("output/graph.json", "graphify-out/graph.json",
                "output/graph.html", "output/GRAPH_REPORT.md"):
        p = kg / rel
        if p.exists():
            b = tmp_path_factory.mktemp("bak") / p.name
            shutil.copy2(p, b); saves[p] = b
    yield
    for p, b in saves.items():
        shutil.copy2(b, p)


def _run(subcmd, scratch, extra_env=None):
    env = dict(os.environ, KG_SCRATCH=str(scratch))
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(_SCRIPT), subcmd],
        capture_output=True, text=True, env=env,
    )


def test_prepare_stages_corpus_into_scratch(tmp_path):
    scratch = tmp_path / "scratch"
    r = _run("prepare", scratch)
    assert r.returncode == 0, r.stderr
    staged = scratch / "_corpus"
    assert staged.is_dir()
    files = list(staged.iterdir())
    assert len(files) > 50, f"expected the real ~90-file corpus, got {len(files)}"
    # leak-shape guard: no forbidden extensions / payload names slipped through
    assert not [p for p in files if p.suffix in {".png", ".json", ".docx"}]
    assert not [p for p in files if "payload" in p.name]


def test_unknown_subcommand_errors(tmp_path):
    r = _run("frobnicate", tmp_path / "s")
    assert r.returncode == 2
    assert "usage" in (r.stdout + r.stderr).lower()
    # the new travel/bootstrap subcommands are advertised
    for sub in ("snapshot-memory", "restore-memory", "bootstrap"):
        assert sub in (r.stdout + r.stderr)


def _run_env(sub, extra_env):
    env = dict(os.environ, **extra_env)
    return subprocess.run(["bash", str(_SCRIPT), sub], capture_output=True, text=True, env=env)


def test_snapshot_memory_copies_md(tmp_path):
    mem = tmp_path / "memory"; mem.mkdir()
    (mem / "a.md").write_text("alpha")
    (mem / "b.md").write_text("beta")
    (mem / "notes.txt").write_text("ignored")  # non-.md must not travel
    snap = tmp_path / "snap"
    r = _run_env("snapshot-memory", {"KG_MEMORY_DIR": str(mem), "KG_SNAPSHOT_DIR": str(snap)})
    assert r.returncode == 0, r.stderr
    got = sorted(p.name for p in snap.glob("*.md"))
    assert got == ["a.md", "b.md"]
    assert not (snap / "notes.txt").exists()


def test_restore_memory_merges_and_backs_up(tmp_path):
    # snapshot (from the "other" machine) has a new file + a changed file
    snap = tmp_path / "snap"; snap.mkdir()
    (snap / "new.md").write_text("brought back from the laptop")
    (snap / "changed.md").write_text("LAPTOP version")
    # this machine's live memory: an unrelated file + the pre-trip version of changed.md
    mem = tmp_path / "memory"; mem.mkdir()
    (mem / "changed.md").write_text("MAIN version")
    (mem / "untouched.md").write_text("stays")
    r = _run_env("restore-memory", {"KG_MEMORY_DIR": str(mem), "KG_SNAPSHOT_DIR": str(snap)})
    assert r.returncode == 0, r.stderr
    # new file added, changed file overwritten with the laptop version, untouched left alone
    assert (mem / "new.md").read_text() == "brought back from the laptop"
    assert (mem / "changed.md").read_text() == "LAPTOP version"
    assert (mem / "untouched.md").read_text() == "stays"
    # main's prior version of the overwritten file was backed up (non-destructive)
    baks = list(snap.glob(".main_memory_bak_*/changed.md"))
    assert baks and baks[0].read_text() == "MAIN version"


def test_restore_memory_noop_when_identical(tmp_path):
    snap = tmp_path / "snap"; snap.mkdir()
    mem = tmp_path / "memory"; mem.mkdir()
    (snap / "same.md").write_text("identical")
    (mem / "same.md").write_text("identical")
    r = _run_env("restore-memory", {"KG_MEMORY_DIR": str(mem), "KG_SNAPSHOT_DIR": str(snap)})
    assert r.returncode == 0, r.stderr
    assert "0 added, 0 updated" in r.stdout
    # no backup dir created when nothing was overwritten
    assert not list(snap.glob(".main_memory_bak_*"))


def test_restore_memory_nothing_to_restore(tmp_path):
    snap = tmp_path / "snap"; snap.mkdir()
    mem = tmp_path / "memory"; mem.mkdir()
    r = _run_env("restore-memory", {"KG_MEMORY_DIR": str(mem), "KG_SNAPSHOT_DIR": str(snap)})
    assert r.returncode == 0, r.stderr
    assert "nothing to restore" in r.stdout.lower()


def _fake_graphify_out(scratch):
    """Simulate what /graphify leaves behind, so finalize can be tested offline."""
    out = scratch / "graphify-out"
    out.mkdir(parents=True)
    (out / "graph.json").write_text('{"nodes":[],"links":[]}')
    (out / "graph.html").write_text("<html>graph</html>")
    (out / "GRAPH_REPORT.md").write_text("# Report\n\nGraph: 5 nodes, 4 edges, 2 communities\n")
    return out


def test_finalize_without_graphify_run_errors(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    r = _run("finalize", scratch)
    assert r.returncode != 0
    assert "graph.json" in (r.stdout + r.stderr)


def test_finalize_syncs_both_output_and_inplace(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    _fake_graphify_out(scratch)
    r = _run("finalize", scratch)
    assert r.returncode == 0, r.stderr
    kg = _HERE
    # deliverable in output/
    assert (kg / "output" / "graph.json").read_text() == '{"nodes":[],"links":[]}'
    assert (kg / "output" / "graph.html").exists()
    assert (kg / "output" / "GRAPH_REPORT.md").exists()
    # in-place copy for /graphify query MUST also be updated (the §3 regression guard)
    assert (kg / "graphify-out" / "graph.json").read_text() == '{"nodes":[],"links":[]}'
