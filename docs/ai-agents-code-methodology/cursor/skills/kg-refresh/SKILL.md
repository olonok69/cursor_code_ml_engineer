---
name: kg-refresh
description: >-
  Rebuild or refresh the ticket knowledge graph (graphify corpus) after new
  writeups land. Use when closing a ticket loop, after adding STATUS/PLAYBOOK
  lessons, or when the user asks to refresh /kg.
---

# kg-refresh — rebuild ticket knowledge graph

## When to use

- Stage **11 Persist** after durable docs changed.
- User asks to refresh the ticket graph / `/kg-refresh`.

## Procedure

1. Locate project scripts (commonly `docs/knowledge-graph/kg_refresh.sh` or equivalent).
2. Follow the project’s documented pipeline. Typical shape:

```text
kg_refresh.sh prepare   # stage corpus outside gitignored paths if required
# run graphify extract on the staged corpus (may need an agent step)
kg_refresh.sh finalize  # copy artifacts + leak-check
```

3. **Gotcha:** some graphify setups respect `.gitignore` and will see **0 files** if run inside a gitignored `data/` tree. Prefer the project’s scratch/staging flow; do not invent a shortcut that indexes stale travel tarballs.
4. Smoke-test with the `kg` skill on a known ticket id.
5. Report what changed (node/edge counts if available) and any failures.

## If graphify is not installed

Do not fail the methodology. Ensure instead:

1. `data/changes/STATUS.md` updated.
2. Per-ticket writeup complete.
3. `SHARP_EDGES.md` / `PLAYBOOK.md` updated if a reusable lesson exists.

Tell the user the graph refresh was skipped and the STATUS fallback remains authoritative.
