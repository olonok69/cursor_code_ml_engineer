#!/usr/bin/env bash
# data/knowledge-graph/kg_query.sh
# Deterministic query surface over the ticket knowledge graph (the CodeGraph analog
# for tickets/lessons). Wraps graphify's `explain` / `path` with the graph path +
# interpreter resolved, and adds a `find` helper for discovering node names.
# No LLM — reads output/graph.json directly. Refresh the graph with /kg-refresh.
set -euo pipefail

KG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH="$KG_DIR/output/graph.json"

# --- resolve an interpreter that can import graphify --------------------------
pick_graphify() {
  for p in "$HOME/miniconda3/bin/python3" "$HOME/miniconda3/bin/python" python3 python; do
    if command -v "$p" >/dev/null 2>&1 && "$p" -c "import graphify" >/dev/null 2>&1; then
      echo "$p"; return
    fi
  done
  echo ""
}

# strip graphify's version-skew warning so output is clean
run_graphify() { "$GPY" -m graphify "$@" --graph "$GRAPH" 2>&1 | grep -vE "warning: skill is from graphify|Run 'graphify install'" || true; }

usage() {
  cat >&2 <<EOF
usage:
  kg_query.sh <ticket-or-topic>        neighbours of a node   (graphify explain)
  kg_query.sh <A> <B>                  shortest path A<->B     (graphify path)
  kg_query.sh find <substring>         list node labels/ids matching <substring>

examples:
  kg_query.sh SST-5623                 # letter-end danger-zone cluster
  kg_query.sh "letter-end"
  kg_query.sh get_letter_end
  kg_query.sh SST-5623 SST-4280        # how are these two related?
  kg_query.sh find signature           # discover node names containing "signature"
EOF
  exit 2
}

[ $# -ge 1 ] || usage
[ -f "$GRAPH" ] || { echo "No graph at $GRAPH — run /kg-refresh first." >&2; exit 1; }

# --- find mode: substring search over node labels/ids (pure python) ----------
if [ "$1" = "find" ]; then
  [ $# -eq 2 ] || usage
  python3 - "$GRAPH" "$2" <<'PY'
import json, sys
graph, needle = sys.argv[1], sys.argv[2].lower()
d = json.load(open(graph))
hits = []
for n in d["nodes"]:
    hay = f"{n.get('id','')} {n.get('label','')} {n.get('norm_label','')}".lower()
    if needle in hay:
        hits.append((n.get("id",""), n.get("label",""), n.get("source_file","")))
if not hits:
    print(f"no nodes match {needle!r}")
else:
    print(f"{len(hits)} node(s) match {needle!r}:")
    for nid, label, src in sorted(hits)[:40]:
        print(f"  {nid:36} {label[:44]:44} <- {src}")
    if len(hits) > 40:
        print(f"  ... and {len(hits)-40} more")
PY
  exit 0
fi

GPY="$(pick_graphify)"
[ -n "$GPY" ] || { echo "graphify package not importable (tried miniconda + python3)." >&2; exit 1; }

if [ $# -eq 1 ]; then
  run_graphify explain "$1"
elif [ $# -eq 2 ]; then
  run_graphify path "$1" "$2"
else
  usage
fi
