import os
import shutil
import glob
import re
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("/Users/KS/.openclaw/workspace/logs/workspace_cleanup.log"),
        logging.StreamHandler()
    ]
)

WORKSPACE_DIR = "/Users/KS/.openclaw/workspace"
RESEARCH_DIR = os.path.join(WORKSPACE_DIR, "research")

# 🛡️ 3. 保留名單 (絕對不觸碰)
PROTECTED_ITEMS = {
    "AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md", "MEMORY.md",
    "system_gene_sentry.py", "arc_complete_task.py",
    "memory", "logs", "bin", "config", "skills", "powerskills", ".genome", "Sutra_Library"
}

# 🗑️ 1. 刪除清單
DELETE_DIRS = [
    "test_env_physical", "sandbox", "benchmark_swarm_baseline", 
    "benchmark_swarm_optimized", "mempalace_eval"
]

DELETE_GLOBS = [
    "algorithm_case_*.py", "case[0-9]+_algorithms.py", "case_[0-9]+.py",
    "test-*.py", "test_*.py", "test_*.tx*", "relational_test*.py", "routing_test*.py",
    "extract_*.py", "chunk*.json", "pts_cases.json", "symbol_map.json", "reviews_buffer.json",
    "test_write.txt", "final_report.md", "temp_response_draft.md", "final_proposal_draft.md",
    "folder_report*.py", "folder_stats.py", "report_draft.txt", "project_closure_report_*.md",
    "batch_[0-9]+_papers.txt", ".DS_Store"
]

# 📦 2. 遷移地圖
MIGRATION_MAP = {
    "clawteam_research": "clawteam",
    "social_market_research": "social_market",
    "exp_mempalace": "mempalace_exp",
    "Rebirth": "rebirth",
    "swarm_stability": "swarm_stability",
    "research_salvage": "salvage",
    "[SENSITIVE_TOKEN_HARD_REDACTED].skill": "mempalace_fintune",
    "google_places_parser.py": "google-maps",
}

# 模式匹配遷移 (Wildcards)
PATTERN_MIGRATIONS = [
    (r"mempalace_.*\.(md|json)", "mempalace"),
    (r"hallucination_.*", "hallucination"),
    (r"openclaw_forum_.*", "hallucination"),
    (r"(經驗|待整理|hezuo_.*|yibendiao_raw\.json)", "misc")
]

def is_protected(name):
    return name in PROTECTED_ITEMS

def run_cleanup():
    logging.info("=== Starting Workspace Cleanup Process ===")
    
    # --- 1. 執行刪除 ---
    for d in DELETE_DIRS:
        target = os.path.join(WORKSPACE_DIR, d)
        if os.path.exists(target) and not is_protected(d):
            logging.info(f"Deleting directory: {d}")
            shutil.rmtree(target, ignore_errors=True)

    for pattern in DELETE_GLOBS:
        for f in glob.glob(os.path.join(WORKSPACE_DIR, pattern)):
            name = os.path.basename(f)
            if not is_protected(name):
                logging.info(f"Deleting file: {name}")
                os.remove(f)

    # 處理噪聲文件 (極長文件名)
    for f in os.listdir(WORKSPACE_DIR):
        if len(f) > 80 and not os.path.isdir(os.path.join(WORKSPACE_DIR, f)):
             logging.info(f"Deleting noise file (long name): {f[:20]}...")
             os.remove(os.path.join(WORKSPACE_DIR, f))

    # --- 2. 執行遷移 ---
    if not os.path.exists(RESEARCH_DIR):
        os.makedirs(RESEARCH_DIR)

    # 靜態映射
    for src, dest_folder in MIGRATION_MAP.items():
        src_path = os.path.join(WORKSPACE_DIR, src)
        if os.path.exists(src_path) and not is_protected(src):
            dest_path = os.path.join(RESEARCH_DIR, dest_folder)
            os.makedirs(dest_path, exist_ok=True)
            logging.info(f"Migrating {src} to research/{dest_folder}")
            shutil.move(src_path, os.path.join(dest_path, src))

    # 模式匹配映射
    for f in os.listdir(WORKSPACE_DIR):
        if is_protected(f) or f == "research":
            continue
            
        for pattern, dest_folder in PATTERN_MIGRATIONS:
            if re.match(pattern, f):
                src_path = os.path.join(WORKSPACE_DIR, f)
                dest_path = os.path.join(RESEARCH_DIR, dest_folder)
                os.makedirs(dest_path, exist_ok=True)
                logging.info(f"Pattern Match: Migrating {f} to research/{dest_folder}")
                # 使用 shutil.move，如果目標已存在則覆蓋或報錯
                try:
                    shutil.move(src_path, os.path.join(dest_path, f))
                except Exception as e:
                    logging.warning(f"Failed to move {f}: {e}")
                break

    logging.info("=== Cleanup Process Completed ===")

if __name__ == "__main__":
    run_cleanup()
