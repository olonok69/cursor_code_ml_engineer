#!/usr/bin/env bash
# Delete ONE file from the shared bucket on purpose, and record it so every machine follows.
#
#   ./delete.sh <path-under-data> "<reason>"              # dry run (default): shows what would happen
#   ./delete.sh --go <path> "<reason>"                    # delete + record
#   ./delete.sh --go --record-only <path> "<reason>"      # record a deletion already done by hand
#   ./delete.sh --go --restore <path> "<reason>"          # lift a deletion (uploads nothing)
#   ./delete.sh [--go] --from FILE "<reason>"             # one path per line, one confirmation
#   ./delete.sh --list                                    # current deletions
#   ./delete.sh --check                                   # deleted files that are back in the bucket (report only)
#
# Publisher only, and only while this machine holds the baton. Single files only — no wildcards, no folders.
# Why: `aws s3 sync` cannot express "deleted on purpose", so a deletion reached nobody and the next push from any
# machine re-uploaded it (a 176 MB recording came back twice, 2026-10-08 and 10-09).
# Design: README.md, point 6 ("Deleted on purpose")
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env
[[ -r ./_activity_log.sh ]] && source ./_activity_log.sh || true
source ./_deletions.sh

GO=0; MODE=delete; FROM=""; ACTION=""
POS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --go) GO=1 ;;
    --record-only) MODE=record ;;
    --restore) MODE=restore ;;
    --from) shift; FROM="${1:-}" ;;
    --list) ACTION=list ;;
    --check) ACTION=check ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) POS+=( "$1" ) ;;
  esac
  shift
done

if ! deletions_fetch "${READ_PROFILE:-$PROFILE}"; then exit 5; fi
if ! TOMB="$(deletions_py tombstoned)"; then exit 5; fi

if [[ "$ACTION" == "list" ]]; then
  [[ -z "$TOMB" ]] && { echo "no deletions recorded"; exit 0; }
  while IFS= read -r p; do
    echo "$p   ($(deletions_py field "$p" ts), $(deletions_py field "$p" by)) — $(deletions_py field "$p" reason)"
  done <<<"$TOMB"
  exit 0
fi

if [[ "$ACTION" == "check" ]]; then
  found=0
  while IFS= read -r p; do
    [[ -n "$p" ]] || continue
    lm="$(aws s3api head-object --bucket "$BUCKET" --key "$PREFIX/$p" --query LastModified --output text \
          --profile "${READ_PROFILE:-$PROFILE}" --region "$REGION" 2>/dev/null)" || continue
    found=$((found+1))
    who="$(python3 - "$lm" "${ACTIVITY_DIR:-./_activity}" <<'PY'
import datetime as dt, glob, json, os, sys
t = dt.datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
hits = set()
for f in glob.glob(os.path.join(sys.argv[2], "*.jsonl")):
    for line in open(f, encoding="utf-8"):
        try:
            e = json.loads(line)
            ts = dt.datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
        except Exception:
            continue
        if e.get("op") == "push" and e.get("mode") == "go" and abs((ts - t).total_seconds()) <= 600:
            hits.add(e.get("machine", "?"))
print(", ".join(sorted(hits)) or "no recorded push within 10 min")
PY
)"
    echo "⚠️  BACK IN THE BUCKET: $p  (uploaded $lm; pushes around then: $who)"
    echo "    re-apply:  ./delete.sh --go \"$p\" \"$(deletions_py field "$p" reason)\""
  done <<<"$TOMB"
  [[ $found -eq 0 ]] && echo "deletions check: all $(printf '%s\n' "$TOMB" | grep -c . ) deleted file(s) still absent"
  exit 0
fi

# ---- mutating modes ----
if [[ -n "$FROM" ]]; then
  [[ -r "$FROM" ]] || { echo "cannot read $FROM" >&2; exit 2; }
  REASON="${POS[0]:-}"; PATHS=()
  while IFS= read -r l; do [[ -n "$l" ]] && PATHS+=( "$l" ); done < "$FROM"
else
  [[ ${#POS[@]} -eq 2 ]] || { echo "usage: $0 [--go] [--record-only|--restore] <path-under-data> \"<reason>\"" >&2; exit 2; }
  PATHS=( "${POS[0]}" ); REASON="${POS[1]}"
fi
[[ -n "$REASON" ]] || { echo "a reason is required" >&2; exit 2; }

if [[ "$MACHINE_ROLE" != "publisher" ]]; then
  echo "REFUSED: only the publisher deletes from the shared record (this machine: $MACHINE_ROLE)." >&2; exit 3
fi
baton_out="$(aws s3 cp "s3://$BUCKET/$PREFIX/_publisher.json" - --profile "$PROFILE" --region "$REGION" 2>&1)" \
  || { echo "REFUSED: could not read the publisher baton — re-login and retry." >&2; exit 3; }
holder="$(printf '%s' "$baton_out" | python3 -c "import json,sys;print(json.load(sys.stdin).get('holder') or '')" 2>/dev/null || true)"
if [[ "$holder" != "$MACHINE_NAME" ]]; then
  echo "REFUSED: the publisher baton is held by '${holder:-nobody}', not '$MACHINE_NAME'." >&2; exit 3
fi

valid_path() {
  local p="$1"
  [[ -n "$p" && "$p" != /* && "$p" != */ && "$p" != *..* && "$p" != *"*"* && "$p" != *"?"* && "$p" == */* ]]
}
for p in "${PATHS[@]}"; do
  valid_path "$p" || { echo "REFUSED: not a plain file path under data/: '$p'" >&2; exit 3; }
done

[[ $GO -eq 0 ]] && echo ">>> DRY RUN — nothing is deleted or recorded. Re-run with --go."
SNAP="$LOCAL_DATA/_prepull/$(date -u +%Y%m%d-%H%M%S)"
rc_all=0
for p in "${PATHS[@]}"; do
  key="$PREFIX/$p"
  # Case collision / folder check: any other key that equals this one ignoring case, or sits under it.
  siblings="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "$PREFIX/$(dirname "$p")/" \
              --query 'Contents[].Key' --output text --profile "$PROFILE" --region "$REGION" 2>/dev/null | tr '\t' '\n')"
  # Keys go in through a file: stdin already carries the program (a second `<<<` would replace it), and an
  # environment variable overflows the argument limit for a folder like changes/ with thousands of keys.
  sibfile="$(mktemp)"; printf '%s\n' "$siblings" > "$sibfile"
  clash="$(python3 - "$key" "$sibfile" <<'PY'
import sys
key = sys.argv[1]; low = key.lower()
for k in (l.strip() for l in open(sys.argv[2], encoding="utf-8")):
    if k and k != key and (k.lower() == low or k.startswith(key + "/")):
        print(k)
PY
)"
  rm -f "$sibfile"
  if [[ -n "$clash" ]]; then
    echo "REFUSED: $p — another key differs only in case or sits under it:" >&2; printf '   %s\n' $clash >&2; exit 3
  fi

  head="$(aws s3api head-object --bucket "$BUCKET" --key "$key" --query '[ETag,ContentLength,VersionId]' \
          --output text --profile "$PROFILE" --region "$REGION" 2>/dev/null || true)"
  case "$MODE" in
    delete)  [[ -n "$head" ]] || { echo "REFUSED: $p is not in the bucket (use --record-only)" >&2; exit 3; } ;;
    record)  [[ -z "$head" ]] || { echo "REFUSED: $p is still in the bucket (drop --record-only)" >&2; exit 3; } ;;
    restore) grep -qxF "$p" <<<"$TOMB" || { echo "REFUSED: $p is not a recorded deletion" >&2; exit 3; } ;;
  esac

  md5=null; size=null; ver=null
  if [[ "$MODE" != restore ]]; then
    if [[ -f "$LOCAL_DATA/$p" ]]; then
      md5="\"$(_del_md5 "$LOCAL_DATA/$p")\""; size="$(_del_size "$LOCAL_DATA/$p")"
    elif [[ -n "$head" ]]; then
      etag="$(awk -F'\t' '{print $1}' <<<"$head" | tr -d '"')"; size="$(awk -F'\t' '{print $2}' <<<"$head")"
      [[ "$etag" != *-* ]] && md5="\"$etag\""            # multipart ETags are not md5s
    fi
    [[ -n "$head" ]] && ver="\"$(awk -F'\t' '{print $3}' <<<"$head")\""
  fi
  op=delete; [[ "$MODE" == restore ]] && op=restore
  entry="$(python3 -c 'import json,sys,datetime as d
a=sys.argv
print(json.dumps({"ts": d.datetime.now(d.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "op": a[1], "path": a[2],
  "by": a[3], "reason": a[4], "md5": json.loads(a[5]), "size": json.loads(a[6]), "version_id": json.loads(a[7])}))' \
  "$op" "$p" "$MACHINE_NAME" "$REASON" "$md5" "$size" "$ver")"

  echo ">>> $op: $p"; echo "    reason: $REASON"
  [[ $GO -eq 1 ]] || continue

  if [[ "$MODE" == delete ]]; then
    aws s3api delete-object --bucket "$BUCKET" --key "$key" --profile "$PROFILE" --region "$REGION" >/dev/null
  fi
  newlist="$(mktemp)"
  deletions_fetch "$PROFILE" && deletions_py append "$entry" > "$newlist" && TOMB="$(deletions_py tombstoned)" || true
  put_ok=0
  if [[ -s "$newlist" ]]; then
    cond=( --if-none-match "*" ); [[ -n "$DELETIONS_ETAG" ]] && cond=( --if-match "$DELETIONS_ETAG" )
    if aws s3api put-object --bucket "$BUCKET" --key "$DELETIONS_KEY" --body "$newlist" "${cond[@]}" \
         --profile "$PROFILE" --region "$REGION" >/dev/null 2>"$newlist.err"; then put_ok=1
    elif grep -qi 'Unknown options' "$newlist.err" &&
         aws s3api put-object --bucket "$BUCKET" --key "$DELETIONS_KEY" --body "$newlist" \
           --profile "$PROFILE" --region "$REGION" >/dev/null 2>>"$newlist.err"; then put_ok=1   # CLI without conditional writes
    fi
  fi
  if [[ $put_ok -ne 1 ]]; then
    echo "⛔ $p: the deletion was NOT recorded in the list$([[ "$MODE" == delete ]] && echo ' (the bucket object IS deleted)')." >&2
    echo "   Append this line to s3://$BUCKET/$DELETIONS_KEY by re-running, or by hand:" >&2
    echo "   $entry" >&2
    rc_all=6; continue
  fi
  if [[ "$MODE" != restore && -f "$LOCAL_DATA/$p" ]]; then
    mkdir -p "$SNAP/deleted/$(dirname "$p")" && mv "$LOCAL_DATA/$p" "$SNAP/deleted/$p"
    echo "    local copy moved to $SNAP/deleted/$p"
  fi
  declare -f activity_log >/dev/null 2>&1 && activity_log "$op" go 0 ok 1 || true
done
exit $rc_all
