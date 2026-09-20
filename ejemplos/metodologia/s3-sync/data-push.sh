#!/usr/bin/env bash
# Push local data/ -> S3 (only changed files, scoped to docs + KG).
#
# Usage:
#   ./data-push.sh            # dry-run preview (safe; shows what WOULD upload)
#   ./data-push.sh --go       # actually upload
#   ./data-push.sh --go --delete   # also remove S3 objects deleted locally
#
# --delete makes S3 mirror local exactly; omit it to only add/update (safer
# when teammates may have pushed files you don't have locally).
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env
# Actionable failure when config.env predates the per-root sync model (2026-09-04).
[[ -r ./_config_check.sh ]] && source ./_config_check.sh
# Per-machine append-only record of this run (2026-09-16). Never fails the sync.
[[ -r ./_activity_log.sh ]] && source ./_activity_log.sh || true

DRYRUN="--dryrun"
DELETE=""
ALLOW_CLOBBER=0
ONLY_ROOTS=()
_next_is_root=0
for a in "$@"; do
  if [[ "$_next_is_root" -eq 1 ]]; then ONLY_ROOTS+=( "$a" ); _next_is_root=0; continue; fi
  case "$a" in
    --go)     DRYRUN="" ;;
    --delete) DELETE="--delete" ;;
    --allow-clobber) ALLOW_CLOBBER=1 ;;
    --root)   _next_is_root=1 ;;
    --root=*) ONLY_ROOTS+=( "${a#--root=}" ) ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done
if [[ "$_next_is_root" -eq 1 ]]; then echo "--root needs a value" >&2; exit 2; fi

# --root restricts the sweep to the named root(s). `changes` is the only one that moves day
# to day, and a bare run stats all 18.
# ⚠️ Measured 2026-09-19, dry run on this machine: all 18 roots = 212s, --root changes = 123s.
# So this is a ~40% saving, NOT the order-of-magnitude one might expect — most of the cost is
# INSIDE `changes` (aws lists the whole bucket prefix and stats the whole local tree), not in
# the other 17 roots. Use it to trim the day-start/day-end checks; do not expect it to make
# them instant, and do not quote a bigger number than that without re-measuring.
# Names are validated against SYNC_ROOTS so a typo cannot silently sync nothing and report
# success.
if [[ ${#ONLY_ROOTS[@]} -gt 0 ]]; then
  for r in "${ONLY_ROOTS[@]}"; do
    _ok=0
    for s in "${SYNC_ROOTS[@]}"; do if [[ "$r" == "$s" ]]; then _ok=1; break; fi; done
    if [[ "$_ok" -ne 1 ]]; then
      echo "unknown root: $r" >&2
      echo "known roots: ${SYNC_ROOTS[*]}" >&2
      exit 2
    fi
  done
  SYNC_ROOTS=( "${ONLY_ROOTS[@]}" )
  echo ">>> scope: only root(s) ${SYNC_ROOTS[*]}"
fi

# Baton check (added 2026-08-12; SCOPED TO knowledge-graph/ 2026-09-10).
#
# What the baton protects: knowledge-graph/** — above all community_labels.json, whose
# ~100 community names are hand-authored and which NOTHING regenerates. Measured over two
# refreshes, only 37-48% of names survive even our own rebuild, so an overwrite is a real,
# unrecoverable loss. Two machines publishing that file destroy each other's work silently.
#
# ⚠️ What it must NOT block, and did until 2026-09-10: everything else. The check used to sit
# out here and gated the WHOLE sync, so a contributor could not push their own
# changes/sst-NNNN/ folders or even the refresh request that the contributor loop tells them
# to file. That contradicted FOR_NEW_JOINERS.md rules 1 and 4 and the REFRESH_OWNERSHIP.md
# role table, and was never caught because no contributor machine had ever existed. Ticket
# folders are partitioned by owner and were never the risk the baton was written for.
#
# So: resolve the holder once, enforce --delete as publisher-only, and let the per-root loop
# below refuse ONLY the knowledge-graph root. Dry runs are always allowed.
# See publisher.sh, REFRESH_OWNERSHIP.md, FOR_NEW_JOINERS.md § 4.
BATON_HOLDER=""
BATON_READ_OK=1
if [[ -z "$DRYRUN" ]]; then
  # ⚠️ Distinguish "the baton object does not exist" from "the read failed". This inline
  # read used to be `2>/dev/null || echo ""`, so ANY failure — above all an expired SSO
  # token — came back as an empty holder and printed "no publisher baton is set in the
  # bucket". That is the SAME defect publisher.sh was hardened against on 2026-09-08; the
  # fix was applied there and not here, and this site went on lying for nine days.
  # Observed 2026-09-17 05:55Z: token expired overnight, and the push announced that
  # nobody held a baton this machine demonstrably holds.
  _baton_out="$(aws s3 cp "s3://$BUCKET/$PREFIX/_publisher.json" - \
                --profile "$PROFILE" --region "$REGION" 2>&1)" && _baton_rc=0 || _baton_rc=$?
  if [[ $_baton_rc -eq 0 ]]; then
    BATON_HOLDER="$(printf '%s' "$_baton_out" \
      | python3 -c "import json,sys;print(json.load(sys.stdin).get('holder') or '')" 2>/dev/null || echo "")"
  elif grep -qiE '(404)|(Not Found)|(NoSuchKey)|(does not exist)' <<<"$_baton_out"; then
    BATON_HOLDER=""          # genuinely never claimed — the only benign failure
  else
    BATON_READ_OK=0          # could not tell; say so rather than inventing an answer
  fi
  if [[ -n "$DELETE" && "$MACHINE_ROLE" != "publisher" ]]; then
    echo "REFUSED: --delete requires MACHINE_ROLE=publisher (this machine: $MACHINE_ROLE)." >&2
    exit 1
  fi
fi

# May this machine publish the knowledge-graph root right now?
# Returns 0 (yes) or 1 (no, with the reason on stderr). A dry run always returns 0.
kg_push_allowed() {
  [[ -n "$DRYRUN" ]] && return 0
  if [[ "$BATON_READ_OK" -eq 0 ]]; then
    echo "  SKIPPED knowledge-graph/: could NOT read the publisher baton — this is not" >&2
    echo "    'nobody holds it'. The read itself failed (expired token, denied, no network)." >&2
    echo "    Re-login and try again:  aws sso logout && aws sso login" >&2
    return 1
  fi
  if [[ -z "$BATON_HOLDER" ]]; then
    echo "  SKIPPED knowledge-graph/: no publisher baton is set in the bucket." >&2
    echo "    a publisher must run: ./publisher.sh claim \"<why>\"" >&2
    return 1
  fi
  if [[ "$BATON_HOLDER" != "$MACHINE_NAME" ]]; then
    echo "  knowledge-graph/: '$BATON_HOLDER' holds the publisher baton; this machine is '$MACHINE_NAME'." >&2
    echo "    The graph and its names are publisher-only, so only refresh_queue/ is pushed from here." >&2
    echo "    This is expected on a contributor machine and is NOT an error." >&2
    return 1
  fi
  return 0
}

ACTLOG="$(mktemp)"
_act_status="failed"
_act_finish() {
  if declare -f activity_log >/dev/null 2>&1; then
    activity_log "push" "$([[ -n "$DRYRUN" ]] && echo dry || echo go)" \
                 "$([[ -n "$DELETE" ]] && echo 1 || echo 0)" \
                 "$_act_status" "$(activity_count "$ACTLOG")"
    # ⚠️ Now re-upload the ledger. The sync above uploaded it BEFORE this record existed, so
    # the bucket copy never contains the push that carried it — which means teammates could
    # see every dry run and never the real push. Measured 2026-09-17: a colleague's first
    # push moved 103 objects and his published ledger showed only three dry runs.
    # The single most useful fact in the ledger was the one it structurally could not carry.
    if [[ -z "$DRYRUN" && "$_act_status" == "ok" && -n "${MACHINE_NAME:-}" ]]; then
      aws s3 cp "$ACTIVITY_DIR/${MACHINE_NAME}.jsonl" \
        "s3://$BUCKET/$PREFIX/changes/s3-sync/_activity/${MACHINE_NAME}.jsonl" \
        --profile "$PROFILE" --region "$REGION" --quiet 2>/dev/null || true
    fi
  fi
  rm -f "$ACTLOG"
}
trap _act_finish EXIT

if [[ -n "$DRYRUN" ]]; then
  echo ">>> DRY RUN (nothing uploaded). Re-run with --go to apply."
fi
echo ">>> $LOCAL_DATA  ->  s3://$BUCKET/$PREFIX  (profile=$PROFILE, machine=$MACHINE_NAME)"

# ─── Overwrite guard for shared hub files (2026-09-19) ──────────────────────────────
#
# `aws s3 sync` is last-writer-wins with no merge, and the push direction had NO guard at
# all: the pull has snapshotted everything it would replace since 2026-09-17, but a push
# would silently destroy a colleague's NEWER bucket copy and report success. Measured
# 2026-09-18 — two files lost in a single push four minutes after a teammate closed his
# day: `changes/STATUS.md` (his whole evening section, 11 lines) and his activity ledger
# (50 lines -> 14). Nothing on THIS machine looked wrong afterwards, which is why it went
# a full day unnoticed. Both were recovered only because bucket versioning is enabled, and
# that expires at 30 days.
#
# The check: for the handful of multi-author hub files, compare the bucket's LastModified
# against the most recent successful --go sync THIS machine recorded. If the bucket copy is
# newer than anything we did, somebody else wrote it after we last saw it, and uploading
# ours would drop their edit. Abort rather than warn — a warning in a 60-line dry run is
# exactly what got missed.
_last_own_sync_ts() {
  local f="${ACTIVITY_DIR:-./_activity}/${MACHINE_NAME}.jsonl"
  [[ -r "$f" ]] || return 0
  python3 - "$f" <<'PY' 2>/dev/null || true
import json, sys
best = ""
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    # Only a real transfer proves we SAW the bucket state. A dry run touches nothing.
    if r.get("mode") == "go" and r.get("status") == "ok" and r.get("op") in ("pull", "push"):
        ts = (r.get("ts") or "")[:19]
        if ts > best:
            best = ts
print(best)
PY
}

hub_overwrite_guard() {
  local since; since="$(_last_own_sync_ts)"
  if [[ -z "$since" ]]; then
    echo ">>> hub guard: no recorded --go sync for '$MACHINE_NAME' yet — cannot tell what we have seen; skipping."
    return 0
  fi

  # The multi-author files. LEDGERS comes from config.env; the rest are hub files that
  # more than one machine edits on the same day.
  local -a hubs=()
  if [[ ${LEDGERS[@]+set} == set ]]; then hubs+=( "${LEDGERS[@]}" ); fi
  hubs+=( "changes/SHARP_EDGES.md" )
  local p
  for p in "$LOCAL_DATA"/changes/_PENDING_*.md; do
    if [[ -e "$p" ]]; then hubs+=( "changes/$(basename "$p")" ); fi
  done

  local -a collided=()
  local rel head bm etag lmd5
  for rel in "${hubs[@]}"; do
    [[ -f "$LOCAL_DATA/$rel" ]] || continue          # not ours to push
    head="$(aws s3api head-object --bucket "$BUCKET" --key "$PREFIX/$rel" \
              --profile "$PROFILE" --region "$REGION" \
              --query '[LastModified,ETag]' --output text 2>/dev/null || true)"
    if [[ -z "$head" ]]; then continue; fi                    # absent in the bucket: nothing to lose
    bm="$(awk '{print $1}' <<<"$head")"
    etag="$(awk '{print $2}' <<<"$head" | tr -d '"')"
    if [[ -z "$bm" || "$bm" == "None" ]]; then continue; fi
    bm="${bm:0:19}"
    if [[ ! "$bm" > "$since" ]]; then continue; fi             # we have seen this copy

    # ⚠️ The timestamp alone gives a FALSE POSITIVE on the commonest case there is: you pulled
    # the newer copy minutes ago and hold it byte-for-byte, but your ledger has no record of a
    # --go pull (an old data-pull.sh, a --no-snapshot run, a first day on the machine). The
    # guard would then refuse a push that could not possibly destroy anything, on files the
    # user had literally just fetched — which is how a guard trains people to reach for
    # --allow-clobber. So ask the real question: would uploading actually CHANGE the object?
    # ETag is the md5 for a single-part upload; a multipart one contains "-", and there we
    # fall back to the timestamp because we cannot cheaply compare.
    if [[ "$etag" != *-* ]]; then
      lmd5="$(md5sum "$LOCAL_DATA/$rel" 2>/dev/null | awk '{print $1}')"
      if [[ -n "$lmd5" && "$lmd5" == "$etag" ]]; then continue; fi   # identical: nothing to lose
    fi
    collided+=( "$rel  (bucket $bm  >  our last sync $since)" )
  done

  if [[ ${#collided[@]} -eq 0 ]]; then return 0; fi

  echo "" >&2
  echo "⛔ REFUSED: ${#collided[@]} shared hub file(s) changed in the bucket since this machine last synced." >&2
  printf '     %s\n' "${collided[@]}" >&2
  echo "" >&2
  echo "   Someone else edited them after you last pulled. Pushing now would REPLACE their" >&2
  echo "   version with yours — silently, and with no snapshot on this side." >&2
  echo "   These are shared files: the answer is a MERGE, not a winner." >&2
  echo "" >&2
  echo "   1. See what theirs says:" >&2
  echo "      aws s3 cp s3://$BUCKET/$PREFIX/<file> - --profile $PROFILE | diff - $LOCAL_DATA/<file>" >&2
  echo "   2. Fold anything of theirs that you lack into your local copy, then re-run." >&2
  echo "   3. Only if you are certain yours supersedes theirs:  $0 --go --allow-clobber" >&2
  echo "      (bucket versioning can recover the loser for 30 days, if anyone notices.)" >&2
  return 1
}

if [[ "$ALLOW_CLOBBER" -eq 1 ]]; then
  echo ">>> hub guard: DISABLED by --allow-clobber."
elif ! hub_overwrite_guard; then
  # A dry run uploads nothing, so it reports and continues; only a real push is stopped.
  if [[ -z "$DRYRUN" ]]; then
    _act_status="refused"
    exit 4
  fi
  echo ">>> (dry run — continuing so you can still see the file list)" >&2
fi

# Per-root sync (2026-09-04). aws s3 sync stats the WHOLE source tree before applying
# any --exclude, so pointing it at data/ pays for 20k node_modules files it will never
# upload. Walking only the roots in scope keeps purely-local trees free. JUNK_ARGS still
# runs last as the backstop for junk that lives INSIDE a synced root.
KG_RESTRICTED=0
for root in "${SYNC_ROOTS[@]}"; do
  # ⚠️ A contributor is blocked from publishing the GRAPH, never from the refresh QUEUE.
  # refresh_queue/ is the contributor loop's mailbox: kg_refresh.sh writes the request there
  # and the whole coordination model depends on it reaching the bucket. Skipping the root
  # wholesale (as this did between 09:18 and 10:15 on 2026-09-10) silently swallowed the
  # request — created locally, never pushed, publisher never sees it. Caught by simulating
  # the loop, not by reading the code. One file per request, distinct keys, so it is safe
  # under last-writer-wins; --delete is never applied here.
  if [[ "$root" == "knowledge-graph" ]] && ! kg_push_allowed; then
    echo ">>> $root  (refresh_queue/ only — the publisher owns the rest)"
    aws s3 sync "$LOCAL_DATA/$root" "s3://$BUCKET/$PREFIX/$root" \
      --profile "$PROFILE" --region "$REGION" \
      --exclude "*" --include "refresh_queue/*" "${JUNK_ARGS[@]}" \
      $DRYRUN | tee -a "$ACTLOG"
    KG_RESTRICTED=1
    continue
  fi
  fvar="FILTERS_${root//-/_}"
  # `declare -n` (nameref) is bash 4.3+. Stock macOS ships bash 3.2, where it is an
  # "invalid option" and the sync dies on the first root -- after validate.sh has
  # already printed MACHINE READY. Expand the named array indirectly instead. The
  # ${a[@]+"${a[@]}"} guard is needed because most FILTERS_* are EMPTY arrays and
  # `set -u` treats "${empty[@]}" as unbound on bash < 4.4.
  filters=()
  eval "filters=( \${$fvar[@]+\"\${$fvar[@]}\"} )"

  # ⚠️⚠️ NEVER upload another machine's activity ledger. Each ledger is append-only and
  # its OWNING machine is the only writer; our copy of someone else's is whatever we last
  # pulled, i.e. always stale. `aws s3 sync` transfers on a size difference in EITHER
  # direction, so pushing our stale copy ROLLS THEIR AUDIT TRAIL BACK.
  #
  # Measured 2026-09-18: a teammate closed his day at 17:42 and his published ledger grew
  # to 9,144 bytes / 50 lines. Our push at 17:46:43 replaced it with the 2,557-byte / 14-line
  # copy we had pulled that morning, erasing every record of his day — including the two
  # --go pushes that carried his work. The same thing had already happened at 08:31.
  # It read as "he never closed his day". He had.
  #
  # data-pull.sh has excluded OUR OWN ledger from download since 2026-09-17 for exactly this
  # reason; the mirror-image exclusion on the push side was simply missing. Ours still goes
  # up (and _act_finish re-uploads it afterwards, so the run that carried it is recorded).
  push_only=()
  if [[ "$root" == "changes" && -n "${MACHINE_NAME:-}" ]]; then
    push_only=( --exclude "s3-sync/_activity/*.jsonl"
                --include "s3-sync/_activity/${MACHINE_NAME}.jsonl" )
  fi

  echo ">>> $root"
  aws s3 sync "$LOCAL_DATA/$root" "s3://$BUCKET/$PREFIX/$root" \
    --profile "$PROFILE" --region "$REGION" \
    ${filters[@]+"${filters[@]}"} "${JUNK_ARGS[@]}" \
    ${push_only[@]+"${push_only[@]}"} \
    $DELETE $DRYRUN | tee -a "$ACTLOG"
  unset filters push_only
done

if [[ "$KG_RESTRICTED" -eq 1 ]]; then
  echo ">>> done — every root pushed; knowledge-graph/ limited to refresh_queue/ (see above)."
fi

_act_status="ok"
