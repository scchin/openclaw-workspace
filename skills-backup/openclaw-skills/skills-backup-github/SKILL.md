---
name: skills-backup-github
description: Backup and restore all OpenClaw skills to/from GitHub. Use when user asks to backup skills, sync skills to GitHub, or restore skills on a new device. Handles the full flow: gh auth check, rsync with .venv excluded, git diff detection, commit, and push.
---

# Skills Backup GitHub

Backup all OpenClaw skills to GitHub, or restore them on a new device.

## Backup (on any device)

When user says "backup skills", "sync skills to GitHub", or requests a full/incremental skill backup:

```bash
bash /Users/KS/.openclaw/skills/skills-backup-github/scripts/backup.sh
```

**Flow:**
```
1. gh auth check → If not logged in, launch interactive login
2. git remote check → Auto-configure if missing
3. rsync → Copy only changed/new files (excludes .venv/node_modules)
4. git diff → Only commit if there are actual changes
5. git push → Push to github.com/scchin/openclaw-workspace
```

## Restore (on a new device)

When user says "restore skills", "download skills", or "還原技能":

```bash
bash /Users/KS/.openclaw/skills/skills-backup-github/scripts/restore.sh
```

**Flow:**
```
1. gh auth check → If not logged in, launch interactive login
2. Clone or pull the repo (github.com/scchin/openclaw-workspace)
3. rsync --delete → Mirror agents-skills/ into ~/.agents/skills/
4. rsync --delete → Mirror openclaw-skills/ into ~/.openclaw/skills/
5. Done! Restart OpenClaw to load new skills.
```

## GitHub Authorization Flow

If `gh auth status` fails, the script launches an interactive login:

1. **Protocol**: HTTPS (default) → Enter
2. **Authenticate Git?**: Y → Enter
3. **Auth method**: "Login with a web browser" → Enter
4. **One-time code**: User visits https://github.com/login/device and enters the displayed code (e.g. `E604-15A0`)
5. **Browser auth**: Complete in browser → Done

After first login, credentials are cached — subsequent backups/restores are fully automatic.

## What Gets Backed Up / Restored

| Source | Backup location in repo |
|--------|-------------------------|
| `~/.agents/skills/` | `skills-backup/all-skills/agents-skills/` |
| `~/.openclaw/skills/` | `skills-backup/all-skills/openclaw-skills/` |

**Excluded**: `.venv/`, `__pycache__/`, `node_modules/`, `.git/`

## GitHub Repo

- **URL**: https://github.com/scchin/openclaw-workspace
- **Skills backup**: `skills-backup/all-skills/agents-skills/` and `skills-backup/all-skills/openclaw-skills/`

## Prerequisites (on new device)

1. `gh` CLI installed: `brew install gh`
2. GitHub authentication: `gh auth login`
3. Run restore:
  ```bash
  bash /Users/KS/.openclaw/skills/skills-backup-github/scripts/restore.sh
  ```

Alternatively, if the skill itself hasn't been restored yet, clone the repo directly:
  ```bash
  git clone https://github.com/scchin/openclaw-workspace.git ~/.openclaw/workspace
  bash ~/.openclaw/workspace/skills-backup/all-skills/openclaw-skills/skills-backup-github/scripts/restore.sh
  ```