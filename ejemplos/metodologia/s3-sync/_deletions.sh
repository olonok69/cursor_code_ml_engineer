# Deletion list helper — sourced by data-pull.sh, data-push.sh and delete.sh.
#
# The list lives at s3://$BUCKET/$PREFIX/_deletions.jsonl, OUTSIDE every synced root (like _publisher.json), and is
# touched only by direct s3api calls. Inside a synced root, the first contributor push would replace it with a stale
# copy. Only delete.sh (publisher + baton) writes it; entries are appended, never edited.
# Design: README.md, point 6 ("Deleted on purpose")
#
# ⚠️ Reading follows the baton rule (publisher.sh fetch, 2026-09-08): a 404 means "no deletions yet"; ANY other
# failure is "unreadable" and must never be treated as an empty list.
# bash 3.2 safe (stock macOS): no namerefs, no mapfile.

DELETIONS_KEY="$PREFIX/_deletions.jsonl"
DELETIONS_FILE=""
DELETIONS_ETAG=""
DEL_EXCL=()
DEL_MOVED=0
DEL_KEPT=0

deletions_fetch() {
  local prof="${1:-${READ_PROFILE:-$PROFILE}}" out rc
  DELETIONS_FILE="$(mktemp)"
  out="$(aws s3api get-object --bucket "$BUCKET" --key "$DELETIONS_KEY" "$DELETIONS_FILE" \
         --profile "$prof" --region "$REGION" --query ETag --output text 2>&1)" && rc=0 || rc=$?
  if [[ $rc -eq 0 ]]; then DELETIONS_ETAG="$out"; return 0; fi
  # Only S3's own "no such key" answers count as absent. NOT a bare "does not exist" / "Not Found": botocore says
  # "Token for <session> does not exist" after `aws sso logout`, which would read an unreadable list as empty.
  if grep -qE '(NoSuchKey)|(An error occurred \(404\))' <<<"$out"; then
    : > "$DELETIONS_FILE"; DELETIONS_ETAG=""; return 0
  fi
  echo "⛔ could not read the deletion list s3://$BUCKET/$DELETIONS_KEY — this is NOT 'no deletions':" >&2
  printf '%s\n' "$out" | tail -2 | sed 's/^/   /' >&2
  echo "   If the token expired: aws sso logout && aws sso login" >&2
  return 1
}

deletions_py() {
  python3 - "$DELETIONS_FILE" "$@" <<'PY'
import json, re, sys
path, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
latest = {}
try:
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.strip():
            e = json.loads(line)
            latest[e["path"]] = e
except (ValueError, KeyError) as exc:
    sys.stderr.write(f"deletion list line {n} is corrupt: {exc}\n"); sys.exit(3)
tomb = sorted(p for p, e in latest.items() if e.get("op") == "delete")
esc = lambda s: re.sub(r"([\[\]*?])", lambda m: "[" + m.group(1) + "]", s)
if cmd == "tombstoned":
    print("\n".join(tomb)) if tomb else None
elif cmd == "excludes":
    pre = args[0].rstrip("/") + "/"
    out = [esc(p[len(pre):]) for p in tomb if p.startswith(pre)]
    print("\n".join(out)) if out else None
elif cmd == "field":
    v = latest.get(args[0], {}).get(args[1])
    print("" if v is None else v)
elif cmd == "append":
    json.loads(args[0])  # refuse to append something that is not JSON
    sys.stdout.write(open(path, encoding="utf-8").read().rstrip("\n") + ("\n" if latest else "") + args[0] + "\n")
else:
    sys.exit(2)
PY
}

deletions_exclude_args() {
  DEL_EXCL=()
  local x
  while IFS= read -r x; do
    [[ -n "$x" ]] && DEL_EXCL+=( --exclude "$x" )
  done < <(deletions_py excludes "$1")
}

_del_md5() {
  if command -v md5sum >/dev/null 2>&1; then md5sum "$1" 2>/dev/null | awk '{print $1}'
  elif command -v md5 >/dev/null 2>&1; then md5 -q "$1" 2>/dev/null
  else python3 -c "import hashlib,sys;print(hashlib.md5(open(sys.argv[1],'rb').read()).hexdigest())" "$1"
  fi
}
_del_size() { python3 -c "import os,sys;print(os.path.getsize(sys.argv[1]))" "$1"; }

deletions_apply_local() {
  local data="$1" snap="$2" mode="$3" p f want_md5 want_size reason
  DEL_MOVED=0; DEL_KEPT=0
  local moved_list="" kept_list=""
  while IFS= read -r p; do
    [[ -n "$p" ]] || continue
    f="$data/$p"
    [[ -f "$f" ]] || continue
    want_md5="$(deletions_py field "$p" md5)"; want_size="$(deletions_py field "$p" size)"
    reason="$(deletions_py field "$p" reason)"
    if { [[ -n "$want_md5" ]] && [[ "$(_del_md5 "$f")" == "$want_md5" ]]; } ||
       { [[ -z "$want_md5" && -n "$want_size" ]] && [[ "$(_del_size "$f")" == "$want_size" ]]; }; then
      if [[ "$mode" == "go" ]]; then
        mkdir -p "$snap/deleted/$(dirname "$p")" && mv "$f" "$snap/deleted/$p"
      fi
      DEL_MOVED=$((DEL_MOVED+1)); moved_list+="       $p — $reason"$'\n'
    else
      DEL_KEPT=$((DEL_KEPT+1))
      kept_list+="    ⚠️  $p was deleted upstream but your copy differs — kept. Ask the publisher, or delete it yourself."$'\n'
    fi
  done < <(deletions_py tombstoned)
  if [[ $DEL_MOVED -gt 0 ]]; then
    if [[ "$mode" == "go" ]]; then
      echo ">>> $DEL_MOVED file(s) deleted upstream (moved to $snap/deleted/):"
    else
      echo ">>> $DEL_MOVED file(s) deleted upstream (a real pull would move them aside):"
    fi
    printf '%s' "$moved_list"
  fi
  [[ $DEL_KEPT -gt 0 ]] && printf '%s' "$kept_list"
  return 0
}
