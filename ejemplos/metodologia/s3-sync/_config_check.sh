#!/usr/bin/env bash
# Fail a sync with an ACTIONABLE message when config.env is incomplete.
#
# Sourced by data-pull.sh / data-push.sh immediately after config.env.
#
# Why (2026-09-16): both scripts run under `set -u` and use SYNC_ROOTS / JUNK_ARGS /
# READ_PROFILE / LEDGERS. The shipped templates predated the 2026-09-04 per-root sync
# model and defined none of them, so a new joiner's FIRST command died with a bare
# "unbound variable" naming an internal array — unreadable, and indistinguishable from
# a broken install. Nobody noticed because no contributor machine had ever run it.
# A cryptic abort on the first command is how an onboarding path dies quietly.

_cfg_fail() {
  echo "" >&2
  echo "✖ config.env is incomplete: $1" >&2
  echo "" >&2
  echo "  Your config.env predates the current sync model (per-root sync, 2026-09-04)." >&2
  echo "  Regenerate it from the shipped template and re-enter your machine's values:" >&2
  echo "" >&2
  echo "      cp templates/config.corporate.env config.env   # then edit the <PLACEHOLDERS>" >&2
  echo "      ./identity.sh --write" >&2
  echo "      ./validate.sh" >&2
  echo "" >&2
  exit 2
}

for _v in BUCKET PREFIX REGION PROFILE READ_PROFILE LOCAL_DATA MACHINE_NAME MACHINE_ROLE; do
  [[ -n "${!_v:-}" ]] || _cfg_fail "\$$_v is not set"
done
unset _v

for _a in SYNC_ROOTS JUNK_ARGS; do
  declare -p "$_a" >/dev/null 2>&1 || _cfg_fail "the \$$_a array is not defined"
done
unset _a

[[ -d "$LOCAL_DATA" ]] || _cfg_fail "LOCAL_DATA points at '$LOCAL_DATA', which does not exist"
