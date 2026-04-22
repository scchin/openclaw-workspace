#!/bin/bash
# [SENSITIVE_TOKEN_HARD_REDACTED]--------------
# OpenClaw Fortress Logic (v1.0.0) - Trinity Skill Edition
# [SENSITIVE_TOKEN_HARD_REDACTED]--------------

# 獲取技能路徑
LOGIC_DIR=$(dirname "$(realpath "$0")")
SKILL_DIR=$(dirname "$LOGIC_DIR")
EXTENSIONS_DIR="$SKILL_DIR/extensions"
BASE_DIR="$HOME/.openclaw"
OPENCLAW_JSON="$BASE_DIR/openclaw.json"
PLIST_PATH="$HOME/Library/LaunchAgents/ai.openclaw.gateway.plist"
START_GATEWAY_SCRIPT="$LOGIC_DIR/start_gateway.sh"

# --- Fortress Boot: Environment setup ---
export PATH="/usr/sbin:/sbin:/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# 1. IP 偵測 (優先 ZeroTier)
get_lan_ip() {
    zt_ip=$(ifconfig 2>/dev/null | grep -E "feth|zt" -A 2 | grep "inet " | awk '{print $2}' | head -n 1)
    [ -z "$zt_ip" ] && zt_ip=$(ifconfig 2>/dev/null | grep "inet " | grep "192.168.19" | awk '{print $2}' | head -n 1)
    [ -n "$zt_ip" ] && echo "$zt_ip" || ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1
}

# 2. 更新設定
update_config() {
    local IP=$1
    [ -z "$IP" ] && return
    echo "📡 [IP Sync] Detected LAN IP: $IP"
    chflags nouchg "$OPENCLAW_JSON"
    python3 -c "
import json, os
path = '$OPENCLAW_JSON'
with open(path, 'r') as f: data = json.load(f)
origins = data.get('gateway', {}).get('controlUi', {}).get('allowedOrigins', [])
new_origin = 'http://$IP:18792'
if new_origin not in origins:
    origins.append(new_origin)
    print(f'✅ [Fortress] Added {new_origin} to allowedOrigins')
with open(path, 'w') as f: json.dump(data, f, indent=2)
"
    chflags uchg "$OPENCLAW_JSON"
}

# 3. 執行擴充插件
apply_extensions() {
    if [ -d "$EXTENSIONS_DIR" ]; then
        for ext in "$EXTENSIONS_DIR"/*.sh; do
            if [ -x "$ext" ]; then
                echo "🧩 [Extension] Executing $(basename "$ext")..."
                bash "$ext"
            fi
        done
    fi
}

# 4. 系統初始化 (--install)
install_system() {
    echo "🏗️ [Fortress] Engaging System Armor..."
    command -v mkcert &> /dev/null && (echo "🔐 Fixing SSL Trust..."; mkcert -install)
    chflags nouchg "$PLIST_PATH"
    python3 -c "
import os, re
path = '$PLIST_PATH'
if not os.path.exists(path): exit(0)
with open(path, 'r') as f: content = f.read()
new_content = re.sub(
    r'<key>ProgramArguments</key>\s*<array>.*?</array>',
    f'<key>ProgramArguments</key><array><string>/bin/bash</string><string>$START_GATEWAY_SCRIPT</string></array>',
    content, flags=re.DOTALL
)
with open(path, 'w') as f: f.write(new_content)
"
    chflags uchg "$PLIST_PATH"
    launchctl unload -w "$PLIST_PATH" 2>/dev/null; launchctl load -w "$PLIST_PATH"
    echo "✅ [Fortress] System Armor successfully installed."
}

# 執行主邏輯
IP=$(get_lan_ip)
if [ "$1" == "--install" ]; then
    update_config "$IP"
    install_system
else
    update_config "$IP"
fi

# 在所有模式下皆調用擴充邏輯
apply_extensions
