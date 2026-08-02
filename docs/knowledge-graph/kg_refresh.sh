#!/usr/bin/env bash
# data/knowledge-graph/kg_refresh.sh
# Repeatable refresh of the ticket knowledge graph. Deterministic bookends only;
# the /graphify semantic-extraction step in the middle is a Claude step (subagents).
set -euo pipefail

KG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$KG_DIR/../.." && pwd)"
SCRATCH="${KG_SCRATCH:-$HOME/.cache/ils-kg}"
CORPUS="$KG_DIR/_corpus"
MEMORY_DIR="${KG_MEMORY_DIR:-$(ls -d "$HOME"/.claude/projects/*ILS*/memory 2>/dev/null | head -1)}"
MEMORY_DIR="${MEMORY_DIR:-$HOME/.claude/projects/-mnt-d-ILS/memory}"
SNAPSHOT="${KG_SNAPSHOT_DIR:-$KG_DIR/_memory_snapshot}"

# --- resolve python: prefer repo venv, else python3 -------------------------
pick_python() {
  if [ -n "${VIRTUAL_ENV:-}" ]; then echo "python"; return; fi
  for p in "$REPO/.venv/bin/python" "$REPO/.venv-1/bin/python"; do
    [ -x "$p" ] && { echo "$p"; return; }
  done
  echo "python3"
}
PY="$(pick_python)"

usage() {
  cat >&2 <<EOF
usage: kg_refresh.sh {prepare|finalize|snapshot-memory|restore-memory|bootstrap}
  prepare          build manifest -> stage _corpus/ -> copy to \$KG_SCRATCH ($SCRATCH)
                   then run:  /graphify \$KG_SCRATCH/_corpus
  finalize         copy graphify-out artifacts back into data/knowledge-graph/ + leak-check
  snapshot-memory  (before LEAVING a machine) copy ~/.claude memory/*.md -> _memory_snapshot/
                   so it rides the laptop->main delta tarball (memory is not in the delta otherwise)
  restore-memory   (on ARRIVAL) merge _memory_snapshot/*.md back into ~/.claude memory (backs up first)
  bootstrap        (FROM SCRATCH on a bare machine) install graphify + pin interpreter + verify /kg works
EOF
  exit 2
}

cmd_prepare() {
  cd "$KG_DIR"
  "$PY" build_manifest.py
  "$PY" stage_corpus.py
  # belt-and-braces leak guard on the staged corpus (stage_corpus already excludes these)
  local bad
  bad="$(find "$CORPUS" -maxdepth 1 \( -name '*.png' -o -name '*.json' -o -name '*.docx' -o -name '*payload*' \) -print)"
  if [ -n "$bad" ]; then
    echo "ABORT: leak-shaped file(s) staged into _corpus/:" >&2
    echo "$bad" >&2
    exit 1
  fi
  rm -rf "$SCRATCH"
  mkdir -p "$SCRATCH"
  cp -r "$CORPUS" "$SCRATCH/_corpus"
  local n
  n="$(find "$SCRATCH/_corpus" -maxdepth 1 -type f | wc -l | tr -d ' ')"
  echo "prepared: $n files staged -> $SCRATCH/_corpus"
  echo "Next: run  /graphify $SCRATCH/_corpus  then  bash $KG_DIR/kg_refresh.sh finalize"
}

cmd_finalize() {
  local gout="$SCRATCH/graphify-out"
  if [ ! -f "$gout/graph.json" ]; then
    echo "ABORT: $gout/graph.json not found." >&2
    echo "Run  /graphify $SCRATCH/_corpus  before finalize (did prepare run?)." >&2
    exit 1
  fi
  mkdir -p "$KG_DIR/output" "$KG_DIR/graphify-out"
  # deliverable trio -> output/
  cp "$gout/graph.html"      "$KG_DIR/output/graph.html"
  cp "$gout/graph.json"      "$KG_DIR/output/graph.json"
  cp "$gout/GRAPH_REPORT.md" "$KG_DIR/output/GRAPH_REPORT.md"
  # in-place graph.json keeps /graphify query fresh (reads data/knowledge-graph/graphify-out/)
  cp "$gout/graph.json" "$KG_DIR/graphify-out/graph.json"
  # ensure the interpreter marker exists for in-place query
  if [ ! -f "$KG_DIR/graphify-out/.graphify_python" ] && [ -f "$gout/.graphify_python" ]; then
    cp "$gout/.graphify_python" "$KG_DIR/graphify-out/.graphify_python"
  fi
  # leak check: nothing knowledge-graph landed outside data/
  if git -C "$REPO" status --porcelain 2>/dev/null | grep -v '^?? data/' | grep -qi knowledge; then
    echo "ABORT: a knowledge-graph artifact landed OUTSIDE data/ — investigate:" >&2
    git -C "$REPO" status --porcelain | grep -v '^?? data/' | grep -i knowledge >&2
    exit 1
  fi
  local summary
  summary="$(grep -m1 -E 'Graph: .*nodes' "$KG_DIR/output/GRAPH_REPORT.md" || true)"
  echo "finalized -> $KG_DIR/output/  (${summary:-report copied})"
  echo "Open: $KG_DIR/output/graph.html"
}

# --- travel: memory does NOT ride the inbound delta by default (ils-to-main
#     INSTRUCTIONS excludes ~/.claude). snapshot-memory parks it UNDER data/ so it
#     travels; restore-memory folds it back into ~/.claude on the other machine.
#     ~/.claude/.../memory stays the single source of truth; the snapshot is transport.
cmd_snapshot_memory() {
  [ -d "$MEMORY_DIR" ] || { echo "ABORT: no memory dir at $MEMORY_DIR" >&2; exit 1; }
  mkdir -p "$SNAPSHOT"
  rm -f "$SNAPSHOT"/*.md
  local n=0 f
  for f in "$MEMORY_DIR"/*.md; do
    [ -e "$f" ] || continue
    cp -p "$f" "$SNAPSHOT/"; n=$((n+1))
  done
  echo "snapshot-memory: $n memory file(s) -> $SNAPSHOT/"
  echo "It lives under data/ (gitignored) so it rides the laptop->main delta tarball."
  echo "On the OTHER machine after extracting the delta:"
  echo "  bash $KG_DIR/kg_refresh.sh restore-memory   then   /kg-refresh"
}

cmd_restore_memory() {
  local snaps
  snaps="$(find "$SNAPSHOT" -maxdepth 1 -name '*.md' 2>/dev/null || true)"
  [ -n "$snaps" ] || { echo "nothing to restore (no $SNAPSHOT/*.md — run snapshot-memory on the other machine first)"; exit 0; }
  mkdir -p "$MEMORY_DIR"
  local bak="$SNAPSHOT/.main_memory_bak_$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$bak"
  local added=0 updated=0 base dst
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    base="$(basename "$f")"; dst="$MEMORY_DIR/$base"
    if [ -e "$dst" ]; then
      if ! cmp -s "$f" "$dst"; then
        cp -p "$dst" "$bak/"; cp -p "$f" "$dst"; updated=$((updated+1))
        echo "  updated  $base  (this machine's prior version -> $bak/)"
      fi
    else
      cp -p "$f" "$dst"; added=$((added+1))
      echo "  added    $base"
    fi
  done <<< "$snaps"
  rmdir "$bak" 2>/dev/null || true   # drop the backup dir if nothing was overwritten
  echo "restore-memory: $added added, $updated updated into $MEMORY_DIR"
  [ "$updated" -gt 0 ] && echo "  NOTE: files were overwritten — if THIS machine also edited memory while away, reconcile from $bak"
  echo "Snapshot consumed. Then rebuild:  bash $KG_DIR/kg_refresh.sh prepare  (or /kg-refresh)."
  echo "Safe to delete the transport snapshot afterwards:  rm -rf $SNAPSHOT"
}

# --- from-scratch bring-up on a bare machine (graphify not installed yet) ----
cmd_bootstrap() {
  local gpy="" p target
  for p in "$HOME/miniconda3/bin/python3" python3 python; do
    command -v "$p" >/dev/null 2>&1 || continue
    if "$p" -c "import graphify" >/dev/null 2>&1; then gpy="$p"; break; fi
  done
  if [ -z "$gpy" ]; then
    for p in "$HOME/miniconda3/bin/python3" python3; do command -v "$p" >/dev/null 2>&1 && { target="$p"; break; }; done
    [ -n "${target:-}" ] || { echo "ABORT: no python3 found to install graphify into." >&2; exit 1; }
    echo "graphify not importable — installing 'graphifyy' into $target ..."
    "$target" -m pip install -q graphifyy 2>/dev/null \
      || "$target" -m pip install -q --user graphifyy 2>/dev/null \
      || "$target" -m pip install -q --break-system-packages graphifyy 2>/dev/null || true
    "$target" -c "import graphify" >/dev/null 2>&1 && gpy="$target"
  fi
  [ -n "$gpy" ] || { echo "ABORT: graphify still not importable after install (try: <python> -m pip install graphifyy)." >&2; exit 1; }
  mkdir -p "$KG_DIR/graphify-out"
  "$gpy" -c "import sys; open('$KG_DIR/graphify-out/.graphify_python','w').write(sys.executable)"
  echo "graphify OK  ->  interpreter pinned: $(cat "$KG_DIR/graphify-out/.graphify_python")"
  if [ -f "$KG_DIR/output/graph.json" ]; then
    echo "graph present: $("$gpy" -c "import json;d=json.load(open('$KG_DIR/output/graph.json'));print(len(d['nodes']),'nodes /',len(d.get('links',[])),'edges')")"
    echo "smoke test  ->  bash $KG_DIR/kg_query.sh SST-5623"
    bash "$KG_DIR/kg_query.sh" SST-5623 2>&1 | grep -m1 -E "Connections|No node" || true
  else
    echo "no graph yet (output/graph.json missing) — run /kg-refresh to build one."
  fi
  echo "bootstrap OK — /kg and /kg-refresh are ready on this machine."
}

main() {
  [ $# -ge 1 ] || usage
  case "$1" in
    prepare)          cmd_prepare ;;
    finalize)         cmd_finalize ;;
    snapshot-memory)  cmd_snapshot_memory ;;
    restore-memory)   cmd_restore_memory ;;
    bootstrap)        cmd_bootstrap ;;
    *)                usage ;;
  esac
}
main "$@"
