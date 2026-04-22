#!/bin/bash
#===============================================================================
# restore.sh: 全量系統恢復工具 (The All-in-One Restore)
# 目的：在新電腦上 100% 還原 OpenClaw 的所有自定義設定與狀態
#===============================================================================
set -e

WORKSPACE="/Users/KS/.openclaw/workspace"
SNAPSHOT_FILE="$WORKSPACE/system_snapshot.tar.gz"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🔄 Starting Full System Restore..."

# Step 1: Restore Snapshot
if [ ! -f "$SNAPSHOT_FILE" ]; then
    echo "[!] Snapshot file not found. Please run sync on the old machine first."
    exit 1
fi

TMP_RESTORE_DIR="/tmp/openclaw_restore"
mkdir -p "$TMP_RESTORE_DIR"
tar -xzf "$SNAPSHOT_FILE" -C "$TMP_RESTORE_DIR"

# 1. Restore Guardian
mkdir -p "$HOME/.openclaw"
cp -R "$TMP_RESTORE_DIR/guardian" "$HOME/.openclaw/"

# 2. Restore MemPalace Config
mkdir -p "$HOME/.mempalace"
cp "$TMP_RESTORE_DIR/mempalace.yaml" "$HOME/.mempalace/"

# 3. Restore Task Registry
mkdir -p "$HOME/.openclaw/runtime"
cp "$TMP_RESTORE_DIR/active_tasks.json" "$HOME/.openclaw/runtime/"

# 4. Restore LaunchAgents
mkdir -p "$LAUNCH_AGENTS_DIR"
cp "$TMP_RESTORE_DIR/launchagents/"*.plist "$LAUNCH_AGENTS_DIR/"

# 5. Restore Desktop Guides
mkdir -p "$HOME/Desktop"
cp "$TMP_RESTORE_DIR/guides/"* "$HOME/Desktop/"

rm -rf "$TMP_RESTORE_DIR"
echo "[OK] System snapshot restored."

# Step 2: Load Services
echo "[2/2] Loading system services..."
for plist in "$LAUNCH_AGENTS_DIR"/ai.openclaw.*.plist; do
    launchctl load "$plist" 2>/dev/null || launchctl unload "$plist" && launchctl load "$plist"
done

echo "✅ SYSTEM FULLY RESTORED!"
echo "Please restart your browser and visit http://127.0.0.1:18792"
