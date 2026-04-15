#!/bin/bash
#===========================================================
# skills-restore-github: Restore all OpenClaw skills from GitHub
# Run this on a NEW device to restore all skills from backup.
#===========================================================
set -e

WORKSPACE="${WORKSPACE:-/Users/KS/.openclaw/workspace}"
GITHUB_REPO="scchin/openclaw-workspace"
AGENTS_SKILLS="$HOME/.agents/skills"
OPENCLAW_SKILLS="$HOME/.openclaw/skills"

echo "=== Skills Restore from GitHub ==="

# Step 1: Check gh auth
echo "[1/4] Checking GitHub authentication..."
if ! gh auth status &>/dev/null; then
    echo "[!] Not logged in. Starting GitHub login..."
    gh auth login --hostname github.com
fi
echo "[OK] GitHub authenticated"

# Step 2: Clone or update repo
echo "[2/4] Fetching repo..."
cd "$WORKSPACE"
if [ -d ".git" ]; then
    echo "[*] Repo exists, pulling latest..."
    git pull origin main
else
    echo "[*] Cloning repo fresh..."
    git clone "https://github.com/$GITHUB_REPO.git" "$WORKSPACE"
    cd "$WORKSPACE"
fi
echo "[OK] Repo ready"

# Step 3: Restore agents-skills
echo "[3/4] Restoring agents skills..."
if [ -d "skills-backup/all-skills/agents-skills" ]; then
    rsync -a --delete \
        skills-backup/all-skills/agents-skills/ "$AGENTS_SKILLS/"
    echo "[OK] agents-skills restored ($(ls $AGENTS_SKILLS | wc -l | tr -d ' ') skills)"
else
    echo "[!] agents-skills backup not found in repo"
fi

# Step 4: Restore openclaw-skills
echo "[4/4] Restoring openclaw skills..."
if [ -d "skills-backup/all-skills/openclaw-skills" ]; then
    rsync -a --delete \
        skills-backup/all-skills/openclaw-skills/ "$OPENCLAW_SKILLS/"
    echo "[OK] openclaw-skills restored ($(ls $OPENCLAW_SKILLS | wc -l | tr -d ' ') skills)"
else
    echo "[!] openclaw-skills backup not found in repo"
fi

echo ""
echo "=== Restore complete! ==="
echo "Restart OpenClaw to load new skills."
