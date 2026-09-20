#!/usr/bin/env bash
# Append-only, per-machine record of every pull and push.
#
# Sourced by data-pull.sh and data-push.sh. Writes ONE line of JSON per run to
#   _activity/<MACHINE_NAME>.jsonl
# and is read back by ./activity.sh.
#
# Why this exists (2026-09-16): nothing recorded a sync. "When did this machine last
# pull?" and "has anyone pulled my work?" were unanswerable from the repo, so the
# start-of-day pull could quietly stop happening for weeks and no artifact would show
# it — the same failure shape as the contributor loop that was documented for months
# before anyone ran it. A rule nobody can audit is a rule that decays silently.
#
# ONE FILE PER MACHINE is load-bearing, same reasoning as knowledge-graph/refresh_queue/:
# `aws s3 sync` is last-writer-wins with no merge, so a single shared ledger would lose
# entries. Distinct keys never collide.
#
# This must NEVER fail a sync. Every call site tolerates a non-zero return, and every
# statement here is guarded — a broken ledger loses a record, it does not lose your work.

ACTIVITY_DIR="${ACTIVITY_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_activity}"

# activity_log <op> <mode> <delete 0|1> <status> <objects>
#   op      pull | push
#   mode    dry  | go
#   status  ok   | failed
activity_log() {
  local op="${1:-?}" mode="${2:-?}" del="${3:-0}" status="${4:-?}" n="${5:-0}"
  mkdir -p "$ACTIVITY_DIR" 2>/dev/null || return 0
  python3 - "$ACTIVITY_DIR/${MACHINE_NAME:-unknown}.jsonl" \
            "$op" "$mode" "$del" "$status" "$n" \
            "${MACHINE_NAME:-unknown}" "${MACHINE_ROLE:-unknown}" <<'PY' 2>/dev/null || true
import json, sys, os, datetime
path, op, mode, dele, status, n, machine, role = sys.argv[1:9]
try:
    objects = int(n)
except (TypeError, ValueError):
    objects = 0
rec = {
    "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "machine": machine,
    "role": role,
    "op": op,
    "mode": mode,
    "delete": dele == "1",
    "status": status,
    "objects": objects,
    "host": os.uname().nodename,
}
with open(path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec) + "\n")
PY
  return 0
}

# Count transferred objects in a captured sync log. aws prints one entry per object:
#   download: s3://... to ...      upload: ... to s3://...      delete: s3://...
# A dry run prefixes each with "(dryrun) ", counted the same way on purpose — the record
# says mode=dry, so the number means "would have moved".
#
# ⚠️ Count OCCURRENCES, never line-anchored matches. On a real run aws writes its
# "Completed N KiB/~M KiB ..." progress with carriage returns, so the transfer entry ends
# up in the MIDDLE of a line: a `grep -c "^upload:"` returns a confident ZERO for every
# --go run while dry runs (no progress output) count perfectly. Measured 2026-09-16 — the
# first real push recorded objects:0 against 43 files actually uploaded.
activity_count() {
  local log="${1:-}"
  [[ -r "$log" ]] || { echo 0; return 0; }
  grep -oE '(download|upload|delete): ' "$log" 2>/dev/null | wc -l | tr -d ' \n' || echo 0
}
