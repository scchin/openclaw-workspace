#!/bin/bash
# ==============================================================================
# 🔄 OpenClaw 不朽恢復工具 (v2.0 - Path Auto-Repair Edition)
# ==============================================================================
set -e
OLD_USER="KS"
NEW_USER=$(whoami)
WORKSPACE="$HOME/.openclaw/workspace"
SNAPSHOT_FILE="$WORKSPACE/system_snapshot.tar.gz"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🔄 [1/3] 正在恢復系統快照..."
TMP_RESTORE_DIR="/tmp/openclaw_restore"
mkdir -p "$TMP_RESTORE_DIR"
tar -xzf "$SNAPSHOT_FILE" -C "$TMP_RESTORE_DIR"

# 恢復目錄與設定
mkdir -p "$HOME/.openclaw" "$HOME/.mempalace" "$HOME/.openclaw/runtime"
cp -R "$TMP_RESTORE_DIR/guardian" "$HOME/.openclaw/"
cp "$TMP_RESTORE_DIR/mempalace.yaml" "$HOME/.mempalace/"
cp "$TMP_RESTORE_DIR/active_tasks.json" "$HOME/.openclaw/runtime/"
cp "$TMP_RESTORE_DIR/launchagents/"*.plist "$LAUNCH_AGENTS_DIR/"

echo "🛠️ [2/3] 正在執行路徑自癒程序 ($OLD_USER -> $NEW_USER)..."
for plist in "$LAUNCH_AGENTS_DIR"/*openclaw*.plist; do
    [ -f "$plist" ] && sed -i '' "s/\/Users\/$OLD_USER/\/Users\/$NEW_USER/g" "$plist"
done

# 4. 執行擴充插件
apply_extensions() {
    # [不朽防護] 優先執行工作區的自定義擴充 (避風港)
    SAFE_EXT_DIR="$HOME/.openclaw/workspace/custom_extensions"
    if [ -d "$SAFE_EXT_DIR" ]; then
        for ext in "$SAFE_EXT_DIR"/*.sh; do
            [ -x "$ext" ] && bash "$ext"
        done
    fi

    # 執行技能內部的官方擴充
    if [ -d "$EXTENSIONS_DIR" ]; then
        for ext in "$EXTENSIONS_DIR"/*.sh; do
            if [ -x "$ext" ]; then
                echo "🧩 [Extension] Executing $(basename "$ext")..."
                bash "$ext"
            fi
        done
    fi
}

echo "⚡ [3/3] 正在掛載服務並啟動守護..."
for plist in "$LAUNCH_AGENTS_DIR"/ai.openclaw.*.plist; do
    launchctl unload "$plist" 2>/dev/null || true
    launchctl load "$plist"
done

# 注入防遺忘終端機提醒
ZSHRC="$HOME/.zshrc"
GUARD_CMD='[[ -z $(launchctl list | grep openclaw.gateway) ]] && echo -e "\n\033[1;31m🚨 [OpenClaw] 偵測到網關未啟動！請執行：bash '"$WORKSPACE"'/restore.sh\033[0m\n"'
grep -q "OpenClaw" "$ZSHRC" || echo "$GUARD_CMD" >> "$ZSHRC"

rm -rf "$TMP_RESTORE_DIR"
echo "✅ 系統恢復完成，路徑已校準，終端機監控已啟動。"
