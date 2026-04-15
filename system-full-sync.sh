#!/bin/bash
#===============================================================================
# system-full-sync.sh: 全量系統同步工具 (The All-in-One Sync)
# 目的：確保 OpenClaw 的所有自定義設定、指南、技能與狀態可 100% 遷移
#===============================================================================
set -e

# --- 配置區 ---
WORKSPACE="/Users/KS/.openclaw/workspace"
BACKUP_DIR="$WORKSPACE/skills-backup"
GITHUB_REPO="scchin/openclaw-workspace"
AGENTS_SKILLS="/Users/KS/.agents/skills"
OPENCLAW_SKILLS="/Users/KS/.openclaw/skills"
GUARDIAN_DIR="$HOME/.openclaw/guardian"
MEMPALACE_CONFIG="$HOME/.mempalace/mempalace.yaml"
RUNTIME_STATE="$HOME/.openclaw/runtime/active_tasks.json"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# 需要同步的桌面指南清單
DESKTOP_GUIDES=(
    "$HOME/Desktop/《OpenClaw 系統可靠性與 UI 同步增強 ：全量實作指南》.md"
    "$HOME/Desktop/google-reliability-guardian_Guide.md"
)

echo "🚀 Starting Full System Sync..."

# Step 1: GitHub Auth Check
if ! gh auth status &>/dev/null; then
    echo "[!] GitHub not authenticated. Please login first."
    exit 1
fi

# Step 2: Git Workspace Sync (靈魂層)
echo "[1/5] Syncing Workspace (Soul & Memory)..."
cd "$WORKSPACE"
git add .
if ! git diff --cached --quiet; then
    git commit -m "System Sync: workspace update ($(date '+%Y-%m-%d %H:%M'))"
    git push origin main
    echo "[OK] Workspace pushed."
else
    echo "[OK] No workspace changes."
fi

# Step 3: Skills Backup (能力層 - 脫敏處理)
echo "[2/5] Syncing Skills (Capabilities)..."
mkdir -p "$BACKUP_DIR/github-skills/agents-skills" "$BACKUP_DIR/github-skills/openclaw-skills"

# 脫敏函數 (移除 API Key)
redact_keys() {
    sed -i '' -e 's/AIzaSy[AAAA-Za-z0-9_-]*/[API_KEY_REDACTED]/g' "$1"
}

# 同步並脫敏
rsync -a --exclude='.git' "$AGENTS_SKILLS/" "$BACKUP_DIR/github-skills/agents-skills/"
rsync -a --exclude='.git' "$OPENCLAW_SKILLS/" "$BACKUP_DIR/github-skills/openclaw-skills/"

# 遞迴脫敏所有 .py 檔案
find "$BACKUP_DIR/github-skills" -name "*.py" -exec sh -c 'sed -i "" "s/AIzaSy[AAAA-Za-z0-9_-]*/[API_KEY_REDACTED]/g" "$1"' _ {} \;

git add "$BACKUP_DIR/github-skills/"
if ! git diff --cached --quiet; then
    git commit -m "System Sync: skills update ($(date '+%Y-%m-%d %H:%M'))"
    git push origin main
    echo "[OK] Skills pushed."
else
    echo "[OK] No skills changes."
fi

# Step 4: System Snapshot (基礎設施層)
echo "[3/5] Creating System Snapshot (Infrastructure)..."
SNAPSHOT_FILE="$WORKSPACE/system_snapshot.tar.gz"
TMP_SNAPSHOT_DIR="/tmp/openclaw_snapshot"
mkdir -p "$TMP_SNAPSHOT_DIR"

# 收集所有關鍵配置
# 1. 守護進程
[ -d "$GUARDIAN_DIR" ] && cp -R "$GUARDIAN_DIR" "$TMP_SNAPSHOT_DIR/guardian"
# 2. 記憶宮殿配置
[ -f "$MEMPALACE_CONFIG" ] && cp "$MEMPALACE_CONFIG" "$TMP_SNAPSHOT_DIR/mempalace.yaml"
# 3. 任務註冊表
[ -f "$RUNTIME_STATE" ] && cp "$RUNTIME_STATE" "$TMP_SNAPSHOT_DIR/active_tasks.json"
# 4. 啟動項 (僅限 ai.openclaw.*)
mkdir -p "$TMP_SNAPSHOT_DIR/launchagents"
cp "$LAUNCH_AGENTS_DIR"/ai.openclaw.*.plist "$TMP_SNAPSHOT_DIR/launchagents/" 2>/dev/null || true
# 5. 桌面指南
mkdir -p "$TMP_SNAPSHOT_DIR/guides"
for guide in "${DESKTOP_GUIDES[@]}"; do
    [ -f "$guide" ] && cp "$guide" "$TMP_SNAPSHOT_DIR/guides/"
done

# 打包
tar -czf "$SNAPSHOT_FILE" -C "$TMP_SNAPSHOT_DIR" .
rm -rf "$TMP_SNAPSHOT_DIR"

# 將快照同步至 GitHub (建議放在 workspace 根目錄或特定隱藏路徑)
git add "$SNAPSHOT_FILE"
git commit -m "System Sync: snapshot update ($(date '+%Y-%m-%d %H:%M'))"
git push origin main
echo "[OK] System snapshot pushed."

# Step 5: Trigger UI Sync
echo "[4/5] Triggering Control UI force refresh..."
openclaw gateway restart
sleep 2
curl -s http://127.0.0.1:18793/trigger-refresh > /dev/null && echo "[OK] UI refreshed."

echo "✅ FULL SYSTEM SYNC COMPLETE!"
echo "Your entire environment is now backed up to GitHub."
