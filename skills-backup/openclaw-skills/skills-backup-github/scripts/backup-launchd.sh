#!/bin/bash
# Wrapper for launchd: calls backup.sh with dynamic daily log
LOG_DIR="/Users/KS/.openclaw/workspace/logs"
BACKUP_SCRIPT="/Users/KS/.openclaw/skills/skills-backup-github/scripts/backup.sh"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/backup-$TODAY.log"

# Ensure log dir exists
mkdir -p "$LOG_DIR"

# Run backup, output to dated log
/bin/bash "$BACKUP_SCRIPT" >> "$LOG_FILE" 2>&1
