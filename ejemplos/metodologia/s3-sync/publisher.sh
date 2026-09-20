#!/usr/bin/env bash
# Who currently holds the KG publisher role — an advisory lock kept IN the bucket.
#
#   ./publisher.sh status        # who holds it right now
#   ./publisher.sh claim "why"   # take the baton (fails if someone else holds it)
#   ./publisher.sh claim --force "why"
#   ./publisher.sh release       # hand it back (leaves holder empty)
#
# Why this exists: `aws s3 sync` is last-writer-wins with no merge, so two machines
# refreshing the KG both produce a different graph AND a different
# community_labels.json — 102 hand-authored names that nothing can regenerate.
# REFRESH_OWNERSHIP.md calls single-writer "a workaround for the absence of a merge".
# This turns that convention from something both machines must REMEMBER into
# something either machine can CHECK.
#
# Advisory, not a real lock: --force exists, and the bucket has versioning on as the
# backstop. The point is that a mistake becomes visible, not impossible.
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env

KEY="$PREFIX/_publisher.json"
S3="s3://$BUCKET/$KEY"
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT

# ⚠️⚠️ fetch() MUST distinguish "the baton object does not exist" (genuinely nobody holds
# it) from "the read failed" (expired token, denied, no network). It did not until
# 2026-09-08: any failure was swallowed into '{}', so `status` printed "(nobody holds the
# baton)" on an expired SSO token — and, far worse, `claim` saw no holder and SUCCEEDED
# against a baton someone else was holding. That is exactly the two-publishers case this
# script exists to prevent. Same family as the 2026-09-04 filter defects: an instrument
# that cannot fail tells you nothing when it reports clean.
fetch() {
  local err rc
  # `set -e` is active: a bare failing assignment aborts the script before rc is read.
  # NOT --quiet: it suppresses the error text, and the 404 message is the ONLY thing that
  # distinguishes "never claimed" from "the read failed". With --quiet a genuine 404 came
  # back as rc=1 with an EMPTY message and was classified as a hard failure. Caught by the
  # known-answer canary, not by review.
  err="$(aws s3 cp "$S3" "$TMP" --profile "$READ_PROFILE" --region "$REGION" 2>&1)" && rc=0 || rc=$?
  if [[ $rc -eq 0 ]]; then
    return 0
  fi
  # 404 on the key is the ONLY acceptable failure: the baton has never been claimed.
  if grep -qiE '(404)|(Not Found)|(NoSuchKey)|(does not exist)' <<<"$err"; then
    echo '{}' > "$TMP"
    return 0
  fi
  echo "ERROR: could not read the publisher baton at $S3" >&2
  echo "$err" >&2
  echo >&2
  echo "This is NOT 'nobody holds the baton' — the read itself failed. If this is an" >&2
  echo "expired token, re-login and try again; do not claim past it:" >&2
  echo "  aws sso logout && aws sso login --profile $READ_PROFILE" >&2
  exit 2
}
holder() { python3 -c "import json,sys;print(json.load(open('$TMP')).get('holder') or '')"; }

case "${1:-status}" in
  status)
    fetch
    H="$(holder)"
    if [[ -z "$H" ]]; then
      echo "publisher: (nobody holds the baton)"
    else
      python3 - <<PY
import json
d=json.load(open("$TMP"))
print(f"publisher : {d.get('holder')}")
print(f"claimed   : {d.get('claimed_at')}")
print(f"reason    : {d.get('reason','')}")
PY
    fi
    echo "this machine: $MACHINE_NAME (role=$MACHINE_ROLE)"
    ;;

  claim)
    shift
    FORCE=0
    if [[ "${1:-}" == "--force" ]]; then FORCE=1; shift; fi
    REASON="${1:-}"
    fetch
    H="$(holder)"
    if [[ -n "$H" && "$H" != "$MACHINE_NAME" && $FORCE -eq 0 ]]; then
      echo "REFUSED: '$H' holds the publisher baton." >&2
      echo "Have that machine run './publisher.sh release', or re-run with --force if you" >&2
      echo "are certain it is idle. Two publishers destroy community_labels.json silently." >&2
      exit 1
    fi
    python3 - <<PY > "$TMP"
import json
print(json.dumps({
  "holder": "$MACHINE_NAME",
  "claimed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "reason": """$REASON""",
  "note": "Advisory lock. Only the holder may run /kg-refresh, push knowledge-graph/, or use --delete.",
}, indent=2))
PY
    aws s3 cp "$TMP" "$S3" --profile "$PROFILE" --region "$REGION" --quiet
    echo "publisher baton -> $MACHINE_NAME"
    ;;

  release)
    fetch
    H="$(holder)"
    if [[ -n "$H" && "$H" != "$MACHINE_NAME" ]]; then
      echo "REFUSED: baton is held by '$H', not '$MACHINE_NAME'." >&2; exit 1
    fi
    python3 - <<PY > "$TMP"
import json
print(json.dumps({
  "holder": "",
  "released_by": "$MACHINE_NAME",
  "released_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
}, indent=2))
PY
    aws s3 cp "$TMP" "$S3" --profile "$PROFILE" --region "$REGION" --quiet
    echo "publisher baton released by $MACHINE_NAME"
    ;;

  *) echo "usage: $0 [status|claim [--force] \"why\"|release]" >&2; exit 2 ;;
esac
