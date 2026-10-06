#!/usr/bin/env bash
# Pull S3 -> local data/ (only changed files, scoped to docs + KG).
#
# Usage:
#   ./data-pull.sh            # dry-run preview (safe; shows what WOULD download)
#   ./data-pull.sh --go       # actually download
#   ./data-pull.sh --go --delete   # also remove local files deleted on S3
#
# --delete makes local mirror S3 exactly; omit it to only add/update (safer:
# keeps local-only work-in-progress that isn't on S3 yet).
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env
# Actionable failure when config.env predates the per-root sync model (2026-09-04).
[[ -r ./_config_check.sh ]] && source ./_config_check.sh
# Per-machine append-only record of this run (2026-09-16). Never fails the sync.
[[ -r ./_activity_log.sh ]] && source ./_activity_log.sh || true
[[ -r ./_queue_reconcile.sh ]] && source ./_queue_reconcile.sh || true

DRYRUN="--dryrun"
DELETE=""
SNAPSHOT=1
ONLY_ROOTS=()
_next_is_root=0
for a in "$@"; do
  if [[ "$_next_is_root" -eq 1 ]]; then ONLY_ROOTS+=( "$a" ); _next_is_root=0; continue; fi
  case "$a" in
    --go)     DRYRUN="" ;;
    --delete) DELETE="--delete" ;;
    --no-snapshot) SNAPSHOT=0 ;;
    --root)   _next_is_root=1 ;;
    --root=*) ONLY_ROOTS+=( "${a#--root=}" ) ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done
if [[ "${_next_is_root:-0}" -eq 1 ]]; then echo "--root needs a value" >&2; exit 2; fi

# --root restricts the sweep to the named root(s) — see the same block in data-push.sh for the
# measured saving (~40%, not order-of-magnitude: most of the cost is inside `changes`).
# Validated against SYNC_ROOTS so a typo cannot silently sync nothing and report success.
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

ACTLOG="$(mktemp)"
_act_status="failed"
_act_finish() {
  if declare -f activity_log >/dev/null 2>&1; then
    activity_log "pull" "$([[ -n "$DRYRUN" ]] && echo dry || echo go)" \
                 "$([[ -n "$DELETE" ]] && echo 1 || echo 0)" \
                 "$_act_status" "$(activity_count "$ACTLOG")"
  fi
  rm -f "$ACTLOG"
  # The snapshot block below also needs a temp file cleaned up. It used to install its own
  # `trap ... EXIT`, which SILENTLY REPLACED this one — bash keeps only one EXIT trap. Since
  # that block runs only on --go, every real pull stopped being recorded while dry runs kept
  # logging, so activity.sh showed a "last pull" that was only ever a dry run. Clean it up
  # from here instead; never add a second EXIT trap to this script.
  [[ -n "${_plan:-}" ]] && rm -f "$_plan"
  return 0
}
trap _act_finish EXIT

if [[ -n "$DRYRUN" ]]; then
  echo ">>> DRY RUN (nothing downloaded). Re-run with --go to apply."
fi
# Append-only ledger check (2026-09-04). Runs BEFORE the sync so you see what an
# incoming copy is missing while your local copy is still intact. Advisory: never
# blocks, never edits. See ledger_check.sh for why, and for the 30-day recovery window.
if [[ -x ./ledger_check.sh ]]; then
  echo ">>> ledger check (append-only files)"
  ./ledger_check.sh --quiet || true
fi

echo ">>> s3://$BUCKET/$PREFIX  ->  $LOCAL_DATA  (profile=$READ_PROFILE)"

# ── PRE-PULL SNAPSHOT + DIVERGENCE GUARD (2026-09-17) ────────────────────────
# ⚠️⚠️ `aws s3 sync` transfers on a SIZE DIFFERENCE, not only when the remote copy is
# newer, so a pull OVERWRITES local work that is newer than the bucket's — silently, with
# no --delete involved. It bit three times on the first two-machine day: this machine's
# hub files, a teammate's ticket docs (via case-colliding keys), and — while being written
# — THIS SCRIPT, whose unpushed guard code a pull replaced with the bucket's older copy.
#
# So: dry-run first, snapshot every local file the pull is about to replace, and print it.
# A pull becomes reversible instead of destructive. Skip with --no-snapshot.
# Every planned download as "<root>/<rel>" under LOCAL_DATA, one per line.
# ⚠️ Not `grep 'download: s3://[^ ]+ to .*'`: that dropped every key with a space (2,737 of 6,129
# keys on 2026-10-05), so those files were neither snapshotted nor collision-checked. Keys can
# also contain " to ", so the split is the LAST " to " after which the
# destination ends with the same relative path as the source.
_planned_rels() {
  awk -v pre="download: s3://$BUCKET/$PREFIX/" '
    { i = index($0, pre); if (!i) next
      x = substr($0, i + length(pre)); n = length(x); hit = ""
      for (p = 1; p <= n - 3; p++) {
        if (substr(x, p, 4) != " to ") continue
        src = substr(x, 1, p - 1); dst = substr(x, p + 4)
        rel = substr(src, index(src, "/") + 1)
        if (length(dst) >= length(rel) && substr(dst, length(dst) - length(rel) + 1) == rel) hit = src
      }
      if (hit != "") print hit }' "$1"
}

SNAP=""
if [[ -z "$DRYRUN" && "$SNAPSHOT" -eq 1 ]]; then
  SNAP="$LOCAL_DATA/_prepull/$(date -u +%Y%m%d-%H%M%S)"
  echo ">>> pre-pull check (dry run) — snapshotting anything this pull would overwrite"
  _plan="$(mktemp)"   # cleaned up by _act_finish — do NOT install an EXIT trap here
  for root in "${SYNC_ROOTS[@]}"; do
    fvar="FILTERS_${root//-/_}"
    filters=(); eval "filters=( \${$fvar[@]+\"\${$fvar[@]}\"} )"
    pull_only=()
    if [[ "$root" == "changes" && -n "${MACHINE_NAME:-}" ]]; then
      pull_only=( --exclude "s3-sync/_activity/${MACHINE_NAME}.jsonl" )
    fi
    aws s3 sync "s3://$BUCKET/$PREFIX/$root" "$LOCAL_DATA/$root" \
      --profile "$READ_PROFILE" --region "$REGION" \
      ${filters[@]+"${filters[@]}"} "${JUNK_ARGS[@]}" \
      ${pull_only[@]+"${pull_only[@]}"} \
      $DELETE --dryrun 2>/dev/null >> "$_plan" || true
    unset filters pull_only
  done

  # ⚠️ mkdir the snapshot root BEFORE writing the list. The first version of this guard
  # redirected into "$SNAP.list" while $SNAP did not exist yet: the redirect failed, the
  # loop produced nothing, and it printed "nothing existing would be replaced" while the
  # pull went on to destroy the canary file. A guard that cannot fire is worse than none.
  mkdir -p "$SNAP"
  : > "$SNAP.list"
  _n=0
  while IFS= read -r _rel; do
    [[ -n "$_rel" ]] || continue
    # Built from the S3 key, not from aws's printed destination: that is relative to this
    # script's directory ("../STATUS.md"), which needed path resolution and broke on spaces.
    _dst="$LOCAL_DATA/$_rel"
    [[ -f "$_dst" ]] || continue                        # new file: nothing to lose
    mkdir -p "$SNAP/$(dirname "$_rel")" 2>/dev/null || continue
    cp -p "$_dst" "$SNAP/$_rel" 2>/dev/null || continue
    _n=$((_n+1)); echo "$_rel" >> "$SNAP.list"
  done < <(_planned_rels "$_plan")

  if [[ "$_n" -gt 0 ]]; then
    echo "    ⚠️  $_n existing local file(s) will be REPLACED. Snapshot: $SNAP"
    head -25 "$SNAP.list" | sed 's/^/       /'
    [[ "$_n" -gt 25 ]] && echo "       ... and $((_n-25)) more (full list: $SNAP.list)"
    echo "    Undo the whole pull with:  cp -a \"$SNAP/.\" \"$LOCAL_DATA/\""
  else
    echo "    nothing existing would be replaced."
    rmdir "$SNAP" 2>/dev/null; rm -f "$SNAP.list" 2>/dev/null
  fi

  # Case-colliding keys: two S3 objects differing only in case map to ONE file on a
  # case-insensitive filesystem (APFS, the WSL/NTFS mount), so every pull picks a winner
  # at random. This destroyed a teammate's ticket doc on 2026-09-17.
  # Whole relative path, lower-cased (the old `cut -d' ' -f1` would have flagged "a b.docx" and
  # "a c.docx" as a collision once names with spaces reached this check).
  _dupes="$(_planned_rels "$_plan" | awk '{print tolower($0)}' | sort | uniq -d)"
  if [[ -n "$_dupes" ]]; then
    echo "" >&2
    echo "⛔ CASE-COLLIDING FILES — two bucket objects differ only in capitalisation and map" >&2
    echo "   to ONE local file here. The pull would pick a winner at random:" >&2
    sed 's/^/     /' <<<"$_dupes" >&2
    echo "   Delete the wrong-cased key in the bucket first. Canonical: lowercase sst-NNNN.md" >&2
    exit 3
  fi
fi

# Per-root sync (2026-09-04). aws s3 sync stats the WHOLE source tree before applying
# any --exclude, so pointing it at data/ pays for 20k node_modules files it will never
# upload. Walking only the roots in scope keeps purely-local trees free. JUNK_ARGS still
# runs last as the backstop for junk that lives INSIDE a synced root.
for root in "${SYNC_ROOTS[@]}"; do
  fvar="FILTERS_${root//-/_}"
  # `declare -n` (nameref) is bash 4.3+. Stock macOS ships bash 3.2, where it is an
  # "invalid option" and the sync dies on the first root -- after validate.sh has
  # already printed MACHINE READY. Expand the named array indirectly instead. The
  # ${a[@]+"${a[@]}"} guard is needed because most FILTERS_* are EMPTY arrays and
  # `set -u` treats "${empty[@]}" as unbound on bash < 4.4.
  filters=()
  eval "filters=( \${$fvar[@]+\"\${$fvar[@]}\"} )"

  # ⚠️ Never pull back THIS machine's own activity ledger. The bucket copy is uploaded
  # DURING a push, before that run appends its own record at exit, so it is always one
  # record behind local — and `aws s3 sync` transfers on a size difference, so a later
  # pull silently ROLLS THE AUDIT TRAIL BACK. Observed 2026-09-17: the 06:05Z push
  # record vanished and activity.sh then reported "last push FAILED" for a push that had
  # succeeded. A ledger that can lose entries is worse than none, because it is believed.
  # Other machines' ledgers are pulled normally — only our own is authoritative locally.
  pull_only=()
  if [[ "$root" == "changes" && -n "${MACHINE_NAME:-}" ]]; then
    pull_only=( --exclude "s3-sync/_activity/${MACHINE_NAME}.jsonl" )
  fi

  echo ">>> $root"
  aws s3 sync "s3://$BUCKET/$PREFIX/$root" "$LOCAL_DATA/$root" \
    --profile "$READ_PROFILE" --region "$REGION" \
    ${filters[@]+"${filters[@]}"} "${JUNK_ARGS[@]}" \
    ${pull_only[@]+"${pull_only[@]}"} \
    $DELETE $DRYRUN | tee -a "$ACTLOG"
  unset filters pull_only
done

# After the sync: a consumed/ twin that just arrived retires the local copy (_queue_reconcile.sh).
declare -f reconcile_refresh_queue >/dev/null 2>&1 && reconcile_refresh_queue "$DRYRUN"
_act_status="ok"
