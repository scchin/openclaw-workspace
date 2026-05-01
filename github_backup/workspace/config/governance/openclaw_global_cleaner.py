import os
import shutil
import re
import sys
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("/Users/KS/.openclaw/workspace/logs/global_cleanup.log"),
        logging.StreamHandler()
    ]
)

def run_global_cleanup(root_dir="/Users/KS/.openclaw", dry_run=False):
    logging.info(f"🚀 Starting Global Cleanup in: {root_dir} (Dry Run: {dry_run})")
    
    # 絕對禁區 (Blacklist) - Do not traverse into these deep system folders
    EXCLUDE_DIRS = {
        "node_modules", ".git", "repo", "lib", "src", "dist",
        "workspace", "agents", "guardian", "plugins", "cache", "dna"
    }
    
    # 直接刪除的特定垃圾目錄 (僅限根目錄下)
    ROOT_DELETE_DIRS = {"test_dir", "workspace-benchmark"}
    
    # 要刪除的檔案模式 (Regex)
    FILE_PATTERNS = [
        r".*\.bak(\.\d+)?$",             # e.g. openclaw.json.bak, openclaw.json.bak.1
        r".*\.clobbered\..*$",          # e.g. openclaw.json.clobbered.2026-04-28...
        r".*\.qclaw\.bak\..*\.json$",   # e.g. openclaw.json.qclaw.bak.2026...json
        r".*\.tmp$",                    # e.g. openclaw.json.tmp
        r"^sync_progress\.log$"         # Specific noise log
    ]
    
    deleted_files = 0
    deleted_dirs = 0

    # 1. 刪除特定垃圾目錄
    for d in ROOT_DELETE_DIRS:
        dir_path = os.path.join(root_dir, d)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            logging.info(f"💥 [DELETE DIR] {dir_path}")
            if not dry_run:
                shutil.rmtree(dir_path, ignore_errors=True)
            deleted_dirs += 1

    # 2. 遞迴掃描並刪除垃圾檔案
    for current_root, dirs, files in os.walk(root_dir):
        # 攔截並移除禁區目錄，阻止 os.walk 進入
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            for pattern in FILE_PATTERNS:
                if re.match(pattern, file):
                    file_path = os.path.join(current_root, file)
                    logging.info(f"💥 [DELETE FILE] {file_path}")
                    if not dry_run:
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logging.warning(f"⚠️ Failed to remove {file_path}: {e}")
                    deleted_files += 1
                    break # 避免重複匹配

    logging.info(f"✨ Global Cleanup finished. Files deleted: {deleted_files}, Directories deleted: {deleted_dirs}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/Users/KS/.openclaw"
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        sys.argv.remove("--dry-run")
        target = sys.argv[1] if len(sys.argv) > 1 else target
        
    run_global_cleanup(target, dry_run=dry_run)
