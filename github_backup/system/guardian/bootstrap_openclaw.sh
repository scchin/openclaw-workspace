#!/bin/bash
# =============================================================================
# OpenClaw 終極轉移與防護部署腳本 (Bootstrap Protection)
# =============================================================================

PLIST_PATH="$HOME/Library/LaunchAgents/ai.openclaw.gateway.plist"
PATCH_PATH="$HOME/.openclaw/guardian/epperm-patch.mjs"

if [ ! -f "$PATCH_PATH" ] || [ ! -f "$PLIST_PATH" ]; then
    exit 0
fi

# 解除 LaunchAgent 的防護以便注入
chflags nouchg "$PLIST_PATH" 2>/dev/null

if ! grep -q "NODE_OPTIONS" "$PLIST_PATH"; then
    python3 -c '
import sys, re
path = sys.argv[1]
with open(path, "r") as f: content = f.read()
if "<key>EnvironmentVariables</key>" in content:
    replacement = "<key>EnvironmentVariables</key>\n    <dict>\n    <key>NODE_OPTIONS</key>\n    <string>--import /Users/KS/.openclaw/guardian/epperm-patch.mjs</string>"
    content = re.sub(r"<key>EnvironmentVariables</key>\s*<dict>", replacement, content)
    with open(path, "w") as f: f.write(content)
' "$PLIST_PATH"
    
    # 只要有發生修改，才熱重載服務 (避免無窮迴圈)
    launchctl unload -w "$PLIST_PATH" 2>/dev/null
    launchctl load -w "$PLIST_PATH"
fi

# 唯獨對 Plist 進行物理鎖定，從此放開環境變數與金鑰檔的鎖定供手動修改
chflags uchg "$PLIST_PATH"
