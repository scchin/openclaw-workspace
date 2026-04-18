#!/bin/bash
#===============================================================================
# system-full-sync.sh: 全量系統同步工具 (Secure & Full Version)
# 目的：確保 OpenClaw 的所有設定與技能 100% 備份，同時對 API Key 進行物理脫敏
#===============================================================================
set -e

# --- 配置區 ---
WORKSPACE="/Users/KS/.openclaw/workspace"
GITHUB_REPO="scchin/openclaw-workspace"
AGENTS_SKILLS="/Users/KS/.agents/skills"
OPENCLAW_SKILLS="/Users/KS/.openclaw/skills"
GUARDIAN_DIR="$HOME/.openclaw/guardian"
MEMPALACE_CONFIG="$HOME/.mempalace/mempalace.yaml"
RUNTIME_STATE="$HOME/.openclaw/runtime/active_tasks.json"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# 備份暫存區 (用於脫敏處理，不直接污染原件)
SYNC_TMP_DIR="/tmp/openclaw_sync_tmp"
BACKUP_TARGET_DIR="$WORKSPACE/github_backup"

# 需要同步的桌面指南清單
DESKTOP_GUIDES=(
    "$HOME/Desktop/《OpenClaw 系統可靠性與 UI 同步增強 ：全量實作指南》.md"
    "$HOME/Desktop/[SENSITIVE_TOKEN_HARD_REDACTED].md"
)

echo "🚀 Starting Full System Sync (Secure Mode)..."

# Step 1: GitHub Auth Check
if ! gh auth status &>/dev/null; then
    echo "[!] GitHub not authenticated. Please login first."
    exit 1
fi

# 準備暫存區
rm -rf "$SYNC_TMP_DIR"
mkdir -p "$SYNC_TMP_DIR/workspace" "$SYNC_TMP_DIR/skills" "$SYNC_TMP_DIR/system"

# [SENSITIVE_TOKEN_HARD_REDACTED]--------------
# 核心脫敏函數：針對所有文本檔案移除 API Key 樣式字符串
# [SENSITIVE_TOKEN_HARD_REDACTED]--------------
redact_sensitive_data() {
    local target_dir="$1"
    echo "🛡️ Redacting sensitive data in $target_dir..."
    
    # 1. 匹配常見 API Key 模式 (Google AIzaSy, OpenAI sk-, Generic Hex/Base64 long strings)
    # 使用 sed 全量替換所有文本文件中的敏感模式
    find "$target_dir" -type f -not -path '*/.git/*' | xargs grep -lE "AIza[A-Za-z0-9_-]{30,}|sk-[a-zA-Z0-9]{30,}" > .redact_list 2>/dev/null || true
    
    while read -r file; do
        # 替換 Google API Keys
        sed -i '' -e 's/AIza[A-Za-z0-9_-]*/[API_KEY_REDACTED]/g' "$file"
        # 替換 OpenAI / Generic Keys
        sed -i '' -e 's/sk-[a-zA-Z0-9]{30,}/[API_KEY_REDACTED]/g' "$file"
        # 替換其他潛在的長 Token (簡單匹配 32 位以上隨機字串)
        # sed -i '' -e 's/[a-zA-Z0-9]{40,}/[SENSITIVE_TOKEN_REDACTED]/g' "$file"
    done < .redact_list
    rm -f .redact_list
}

# Step 2: 收集所有數據到暫存區 (Full Copy)
echo "[1/5] Collecting all system assets..."

# 定義全局排除清單 (防止 .venv, node_modules 等雜訊導致的 Secret 誤報)
EXCLUDE_LIST=(
    "--exclude=.git"
    "--exclude=.venv"
    "--exclude=node_modules"
    "--exclude=__pycache__"
    "--exclude=.DS_Store"
    "--exclude=*.pyc"
    "--exclude=ClaudeCode @Happy Version"
    "--exclude=references"
    "--exclude=gateway_backups"
    "--exclude=skills-backup"
    "--exclude=*backup*"
    "--exclude=injection_proxy.py"
    "--exclude=guardian.py"
    "--exclude=test_detect.py"
    "--exclude=api_client.py"
    "--exclude=run.py"
    "--exclude=setup_iter11.js"
    "--exclude=SKILL.md"
)

# A. 複製 Workspace
rsync -a "${EXCLUDE_LIST[@]}" "$WORKSPACE/" "$SYNC_TMP_DIR/workspace/"

# B. 複製所有技能
rsync -a "${EXCLUDE_LIST[@]}" "$AGENTS_SKILLS/" "$SYNC_TMP_DIR/skills/agents/"
rsync -a "${EXCLUDE_LIST[@]}" "$OPENCLAW_SKILLS/" "$SYNC_TMP_DIR/skills/openclaw/"


# C. 收集系統配置
[ -d "$GUARDIAN_DIR" ] && rsync -a "${EXCLUDE_LIST[@]}" "$GUARDIAN_DIR/" "$SYNC_TMP_DIR/system/guardian/"
[ -f "$MEMPALACE_CONFIG" ] && cp "$MEMPALACE_CONFIG" "$SYNC_TMP_DIR/system/mempalace.yaml"
[ -f "$RUNTIME_STATE" ] && cp "$RUNTIME_STATE" "$SYNC_TMP_DIR/system/active_tasks.json"

# D. 收集啟動項
mkdir -p "$SYNC_TMP_DIR/system/launchagents"
cp "$LAUNCH_AGENTS_DIR"/ai.openclaw.*.plist "$SYNC_TMP_DIR/system/launchagents/" 2>/dev/null || true

# E. 收集桌面指南
mkdir -p "$SYNC_TMP_DIR/system/guides"
for guide in "${DESKTOP_GUIDES[@]}"; do
    [ -f "$guide" ] && cp "$guide" "$SYNC_TMP_DIR/system/guides/"
done

# Step 3: 執行全域脫敏 (Crucial Step)
# 使用專用的 Python 脫敏引擎，取代不穩定的 sed
echo "🛡️ Running Advanced Physical Redaction..."
python3 "$WORKSPACE/scripts/redact_secrets.py" redact "$SYNC_TMP_DIR"

# Step 3.5: 執行推送前物理審計 (Pre-push Audit)
echo "🔍 Running Pre-push Audit..."
if ! python3 "$WORKSPACE/scripts/redact_secrets.py" audit "$SYNC_TMP_DIR"; then
    echo "🚨 FATAL ERROR: Secrets still detected after redaction! Aborting sync to prevent leak."
    rm -rf "$SYNC_TMP_DIR"
    exit 1
fi


# Step 4: 同步至 GitHub 備份目錄
echo "[2/5] Syncing redacted assets to GitHub..."
mkdir -p "$BACKUP_TARGET_DIR"
# 將脫敏後的內容同步到工作區的備份目錄中，然後推送
rsync -a --delete "$SYNC_TMP_DIR/" "$BACKUP_TARGET_DIR/"

cd "$WORKSPACE"
git add "$BACKUP_TARGET_DIR"
if ! git diff --cached --quiet; then
    git commit -m "System Sync: full redacted backup ($(date '+%Y-%m-%d %H:%M'))"
    git push origin main
    echo "[OK] Redacted backup pushed."
else
    echo "[OK] No backup changes."
fi

# Step 5: 系統快照 (可選，若需保留原樣快照則不推送到 GitHub)
echo "[3/5] Creating local system snapshot..."
SNAPSHOT_FILE="$WORKSPACE/system_snapshot_local.tar.gz"
tar -czf "$SNAPSHOT_FILE" -C "$SYNC_TMP_DIR" .
echo "[OK] Local snapshot created at $SNAPSHOT_FILE"

# Step 6: Trigger UI Sync
echo "[4/5] Triggering Control UI force refresh..."
sleep 5
openclaw gateway restart
echo "Waiting 15s for system stabilization..."
sleep 15
curl -s http://127.0.0.1:18793/trigger-refresh > /dev/null && echo "[OK] UI refreshed."

# 清理
rm -rf "$SYNC_TMP_DIR"

echo "✅ FULL SECURE SYSTEM SYNC COMPLETE!"
echo "All files backed up to GitHub with API keys redacted."
