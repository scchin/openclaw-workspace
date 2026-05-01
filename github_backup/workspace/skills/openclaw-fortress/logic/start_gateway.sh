#!/bin/bash
# OpenClaw Fortress 啟動引導器 (Skill Edition)

LOGIC_DIR=$(dirname "$(realpath "$0")")
FORTIFY_CMD="bash $LOGIC_DIR/fortify.sh"
PATCH_PATH="$LOGIC_DIR/epperm-patch.mjs"

echo "🛡️ [Fortress Boot] Checking system integrity..."
$FORTIFY_CMD --check

# 在啟動 Gateway 之前，先確保金鑰守護進程已在背景運行
echo "📡 [Fortress Boot] Starting Key Guardian..."
python3 "$LOGIC_DIR/guardian_logic.py" &

echo "🚀 [Fortress Boot] Launching OpenClaw Gateway with EPERM shield..."
exec /opt/homebrew/opt/node/bin/node \
    --import "$PATCH_PATH" \
    /opt/homebrew/lib/node_modules/openclaw/dist/index.js gateway
