---
name: skills-github-backup
description: 備份與還原所有 OpenClaw 技能至 GitHub。
author: King Sean of KS
category: System
tags: [backup, github, sync]
---

# Skills Backup GitHub

Backup all OpenClaw skills to GitHub, or restore them on a new device.

## Backup (on any device)

When user says "backup skills", "sync skills to GitHub", or requests a full/incremental skill backup:

```bash
bash /Users/KS/.openclaw/skills/skills-github-backup/scripts/backup.sh
```

## Restore (on a new device)

When user says "restore skills", "download skills", or "還原技能":

```bash
bash /Users/KS/.openclaw/skills/github-backup/scripts/restore.sh
```
