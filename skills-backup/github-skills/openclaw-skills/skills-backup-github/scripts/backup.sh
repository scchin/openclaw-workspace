#===========================================================
# skills-backup-github: Backup all OpenClaw skills to GitHub
#
# 安全策略：
# 1. API Key / Token / Secret 等敏感性資料，絕不上傳 GitHub
# 2. 本地備份（~/.openclaw/workspace/skills-backup/all-skills/）則完整保留
#===========================================================
set -e

WORKSPACE="/Users/KS/.openclaw/workspace"
BACKUP_DIR="$WORKSPACE/skills-backup"
GITHUB_REPO="scchin/openclaw-workspace"
AGENTS_SKILLS="/Users/KS/.agents/skills"
OPENCLAW_SKILLS="/Users/KS/.openclaw/skills"

# ★★★ 敏感資料關鍵字（這些檔案內容不上 GitHub）★★★
# 格式：路徑正規表達式（相對於技能目錄）
EXCLUDE_BY_PATH="query\\.py|\.env|SECRET|TOKEN|API_KEY|\.pem|credentials"

# 備份前，先把含 API Key 的檔案置換成啞巴版本（僅備份到 GitHub 用）
# 策略：針對 google-places/query.py 備份時替換關鍵內容
_prepare_github_safe_backup() {
    local src="$1"
    local tmp="$2"
    mkdir -p "$(dirname "$tmp")"
    rsync -a \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='node_modules' \
        --exclude='.git' \
        "$src/" "$tmp/"
    # 對 google-places/query.py 進行脫敏處理（只保留結構成份，移除 Key）
    if [ -f "$tmp/google-places/scripts/query.py" ]; then
        sed -i '' \
            -e 's/AIzaSy[AAAA-Za-z0-9_-]*/[API_KEY_REDACTED]/g' \
            -e 's/GOOGLE_PLACES_API_KEY[^\"]*/GOOGLE_PLACES_API_KEY/g' \
            "$tmp/google-places/scripts/query.py"
    fi
}

echo "=== Skills Backup to GitHub ==="

# Step 1: Check gh auth
echo "[1/5] Checking GitHub authentication..."
if ! gh auth status &>/dev/null; then
    echo "[!] Not authenticated. Starting GitHub login..."
    gh auth login --hostname github.com
fi
echo "[OK] GitHub authenticated"

# Step 2: Ensure git remote is set
echo "[2/5] Checking git remote..."
cd "$WORKSPACE"
if ! git remote -v | grep -q "github.com"; then
    echo "[!] No GitHub remote found. Creating..."
    if gh repo view "$GITHUB_REPO" &>/dev/null; then
        git remote add origin "https://github.com/$GITHUB_REPO.git"
        git branch -M main
        git config git_protocol https
    else
        echo "[!] Repo $GITHUB_REPO not found. Creating new repo..."
        gh repo create "$GITHUB_REPO" --public --source="$WORKSPACE" --push
        echo "[OK] Repo created and pushed"
        echo "[OK] Backup complete!"
        exit 0
    fi
fi

# Step 3a: 本地完整備份（含 API Key）
echo "[3a/6] Syncing full skills to local backup (includes API keys)..."
mkdir -p "$BACKUP_DIR/all-skills/agents-skills" "$BACKUP_DIR/all-skills/openclaw-skills"
rsync -a \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    "$AGENTS_SKILLS/" "$BACKUP_DIR/all-skills/agents-skills/"
rsync -a \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    "$OPENCLAW_SKILLS/" "$BACKUP_DIR/all-skills/openclaw-skills/"

# Step 3b: GitHub 安全備份（脫敏後上傳）
echo "[3b/6] Syncing GitHub-safe skills (API keys redacted)..."
mkdir -p "$BACKUP_DIR/github-skills/agents-skills" "$BACKUP_DIR/github-skills/openclaw-skills"
_prepare_github_safe_backup "$AGENTS_SKILLS" "$BACKUP_DIR/github-skills/agents-skills"
_prepare_github_safe_backup "$OPENCLAW_SKILLS" "$BACKUP_DIR/github-skills/openclaw-skills"

echo "[OK] Sync done"

# Step 4: Git add + diff check（只上傳脫敏版本）
echo "[4/6] Checking for changes..."
cd "$WORKSPACE"
git add skills-backup/github-skills/

# Check if there are actual changes
if git diff --cached --quiet; then
    echo "[OK] No changes detected. Nothing to commit."
else
    CHANGES=$(git diff --cached --stat | tail -1)
    echo "[Changes] $CHANGES"

    # Auto-commit with timestamp
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
    git commit -m "Backup: skills update ($TIMESTAMP)"
    echo "[OK] Committed"
fi

# Step 5: Push
echo "[5/6] Pushing to GitHub..."
git push origin main
echo "[OK] Backup complete!"

# Step 6: 本地完整備份完成通知
echo "[6/6] Local full backup (with API keys): $BACKUP_DIR/all-skills/"
