---
name: skills-backup-github
description: Backup all installed OpenClaw skills to a GitHub repository, automatically syncing only changed or new files. Use when user asks to backup skills, sync skills to GitHub, or update skill backups. Handles the full flow: gh auth check, rsync with .venv excluded, git diff detection, commit, and push.
---

# Skills Backup GitHub

## Overview

Automatically backup all OpenClaw skills (from `~/.agents/skills/` and `~/.openclaw/skills/`) to the GitHub repo `scchin/openclaw-workspace`. Skips `.venv`, `__pycache__`, and `node_modules` to keep the backup lean.

## Usage

When user says "backup skills", "sync skills to GitHub", "update skill backup", or requests a full/incremental backup of installed skills, run:

```bash
bash /Users/KS/.openclaw/skills/skills-backup-github/scripts/backup.sh
```

## Workflow

The backup script runs these steps automatically:

```
1. Check gh auth → If not logged in, launch "gh auth login" (interactive)
2. Check git remote → If missing, add origin remote
3. rsync skills → Copy to workspace/skills-backup/, excluding .venv/node_modules
4. Git diff check → Only commit if there are actual changes
5. Git push → Push to github.com/scchin/openclaw-workspace
```

## GitHub Authorization Flow

If `gh auth status` fails, the script launches an interactive login:

1. **Protocol**: Choose HTTPS (default) → Enter
2. **Authenticate Git?**: Y → Enter
3. **Auth method**: "Login with a web browser" → Enter
4. **One-time code**: User visits https://github.com/login/device and enters the displayed code (e.g. `E604-15A0`)
5. **Browser auth**: Complete in the browser → Done

After first login, credentials are cached — subsequent backups are fully automatic with no interaction.

## What Gets Backed Up

| Source | Destination in workspace | Notes |
|--------|--------------------------|-------|
| `~/.agents/skills/` | `skills-backup/agents-skills/` | 53 skills |
| `~/.openclaw/skills/` | `skills-backup/openclaw-skills/` | 11 skills |

**Excluded**: `.venv/`, `__pycache__/`, `node_modules/`, `.git/`, `skills-backup*` (prevents self-referential copy)

## GitHub Repo

- **URL**: https://github.com/scchin/openclaw-workspace
- **Backup location in repo**: `skills-backup/agents-skills/` and `skills-backup/openclaw-skills/`
- **Automation**: Fully automatic after first setup — no manual intervention needed on subsequent runs

## Manual Run

```bash
# Full manual run
bash /Users/KS/.openclaw/skills/skills-backup-github/scripts/backup.sh

# Dry-run (check what would change, without committing)
cd /Users/KS/.openclaw/workspace
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='node_modules' ~/.agents/skills/ skills-backup/agents-skills/
rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='node_modules' --exclude='skills-backup*' ~/.openclaw/skills/ skills-backup/openclaw-skills/
git diff skills-backup/ --stat
```
