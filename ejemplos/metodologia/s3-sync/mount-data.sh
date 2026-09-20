#!/usr/bin/env bash
# Mount the shared data/ prefix as a READ-ONLY local folder via mountpoint-s3.
#
# Read-only is deliberate: mountpoint-s3 has no file locking and can't rename
# or do partial writes, so running git / KG-refresh directly on the mount is
# unreliable. Use the mount to BROWSE/READ the shared data live; do WRITES on
# your real local disk and publish them with ./data-push.sh --go.
#
# Usage:
#   ./mount-data.sh          # mount read-only at $MOUNT_DIR
#   ./unmount-data.sh        # unmount
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env

if ! command -v mount-s3 >/dev/null 2>&1; then
  echo "mount-s3 not installed. Install it first:" >&2
  echo "  sudo apt-get install ./mount-s3.deb   (see README.md)" >&2
  exit 1
fi

mkdir -p "$MOUNT_DIR"

if mountpoint -q "$MOUNT_DIR"; then
  echo "Already mounted at $MOUNT_DIR"
  exit 0
fi

echo ">>> mounting s3://$BUCKET/$PREFIX  (read-only)  ->  $MOUNT_DIR"
mount-s3 "$BUCKET" "$MOUNT_DIR" \
  --profile "$PROFILE" \
  --region "$REGION" \
  --prefix "$PREFIX/" \
  --read-only

echo ">>> mounted. Browse it:  ls -la $MOUNT_DIR"
echo ">>> unmount with:        ./unmount-data.sh"
