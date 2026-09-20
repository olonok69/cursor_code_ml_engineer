#!/usr/bin/env bash
# Unmount the read-only mountpoint-s3 view.
set -euo pipefail
cd "$(dirname "$0")"
source ./config.env

if mountpoint -q "$MOUNT_DIR"; then
  fusermount3 -u "$MOUNT_DIR"
  echo ">>> unmounted $MOUNT_DIR"
else
  echo ">>> $MOUNT_DIR is not mounted"
fi
