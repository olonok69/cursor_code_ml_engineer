"""Offline guard tests for kg_query.sh (read-only query surface).

`find` is pure-python and always runs; `explain`/`path` need the graphify package
and skip if it is not importable. All run against the real output/graph.json.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPT = _HERE / "kg_query.sh"
_GRAPH = _HERE / "output" / "graph.json"


def _run(*args):
    return subprocess.run(
        ["bash", str(_SCRIPT), *args], capture_output=True, text=True
    )


def _has_graphify():
    for exe in ("python3", str(Path.home() / "miniconda3/bin/python3")):
        if shutil.which(exe) or Path(exe).exists():
            r = subprocess.run([exe, "-c", "import graphify"], capture_output=True)
            if r.returncode == 0:
                return True
    return False


def test_usage_on_no_args():
    r = _run()
    assert r.returncode == 2
    assert "usage" in (r.stdout + r.stderr).lower()


def test_find_matches_real_graph():
    r = _run("find", "letter")
    assert r.returncode == 0, r.stderr
    assert "match" in r.stdout.lower()
    # every result row traces back to a source file
    assert "<-" in r.stdout


def test_find_no_match_is_graceful():
    r = _run("find", "zzz-not-a-real-node-xyz")
    assert r.returncode == 0, r.stderr
    assert "no nodes match" in r.stdout.lower()


@pytest.mark.skipif(not _GRAPH.exists(), reason="graph not built (run /kg-refresh)")
@pytest.mark.skipif(not _has_graphify(), reason="graphify package not importable")
def test_explain_known_ticket_lists_connections():
    r = _run("SST-5623")
    assert r.returncode == 0, r.stderr
    assert "Connections" in r.stdout
    # the letter-end danger zone should be reachable from SST-5623
    assert "SST-4280" in r.stdout or "SST-4940" in r.stdout


@pytest.mark.skipif(not _GRAPH.exists(), reason="graph not built (run /kg-refresh)")
@pytest.mark.skipif(not _has_graphify(), reason="graphify package not importable")
def test_path_between_two_tickets():
    r = _run("SST-5623", "SST-4280")
    assert r.returncode == 0, r.stderr
    assert "path" in r.stdout.lower()
