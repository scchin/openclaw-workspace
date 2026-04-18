#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime

# =============================================================================
# System Backup Manager
# =============================================================================

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
SYNC_SCRIPT = os.path.join(WORKSPACE, "system-full-sync.sh")
CHANGELOG_FILE = os.path.join(WORKSPACE, f"CHANGELOG_{datetime.now().strftime('%Y-%m-%d')}.md")

def log_change(summary):
    """將變更摘要寫入當日 Changelog 文件"""
    timestamp = datetime.now().strftime("%H:%M")
    entry = f"- **{timestamp}**: {summary}\n"
    
    try:
        if not os.path.exists(CHANGELOG_FILE):
            with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"# 📅 系統變更完整追蹤表 ({datetime.now().strftime('%Y-%m-%d')})\n\n")
        
        with open(CHANGELOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except Exception as e:
        print(f"Error writing to changelog: {e}")
        return False

def run_sync():
    """執行全量同步腳本"""
    try:
        # 執行 system-full-sync.sh
        result = subprocess.run(["bash", SYNC_SCRIPT], capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except Exception as e:
        return False, str(e)

def main(summary="執行例行系統全量同步"):
    print(f"🚀 Starting System Backup with summary: {summary}")
    
    # 1. 記錄變更
    if log_change(summary):
        print(f"✅ Changelog updated: {CHANGELOG_FILE}")
    else:
        print("⚠️ Changelog update failed, continuing sync...")

    # 2. 執行同步
    success, output = run_sync()
    
    if success:
        print("✅ System full sync completed successfully.")
        print(output)
    else:
        print(f"❌ System full sync failed:\n{output}")
        exit(1)

if __name__ == "__main__":
    import sys
    user_summary = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "執行例行系統全量同步"
    main(user_summary)
