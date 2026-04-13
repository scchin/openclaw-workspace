---
name: skills-github-backup
description: 備份與還原所有 OpenClaw 技能至 GitHub（v1.0.1）。
author: King Sean of KS
category: System
tags: [backup, github, sync]
---

# Skills Backup GitHub (v1.0.1)

Backup all OpenClaw skills to GitHub, or restore them on a new device.

## Backup (on any device)

When user says "backup skills", "sync skills to GitHub", or requests a full/incremental skill backup:

```bash
bash /Users/KS/.openclaw/skills/skills-github-backup/scripts/backup.sh
```

## Restore (on a new device)

When user says "restore skills", "download skills", or "還原技能":

```bash
bash /Users/KS/.openclaw/skills/skills-github-backup/scripts/restore.sh
```

---
## 更新紀錄
- v1.0.1 (2026-04-13): 修正執行路徑錯誤。將 `github-backup` 修正為 `skills-github-backup` 以匹配實際目錄結構。
