#!/bin/bash
# Emergency Clone Script
set -e

BACKUP_FILE="/Users/KS/.openclaw/workspace/system_clones/Gateway_Patch_Pre_Snapshot.tar.gz"
TARGETS=(
    "/Users/KS/.openclaw"
    "/Users/KS/.agents/skills"
    "/opt/homebrew/lib/node_modules/openclaw"
    "/Users/KS/Library/LaunchAgents"
)

echo "Stopping Gateway..."
openclaw gateway stop || true

echo "Starting Clone..."
# Use -C / and remove leading slash from targets to avoid macOS tar issues
TARGETS_STR=""
for t in "${TARGETS[@]}"; do
    TARGETS_STR="$TARGETS_STR ${t#/}"
done

tar -cpzf "$BACKUP_FILE" -C / $TARGETS_STR

echo "Starting Gateway..."
openclaw gateway start

echo "Verification..."
if [ -f "$BACKUP_FILE" ]; then
    echo "SUCCESS: Backup created at $BACKUP_FILE"
    ls -lh "$BACKUP_FILE"
else
    echo "FAILURE: Backup file not found"
    exit 1
fi
