#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

# =============================================================================
# ARC (Atomic Report-and-Clear) Tool
# Purpose: Force a report before allowing task clearance from the ledger.
# =============================================================================

PENDING_TASKS_FILE = os.path.expanduser("~/.openclaw/workspace/pending_tasks.json")
HISTORY_LOG_FILE = os.path.expanduser("~/.openclaw/workspace/closure_history.log")

def log_report(task_name, report):
    """Archive the report to the long-term closure log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] TASK: {task_name}\nREPORT:\n{report}\n{'-'*40}\n"
    try:
        with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        return True
    except Exception as e:
        print(f"Error writing to history log: {e}")
        return False

def clear_task(task_name):
    """Remove the specific task from pending_tasks.json."""
    try:
        if not os.path.exists(PENDING_TASKS_FILE):
            return False, "Pending tasks file not found."
        
        with open(PENDING_TASKS_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        
        # Filter out the task with the matching name
        new_tasks = [t for t in tasks if t.get("task") != task_name]
        
        if len(new_tasks) == len(tasks):
            return False, f"Task '{task_name}' not found in ledger."
        
        with open(PENDING_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_tasks, f, indent=2, ensure_ascii=False)
        
        return True, "Task cleared from ledger."
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 arc_complete_task.py \"Task Name\" \"Report Content\"")
        sys.exit(1)
    
    task_name = sys.argv[1]
    report_content = sys.argv[2]
    
    # 1. Validation: Report must not be too brief
    if len(report_content.strip()) < 20:
        print("❌ ERROR: Report content is too brief. A detailed conclusion report is required for closure.")
        sys.exit(1)
    
    # 2. Archive Report
    if not log_report(task_name, report_content):
        print("❌ ERROR: Failed to archive report to history log.")
        sys.exit(1)
    
    # 3. Clear Ledger
    success, msg = clear_task(task_name)
    if not success:
        print(f"❌ ERROR: {msg}")
        sys.exit(1)
    
    print(f"✅ [CONFIRMED] Task '{task_name}' cleared. Report archived. Closure complete.")

if __name__ == "__main__":
    main()
