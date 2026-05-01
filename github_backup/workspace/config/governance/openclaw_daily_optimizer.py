import os
import subprocess
import logging
import sys

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("/Users/KS/.openclaw/workspace/logs/daily_optimizer.log"),
        logging.StreamHandler()
    ]
)

GOVERNANCE_DIR = "/Users/KS/.openclaw/workspace/config/governance"

def run_task(name, script_path):
    logging.info(f"--- Running Task: {name} ---")
    if not os.path.exists(script_path):
        logging.error(f"Script not found: {script_path}")
        return False
    
    try:
        # 使用相同的 Python 解釋器執行
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Task {name} failed with exit code {e.returncode}")
        logging.error(e.stderr)
        return False

def main():
    logging.info("🚀 [OpenClaw Daily Optimizer] Starting Automated Maintenance Cycle")

    # 1. 執行工作區清理與歸檔
    cleanup_script = os.path.join(GOVERNANCE_DIR, "workspace_cleanup.py")
    run_task("Workspace Cleanup & Archiving", cleanup_script)

    # 2. 執行全局環境碎片清理 (安全沙盒保護機制)
    global_cleaner_script = os.path.join(GOVERNANCE_DIR, "openclaw_global_cleaner.py")
    run_task("Global Environment Purge", global_cleaner_script)

    logging.info("✨ [OpenClaw Daily Optimizer] Maintenance Cycle Finished")

if __name__ == "__main__":
    main()
