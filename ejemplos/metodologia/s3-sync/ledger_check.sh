#!/usr/bin/env bash
# Warn when a line present in a LOCAL append-only ledger is absent from the copy in S3.
#
#   ./ledger_check.sh            # check every ledger in $LEDGERS
#   ./ledger_check.sh --quiet    # only print when something is missing
#   ./ledger_check.sh --self-test  # prove the check can actually FAIL
#
# Why this exists: the bucket has versioning on and a 30-day noncurrent expiry, so an
# overwrite is RECOVERABLE — but nothing tells you it happened. `aws s3 sync` is
# last-writer-wins with no merge, so a colleague rewriting STATUS.md instead of appending
# to it silently drops your row and you find out when you go looking. The ledgers are
# append-only by convention, which makes the test sound: a line that was in your copy and
# is not in theirs is either a clobber or a deliberate deletion. Both are worth seeing.
#
# It is ADVISORY. It never blocks a pull and never edits anything. Recovery is manual:
#   aws s3api list-object-versions --bucket "$BUCKET" --prefix "$PREFIX/<file>"
#   aws s3api copy-object --copy-source "$BUCKET/$PREFIX/<file>?versionId=<id>" ...
# and only works for 30 days.
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env

QUIET=0
SELFTEST=0
for a in "$@"; do
  case "$a" in
    --quiet)     QUIET=1 ;;
    --self-test) SELFTEST=1 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# Lines in $1 that do not appear anywhere in $2, ignoring blank/whitespace-only lines.
missing_lines() {
  local mine="$1" theirs="$2"
  grep -Fxv -f "$theirs" "$mine" 2>/dev/null | grep -vE '^[[:space:]]*$' || true
}

# Fetch one ledger and say WHICH of three things happened. This exists because the
# original code did `if ! aws s3 cp … 2>/dev/null; then echo "not in the bucket yet"`,
# which reports ABSENCE for every possible failure — an expired SSO token, a denied
# read, no network. On 2026-09-11 that printed "(no ledgers in the bucket yet)" for all
# five while the bucket held every one of them; believed, it reads as catastrophic data
# loss. `publisher.sh` was hardened against exactly this and says so out loud.
#
# A missing key is a real answer about the bucket. A failed read is an answer about the
# CALLER, and must never be dressed up as one about the bucket.
#   echoes: ok | absent | failed   (stderr of a failure is left in $TMP/lasterr)
fetch_ledger() {
  local key="$1" dest="$2" err
  if err="$(aws s3 cp "$key" "$dest" \
              --profile "$READ_PROFILE" --region "$REGION" --quiet 2>&1 >/dev/null)"; then
    echo ok; return 0
  fi
  printf '%s\n' "$err" > "$TMP/lasterr"
  classify_s3_error "$err"
}

# Split out so --self-test can exercise it against real AWS error text without a network.
# Only these mean "the object is not there". Everything else is a broken read.
classify_s3_error() {
  if grep -qiE '404|NoSuchKey|Not Found|does not exist' <<<"$1"; then
    echo absent
  else
    echo failed
  fi
}

if [[ $SELFTEST -eq 1 ]]; then
  # Gate 0: the instrument must be shown able to FAIL before any PASS is believed.
  printf 'alpha\nbeta\ngamma\n'  > "$TMP/mine"
  printf 'alpha\ngamma\n'        > "$TMP/theirs"
  got="$(missing_lines "$TMP/mine" "$TMP/theirs")"
  [[ "$got" == "beta" ]] || { echo "SELF-TEST FAILED: expected 'beta', got '$got'" >&2; exit 1; }
  printf 'alpha\nbeta\n' > "$TMP/theirs2"
  cp "$TMP/theirs2" "$TMP/mine2"
  got2="$(missing_lines "$TMP/mine2" "$TMP/theirs2")"
  [[ -z "$got2" ]] || { echo "SELF-TEST FAILED: identical files reported '$got2'" >&2; exit 1; }
  # The read classifier is an instrument too, and it is the one that was wrong on
  # 2026-09-11. Canary it against REAL AWS error text, both directions.
  expired='fatal error: Error when retrieving token from sso: Token has expired and refresh failed'
  denied='fatal error: An error occurred (AccessDenied) when calling the GetObject operation: Access Denied'
  notfound='fatal error: An error occurred (404) when calling the HeadObject operation: Key "x" does not exist'
  nosuchkey='An error occurred (NoSuchKey) when calling the GetObject operation: The specified key does not exist.'
  for pair in "expired:failed" "denied:failed" "notfound:absent" "nosuchkey:absent"; do
    var="${pair%%:*}"; want="${pair##*:}"
    got="$(classify_s3_error "${!var}")"
    [[ "$got" == "$want" ]] || {
      echo "SELF-TEST FAILED: $var classified '$got', expected '$want'" >&2
      echo "  (an expired token must NEVER be reported as 'not in the bucket')" >&2
      exit 1; }
  done
  echo "self-test PASS — detects a dropped line, is silent on identical files,"
  echo "                 and tells a failed read apart from a missing object"
  exit 0
fi

rc=0
checked=0
unreadable=0
for rel in "${LEDGERS[@]}"; do
  local_file="$LOCAL_DATA/$rel"
  [[ -f "$local_file" ]] || continue
  remote="$TMP/$(echo "$rel" | tr '/' '_')"
  case "$(fetch_ledger "s3://$BUCKET/$PREFIX/$rel" "$remote")" in
    absent)
      [[ $QUIET -eq 1 ]] || echo "  skip  $rel (not in the bucket yet)"
      continue ;;
    failed)
      # NOT suppressed by --quiet: a check that could not run is exactly what quiet
      # mode must never hide.
      echo "ERROR  $rel — could NOT be read from the bucket:" >&2
      sed 's/^/    /' "$TMP/lasterr" >&2
      unreadable=$((unreadable+1))
      continue ;;
  esac
  checked=$((checked+1))
  gone="$(missing_lines "$local_file" "$remote")"
  if [[ -n "$gone" ]]; then
    n="$(printf '%s\n' "$gone" | wc -l)"
    echo "WARNING  $rel — $n line(s) in your copy are NOT in the bucket copy:" >&2
    printf '%s\n' "$gone" | head -5 | sed 's/^/    /' >&2
    [[ "$n" -gt 5 ]] && echo "    … $((n-5)) more" >&2
    rc=1
  else
    [[ $QUIET -eq 1 ]] || echo "  ok    $rel"
  fi
done

if [[ $rc -eq 1 ]]; then
  echo "" >&2
  echo "Your rows may have been overwritten. The bucket keeps prior versions for 30 DAYS ONLY:" >&2
  echo "  aws s3api list-object-versions --bucket $BUCKET --prefix $PREFIX/<file> --profile $READ_PROFILE" >&2
  echo "Nothing was changed. This is advisory — you own your own work." >&2
elif [[ $checked -eq 0 && $unreadable -eq 0 && $QUIET -eq 0 ]]; then
  echo "  (no ledgers in the bucket yet — nothing to compare)"
fi

if [[ $unreadable -gt 0 ]]; then
  echo "" >&2
  echo "$unreadable ledger(s) could NOT be read. This is NOT 'absent from the bucket' — the" >&2
  echo "read itself failed, so nothing above is evidence about what the bucket holds." >&2
  echo "If the error mentions an expired token, re-login and run this again:" >&2
  echo "  aws sso logout && aws sso login --profile $READ_PROFILE" >&2
  echo "Do not claim past this: a failed read tells you about THIS MACHINE, not the bucket." >&2
  exit 3
fi
exit 0
