#!/bin/bash
# ==============================================================================
# 🧩 OpenClaw Extension: Immortal Auto-Loader
# 描述: 每次啟動網關時，自動掃描備份目錄並掛載所有定時任務，具備路徑自癒功能。
# ==============================================================================
SOURCE_DIR="$HOME/.openclaw/workspace/github_backup/system/launchagents"
TARGET_DIR="$HOME/Library/LaunchAgents"
CURRENT_USER=$(whoami)

echo "🔋 [Immortal Guard] 正在執行排程自檢..."

if [ -d "$SOURCE_DIR" ]; then
    for plist in "$SOURCE_DIR"/*.plist; do
        filename=$(basename "$plist")
        target_plist="$TARGET_DIR/$filename"
        
        # 1. 物理同步與路徑自癒
        if [ ! -f "$target_plist" ]; then
            echo "🚚 [Sync] 安裝新排程: $filename"
            cp "$plist" "$target_plist"
            sed -i '' "s/\/Users\/[a-zA-Z0-9_-]*/\/Users\/$CURRENT_USER/g" "$target_plist"
        fi
        
        # 2. 啟動狀態維持
        label=$(basename "$filename" .plist)
        if ! launchctl list | grep -q "$label"; then
            echo "⚡ [Activation] 重新加載任務: $label"
            launchctl load "$target_plist" 2>/dev/null
        fi
    done
fi
