#!/usr/bin/env bash
# Validate that THIS machine can use the shared data bucket end-to-end.
# Safe: touches only s3://$BUCKET/$PREFIX/_validate/<host>/ and cleans up.
# Run after install (START_HERE.md § "Setting up a machine"). Exit 0 = all PASS.
set -uo pipefail
cd "$(dirname "$0")"
source ./config.env

PASS=0; FAIL=0; EXPECTED=0
ok(){   printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS+1)); }
bad(){  printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAIL=$((FAIL+1)); }
# An expected denial is not a machine fault. Write access has been revoked for
# every machine since 2026-08-12 (config.env header), and a contributor never
# needed it. Counting those as failures produced a red NOT READY verdict on
# machines that are working exactly as intended, which trains the reader to
# ignore the verdict.
skip(){ printf '  \033[33mN/A \033[0m  %s\n' "$1"; EXPECTED=$((EXPECTED+1)); }
info(){ printf '        %s\n' "$1"; }

# Does this machine expect to be able to WRITE to the bucket? Publisher role and
# write access are separate things: the role says what it may push, WRITE_EXPECTED
# says whether the credentials currently allow it at all.
#
# ⚠️ DEFAULT FLIPPED 0 -> 1 on 2026-09-03, when TCK-1234 landed and the KnowledgeBaseS3
# role gained bucket write. This is not cosmetic. While the default was 0, a genuine
# PutObject denial was counted as "expected-denied" and the script still exited 0 — so
# running it to confirm the new grant would have reported success whether or not the
# grant existed. An instrument that cannot fail is not a gate. Set WRITE_EXPECTED=0
# explicitly only for a machine that is deliberately read-only.
WRITE_EXPECTED="${WRITE_EXPECTED:-1}"

# Reads use READ_PROFILE (config.env; defaults to PROFILE). A read-only joiner has only
# the read-only role on day one, sets READ_PROFILE to that profile, and must get a READY verdict
# for the read path. Until 2026-10-05 every check here used PROFILE, so that joiner saw
# "NOT READY" with 3 failures although pull worked (joiner review 2026-10-05).
READ_PROFILE="${READ_PROFILE:-$PROFILE}"
# Leniency applies ONLY to a machine that declares a separate read profile AND whose write
# profile does not resolve at all (role not granted / profile not configured yet). A machine
# with one profile (the publisher) keeps the strict path: a write failure is a FAIL.
WRITE_PROFILE_OK=1
if [[ "$READ_PROFILE" != "$PROFILE" ]] \
   && ! aws sts get-caller-identity --profile "$PROFILE" >/dev/null 2>&1; then
  WRITE_PROFILE_OK=0
fi

HOST="$(hostname -s 2>/dev/null || echo unknown)"
KEY="$PREFIX/_validate/$HOST/probe-$$.txt"
TMP="$(mktemp)"; RB="$(mktemp)"
trap 'rm -f "$TMP" "$RB"' EXIT
printf 'validate %s\n' "$HOST" > "$TMP"

echo "=== validating on host '$HOST' against s3://$BUCKET/$PREFIX (read=$READ_PROFILE, write=$PROFILE) ==="

# 1. tooling present
command -v aws  >/dev/null && ok "aws CLI present ($(aws --version 2>&1 | cut -d' ' -f1))" || bad "aws CLI missing"

# 2. identity + account
IDENT="$(aws sts get-caller-identity --profile "$READ_PROFILE" --query 'Account' --output text 2>&1)"
if [[ "$IDENT" =~ ^[0-9]{12}$ ]]; then ok "AWS identity OK (account $IDENT)"; else bad "AWS identity failed: $IDENT"; fi

# 3. object put / list / get / delete
if [[ "$WRITE_PROFILE_OK" -eq 1 ]] \
   && aws s3 cp "$TMP" "s3://$BUCKET/$KEY" --profile "$PROFILE" --region "$REGION" >/dev/null 2>&1; then
  ok "PutObject"
  aws s3 ls "s3://$BUCKET/$PREFIX/_validate/$HOST/" --profile "$PROFILE" >/dev/null 2>&1 \
    && ok "ListObjects" || bad "ListObjects"
  if aws s3 cp "s3://$BUCKET/$KEY" "$RB" --profile "$PROFILE" --region "$REGION" >/dev/null 2>&1 \
       && diff -q "$TMP" "$RB" >/dev/null 2>&1; then ok "GetObject (content matches)"; else bad "GetObject"; fi
  aws s3 rm "s3://$BUCKET/$KEY" --profile "$PROFILE" --region "$REGION" >/dev/null 2>&1 \
    && ok "DeleteObject (cleaned up)" || bad "DeleteObject (LEFTOVER: s3://$BUCKET/$KEY)"
else
  if [[ "$WRITE_PROFILE_OK" -eq 0 ]]; then
    skip "PutObject — write profile '$PROFILE' not usable yet (write role not granted or not logged in); read-only until it is"
    skip "DeleteObject — not attempted (no write profile)"
  elif [[ "$WRITE_EXPECTED" == "1" ]]; then
    bad "PutObject — profile '$PROFILE' cannot write. It must be the role with bucket write; re-login first: aws sso login"
  else
    skip "PutObject denied — expected: this profile is read-only (see config.env header)"
    skip "DeleteObject — not attempted (write denied)"
  fi
  # The read path is what a read-only machine actually depends on, so validate it
  # instead of skipping every remaining check. Previously a write denial aborted
  # the whole block and the machine was never read-tested at all.
  aws s3 ls "s3://$BUCKET/$PREFIX/" --profile "$READ_PROFILE" >/dev/null 2>&1 \
    && ok "ListObjects (read path)" || bad "ListObjects (read path)"
  # s3api, not `s3 ls | awk '{print $4}'`: that split a key with spaces at the first space and
  # then fetched a key that does not exist (2,737 of 6,129 keys contain spaces, 2026-10-05).
  FIRST_KEY="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "$PREFIX/changes/" \
                 --max-items 50 --profile "$READ_PROFILE" --region "$REGION" \
                 --query 'Contents[?Size > `0`].Key | [0]' --output text 2>/dev/null | head -n 1)"
  [[ "$FIRST_KEY" == "None" ]] && FIRST_KEY=""
  if [[ -n "$FIRST_KEY" ]]; then
    aws s3 cp "s3://$BUCKET/$FIRST_KEY" "$RB" --profile "$READ_PROFILE" --region "$REGION" >/dev/null 2>&1 \
      && [[ -s "$RB" ]] \
      && ok "GetObject (read path, fetched an existing object)" || bad "GetObject (read path)"
  else
    info "no object under the prefix yet — GetObject not exercised"
  fi
fi

# 4. mountpoint-s3 (optional but recommended)
if command -v mount-s3 >/dev/null 2>&1; then
  ok "mount-s3 present ($(mount-s3 --version 2>&1))"
  # live read-only mount round-trip (needs at least one object under the prefix)
  mkdir -p "$MOUNT_DIR"
  if mountpoint -q "$MOUNT_DIR"; then fusermount3 -u "$MOUNT_DIR" 2>/dev/null; fi
  if mount-s3 "$BUCKET" "$MOUNT_DIR" --profile "$READ_PROFILE" --region "$REGION" \
        --prefix "$PREFIX/" --read-only >/dev/null 2>&1; then
    ls "$MOUNT_DIR" >/dev/null 2>&1 && ok "read-only mount lists" || bad "mount present but cannot list"
    fusermount3 -u "$MOUNT_DIR" 2>/dev/null && ok "unmount clean" || bad "unmount failed (run: fusermount3 -u $MOUNT_DIR)"
  else
    bad "mount failed (creds/prefix?) — writes still work via data-push"
  fi
else
  info "mount-s3 not installed (optional) — install per §2.2 to enable the read-only mount"
fi

# identity card (who am I + role) — reuses identity.sh if present
if [[ -x ./identity.sh ]]; then echo; ./identity.sh || true; fi

echo
echo "=== result: $PASS passed, $FAIL failed, $EXPECTED expected-denied ==="
if [[ "$FAIL" -ne 0 ]]; then
  echo "NOT READY ❌ — see failures above"; exit 1
elif [[ "$EXPECTED" -ne 0 ]]; then
  echo "MACHINE READY ✅ (read-only — $EXPECTED write operation(s) denied as expected)"
  echo "   Pull works; push does not yet. When the write role lands: log in to its profile and re-run this."
  exit 0
else
  echo "MACHINE READY ✅ (read + write)"; exit 0
fi
