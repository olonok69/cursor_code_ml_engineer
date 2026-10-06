#!/usr/bin/env bash
# Drop local refresh requests that were already consumed.
#
# Sourced by data-pull.sh and data-push.sh. A request is pending only while it has no twin in
# refresh_queue/consumed/. The publisher's `kg_refresh.sh queue --clear` moves it there and
# deletes the bucket key, but `aws s3 sync` never deletes local files, so the REQUESTER keeps
# its own copy, and its next push puts the key back in the bucket. The requester never runs
# `queue`, which is the only other place that cleaned this up.
#
# Measured 2026-10-05: 4 consumed requests were back in the bucket, re-pushed
# by the machine that filed them; deleting the keys by hand fixes it only until its next push.
#
# Never fails a sync. With a dry run it reports and changes nothing.

reconcile_refresh_queue() {
  local q="$LOCAL_DATA/knowledge-graph/refresh_queue" dry="${1:-}" f n=0
  [[ -d "$q/consumed" ]] || return 0
  for f in "$q"/*.request; do
    [[ -f "$f" ]] || continue
    [[ -f "$q/consumed/$(basename "$f")" ]] || continue
    if [[ -n "$dry" ]]; then
      echo "  (dry run) would drop already-consumed request: $(basename "$f")"
    else
      rm -f "$f" && echo "  dropped already-consumed request: $(basename "$f")"
    fi
    n=$((n + 1))
  done
  [[ "$n" -gt 0 ]] && echo ">>> refresh queue: $n already-consumed request(s) $([[ -n "$dry" ]] && echo 'would be' || echo 'were') dropped locally"
  return 0
}
