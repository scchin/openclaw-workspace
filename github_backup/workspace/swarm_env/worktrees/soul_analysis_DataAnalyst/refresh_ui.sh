#!/bin/zsh
# =============================================================================
# OpenClaw UI Force Refresh Utility
# =============================================================================
# This script triggers the sync_sidecar to push a FORCE_RELOAD command to 
# all connected UI clients via WebSocket.
# =============================================================================

ENDPOINT="http://127.0.0.1:18793/trigger-refresh"

echo "🚀 Triggering UI Force Refresh..."
if curl -s "$ENDPOINT" > /dev/null; then
    echo "✅ UI Refresh signal sent successfully."
else
    echo "❌ Failed to send refresh signal. Is sync_sidecar (18793) running?"
    exit 1
fi
