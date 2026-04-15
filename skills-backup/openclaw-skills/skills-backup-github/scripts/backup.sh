#!/bin/bash
#===========================================================
# skills-backup-github: Backup all OpenClaw skills to GitHub
#===========================================================
set -e

WORKSPACE="/Users/KS/.openclaw/workspace"
BACKUP_DIR="$WORKSPACE/skills-backup"
GITHUB_REPO="scchin/openclaw-workspace"
AGENTS_SKILLS="/Users/KS/.agents/skills"
OPENCLAW_SKILLS="/Users/KS/.openclaw/skills"

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

# Step 3: Sync skills (rsync, exclude .venv/node_modules)
echo "[3/5] Syncing skills to backup dir..."
mkdir -p "$BACKUP_DIR/agents-skills" "$BACKUP_DIR/openclaw-skills"

rsync -a \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    "$AGENTS_SKILLS/" "$BACKUP_DIR/agents-skills/"

rsync -a \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    "$OPENCLAW_SKILLS/" "$BACKUP_DIR/openclaw-skills/"

echo "[OK] Sync done"

# Step 4: Git add + diff check
echo "[4/5] Checking for changes..."
cd "$WORKSPACE"
git add skills-backup/

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
echo "[5/5] Pushing to GitHub..."
git push origin main

# Step 6: Force UI Sync (Condition-Based Refresh)
echo "[6/6] Waiting for Gateway skills to be ready..."

# Loop until skills.status returns a non-empty list or timeout (max 15s)
COUNT=0
while [ $COUNT -lt 15 ]; do
    # Check if skills.status returns something other than an empty list []
    if curl -s http://127.0.0.1:18792/skills/status | grep -q "\["; then
        # Note: We check if the response is more than just "[]"
        RESP=$(curl -s http://127.0.0.1:18792/skills/status)
        if [[ "$RESP" != "[]" && "$RESP" != "" ]]; then
            echo "[OK] Skills are ready! Triggering UI refresh..."
            curl -s http://127.0.0.1:18793/trigger-refresh > /dev/null
            echo "[OK] UI refresh command sent successfully!"
            break
        fi
    fi
    echo "Waiting for skills indexing... ($((COUNT+1))/15)"
    sleep 1
    COUNT=$((COUNT+1))
done

if [ $COUNT -eq 15 ]; then
    echo "[!] Timeout: Skills not ready in 15s. Please manually refresh (Cmd+Shift+R)."
fi

echo "[OK] Backup and UI sync process complete!"


