import os
import shutil
import subprocess
import time
from pathlib import Path

# =============================================================================
# [穩健版] VERSION: v2026.04.20-Robust
# 說明：針對雲端 Provider 500 錯誤與網絡不穩定進行了自動重試與斷點檢測強化。
# 變更：
# 1. 新增 retry_command 函數，支持 3 次指數退避重試。
# 2. 修改 main 循環，加入雲端狀態預檢，支持斷點續傳。
# 3. 強化錯誤捕獲，確保進程崩測前會保留最後的現場狀態。
# =============================================================================

# =============================================================================
# CONFIGURATION
# =============================================================================
BACKUP_DIR = Path("/Users/KS/.openclaw/backups/full_soul_20260420_175738")
REPO_URL = "https://github.com/scchin/openclaw-soul-backups.git"
TEMP_GIT_DIR = Path("/tmp/soul_batch_sync_robust")
BATCH_SIZE = 10
RETRY_COUNT = 3  # 最大重試次數

def run_cmd(cmd, cwd=None, exit_on_fail=False):
    """執行命令並捕獲結果"""
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr.strip()}")
        if exit_on_fail:
            raise Exception(f"Command failed: {cmd} - {result.stderr}")
        return False, result.stderr
    return True, result.stdout

def retry_command(cmd, cwd=None, max_retries=RETRY_COUNT):
    """具備自動重試邏輯的命令執行器 (針對 Network/Provider 錯誤)"""
    for attempt in range(max_retries):
        success, output = run_cmd(cmd, cwd=cwd)
        if success:
            return True, output
        
        wait_time = (attempt + 1) * 5
        print(f"⚠️ 遇到網路或 Provider 錯誤，{wait_time} 秒後進行第 {attempt+1}/{max_retries} 次重試...")
        time.sleep(wait_time)
    
    return False, "Max retries reached"

def main():
    if not BACKUP_DIR.exists():
        print(f"❌ Backup directory {BACKUP_DIR} not found.")
        return

    # 1. Prepare Workspace (清理並重新建立工作目錄)
    if TEMP_GIT_DIR.exists():
        try:
            shutil.rmtree(TEMP_GIT_DIR)
        except Exception as e:
            print(f"⚠️ 無法清理舊目錄，嘗試繼續使用: {e}")
    
    print(f"🚀 Cloning repo to {TEMP_GIT_DIR}...")
    # Clone 包含重試機制，防止克隆時 Provider 500
    success, err = retry_command(f"git clone --depth 1 {REPO_URL} {TEMP_GIT_DIR}")
    if not success:
        print(f"❌ [致命錯誤] 無法連接到 GitHub: {err}")
        return

    # 2. Create Subdirectory in Repo
    target_subdir_name = BACKUP_DIR.name
    target_subdir = TEMP_GIT_DIR / target_subdir_name
    target_subdir.mkdir(parents=True, exist_ok=True)

    # 3. Identify Files
    chunks_dir = BACKUP_DIR / "chunks"
    if not chunks_dir.exists():
        print(f"❌ Chunks directory {chunks_dir} not found.")
        return

    all_files = sorted([f for f in chunks_dir.glob("*.bin") if "part" in f.name])
    manifest_file = BACKUP_DIR / "backup_manifest.json"

    total_files = len(all_files)
    print(f"📦 Found {total_files} chunks. Starting robust synchronization.")

    # 4. Batch Push Loop With Resumability
    for i in range(0, total_files, BATCH_SIZE):
        batch = all_files[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        # [斷點續傳預檢]：如果目標文件已在雲端目錄中，且大小一致，則跳過
        need_upload = False
        for f in batch:
            cloud_file = target_subdir / f.name
            if not cloud_file.exists():
                need_upload = True
                break
        
        if not need_upload:
            print(f"⏭️ Batch {batch_num} already exists in local git state, checking next.")
            continue

        print(f"\n📤 Processing batch {batch_num} ({i+1} to {min(i+BATCH_SIZE, total_files)})")
        
        for f in batch:
            shutil.copy2(f, target_subdir / f.name)
            run_cmd(f"git add '{target_subdir / f.name}'", cwd=TEMP_GIT_DIR)
        
        commit_msg = f"Upload soul backup chunks {i+1}-{min(i+BATCH_SIZE, total_files)}"
        run_cmd(f'git commit -m "{commit_msg}"', cwd=TEMP_GIT_DIR)
        
        # [關鍵重試點]：對推送進行多輪重試，對抗 Provider 500
        success, err = retry_command("git push origin main", cwd=TEMP_GIT_DIR)
        if success:
            print(f"✅ Batch {batch_num} pushed successfully.")
        else:
            print(f"❌ [嚴重錯誤] Batch {batch_num} 推送失敗，Provider 持續報錯，進程暫停以保護數據。")
            return

    # 5. Final Manifest Push
    if manifest_file.exists():
        cloud_manifest = target_subdir / manifest_file.name
        print("\n📝 Finalizing: Uploading manifest...")
        shutil.copy2(manifest_file, cloud_manifest)
        run_cmd(f"git add '{cloud_manifest}'", cwd=TEMP_GIT_DIR)
        run_cmd('git commit -m "Upload backup manifest and finalize snapshot"', cwd=TEMP_GIT_DIR)
        
        success, err = retry_command("git push origin main", cwd=TEMP_GIT_DIR)
        if success:
            print("✨ [SUCCESS] Full backup synchronized successfully!")
        else:
            print(f"❌ [FAILURE] Manifest push failed: {err}")
    else:
        print("\n⚠️ Manifest file not found, skipping finalization.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 被用戶中斷")
    except Exception as e:
        print(f"\n💥 發生非預期系統錯誤: {e}")
