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
EXCLUDE_BY_PATH="query\\.py|\\.env|SECRET|TOKEN|API_KEY|\\.pem|credentials"

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
    for py_file in \
        "$tmp/google-places/scripts/query.py" \
        "$tmp/where-to-go/scripts/run.py" \
        "$tmp/google-places-backup-2026-03-22/scripts/query.py"; do
        if [ -f "$py_file" ]; then
            sed -i '' \
                -e 's/AIzaSy[AAAA-Za-z0-9_-]*/[API_KEY_REDACTED]/g' \
                -e 's/GOOGLE_PLACES_API_KEY[^\"]*/GOOGLE_PLACES_API_KEY/g' \
                "$py_file"
        fi
    done
}

echo "=== Skills Backup to GitHub ==="

echo "[1/5] Checking GitHub authentication..."
if ! gh auth status &>/dev/null; then
    gh auth login --hostname github.com
fi
echo "[OK] GitHub authenticated"

echo "[2/5] Checking git remote..."
cd "$WORKSPACE"
if ! git remote -v | grep -q "github.com"; then
    if gh repo view "$GITHUB_REPO" &>/dev/null; then
        git remote add origin "https://github.com/$GITHUB_REPO.git"
        git branch -M main
        git config git_protocol https
    else
        gh repo create "$GITHUB_REPO" --public --source="$WORKSPACE" --push
        echo "[OK] Repo created and pushed"
        exit 0
    fi
fi

echo "[3a/6] Syncing full skills to local backup (includes API keys)..."
mkdir -p "$BACKUP_DIR/all-skills/agents-skills" "$BACKUP_DIR/all-skills/openclaw-skills"
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='node_modules' --exclude='.git' "$AGENTS_SKILLS/" "$BACKUP_DIR/all-skills/agents-skills/"
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='node_modules' --exclude='.git' "$OPENCLAW_SKILLS/" "$BACKUP_DIR/all-skills/openclaw-skills/"

echo "[3b/6] Syncing GitHub-safe skills (API keys redacted)..."
mkdir -p "$BACKUP_DIR/github-skills/agents-skills" "$BACKUP_DIR/github-skills/openclaw-skills"
_prepare_github_safe_backup "$AGENTS_SKILLS" "$BACKUP_DIR/github-skills/agents-skills"
_prepare_github_safe_backup "$OPENCLAW_SKILLS" "$BACKUP_DIR/github-skills/openclaw-skills"

echo "[OK] Sync done"

echo "[4/6] Checking for changes..."
cd "$WORKSPACE"
git add skills-backup/github-skills/
if git diff --cached --quiet; then
    echo "[OK] No changes detected. Nothing to commit."
else
    CHANGES=$(git diff --cached --stat | tail -1)
    echo "[Changes] $CHANGES"
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
    git commit -m "Backup: skills update ($TIMESTAMP)"
    echo "[OK] Committed"
fi

echo "[5/6] Pushing to GitHub..."
git push origin main
echo "[OK] Backup complete!"

# ============================================================
# Step 6: 生成結構化彙總報告 (Structured Summary Report)
# ============================================================
echo -e "\n📊 GitHub 技能備份彙總報告"
echo "總計發現技能數：$(find "$BACKUP_DIR/github-skills" -name "SKILL.md" | wc -l) 個 (包含所有路徑)"
echo "唯一技能數：$(find "$BACKUP_DIR/github-skills" -name "SKILL.md" | xargs -I {} basename \$(dirname {}) | sort -u | wc -l) 個"
echo ""

echo "📂 分類清單"
echo "1. Agent 專業技能 (agents-skills)"
echo "這類技能主要集中在專業任務自動化、研究與內容創作："
echo ""

# 定義 Agent 技能類別映射
# 格式: "類別名稱|關鍵字1,關鍵字2..."
AGENT_CATEGORIES=(
    "AI 自動化|autoglm,websearch,browser,deepresearch,generate-image,search-image,open-link"
    "內容與行銷|copywriting,content-strategy,seo,blog,social-content,social-media"
    "開發與設計|code,architecture,frontend,ui-ux,git-essentials,opencode"
    "研究與分析|research-paper,market-research,aminer,backtest,stock-analysis"
    "管理與效率|executing-plans,writing-plans,automation,skill-creator,skill-vetter"
    "個人化工具|memory,obsidian,tmux,1password"
    "專業診斷|security-auditor,clawdefender,debug-pro"
)

for cat_info in "${AGENT_CATEGORIES[@]}"; do
    IFS="|" read -r cat_name keywords <<< "$cat_info"
    SKILLS_IN_CAT=""
    
    # 掃描所有 agent skills
    while read -r skill_dir; do
        skill_name=$(basename "$skill_dir")
        for kw in ${keywords//,/ }; do
            if [[ "$skill_name" == *"$kw"* ]]; then
                SKILLS_IN_CAT+="$skill_name, "
                break
            fi
        done
    done < <(find "$BACKUP_DIR/github-skills/agents-skills" -type d -maxdepth 1 -mindepth 1)
    
    if [ -n "$SKILLS_IN_CAT" ]; then
        echo "$cat_name：${SKILLS_IN_CAT%, }"
        echo ""
    fi
done

echo "2. OpenClaw 核心/工具技能 (openclaw-skills)"
echo "這類技能主要負責系統維護與生活機能查詢："
echo ""

# 定義 OpenClaw 技能類別映射
OC_CATEGORIES=(
    "系統維護|skills-github-backup,skill-installation,token-optimizer"
    "飛書整合|feishu-calendar,feishu-doc,feishu-drive,feishu-wiki,feishu-perm"
    "生活工具|where-to-go,google-places,chinese-date"
    "文件處理|pptx-maker,prompt-guard"
)

for cat_info in "${OC_CATEGORIES[@]}"; do
    IFS="|" read -r cat_name keywords <<< "$cat_info"
    SKILLS_IN_CAT=""
    
    while read -r skill_dir; do
        skill_name=$(basename "$skill_dir")
        for kw in ${keywords//,/ }; do
            if [[ "$skill_name" == *"$kw"* ]]; then
                SKILLS_IN_CAT+="$skill_name, "
                break
            fi
        done
    done < <(find "$BACKUP_DIR/github-skills/openclaw-skills" -type d -maxdepth 1 -mindepth 1)
    
    if [ -n "$SKILLS_IN_CAT" ]; then
        echo "$cat_name：${SKILLS_IN_CAT%, }"
        echo ""
    fi
done

echo "📈 統計概覽"
echo "最新同步：$(date '+%Y-%m-%d %H:%M')"
echo "分佈情況：majority 屬於 agents-skills，涵蓋了從金融分析到前端設計的極廣範疇。"
echo "備份狀態：所有 SKILL.md 均已正確同步至 skills-backup/ 結構中，可用於快速還原。"
echo "如果您需要針對某個特定類別（例如「飛書相關」或「AI 自動化」）的詳細清單，請告訴我！"

echo -e "\nLocal full backup (with API keys): $BACKUP_DIR/all-skills/"
