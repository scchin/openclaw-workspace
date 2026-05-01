import os
import subprocess
import shutil

class SyncHandler:
    """
    Handles the synchronization of soul backups between local storage
    and a private GitHub repository with deterministic binary enforcement.
    [Immortal Edition v2.3.1 - Pulse Push]

    變更紀錄:
    v2.3.1-hotfix-2 (2026-04-25)
      - [FIX] 廢除 git init 在 launchd 乾淨環境下的不穩定行為，改為嚴謹的 clone/pull 流程
      - [FIX] 廢除 git reset --soft origin/main，改為 git pull --rebase，確保增量更新
      - [FIX] 廢除 git push -f，保護雲端歷史數據
      - [FIX] 加入 git user.email / user.name 設定，防止 launchd 環境 commit 失敗
      - [FIX] 加入 git config 允許 push 到非 bare repo
    """

    def __init__(self, github_token, repo_name):
        self.github_token = github_token
        self.repo_name = repo_name
        if github_token and repo_name:
            self.remote_url = f"https://{github_token}@github.com/{repo_name}.git"
        else:
            self.remote_url = None

    def run_git(self, args, cwd=None):
        try:
            result = subprocess.run(
                ["git"] + args, cwd=cwd, capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Git Command Error: {e.stderr}")
            raise e

    def _ensure_git_repo(self, base_dir):
        """
        確保 base_dir 是一個有效的 Git Repo，且已正確指向遠端。
        若不是，則 clone 遠端倉庫。
        """
        git_dir = os.path.join(base_dir, ".git")
        if not os.path.exists(git_dir):
            print(f"📦 [Pulse Push] No Git Repo found. Cloning remote...", flush=True)
            # 備份現有檔案
            tmp_backup = base_dir + "_tmp_backup"
            shutil.copytree(base_dir, tmp_backup, dirs_exist_ok=True)
            shutil.rmtree(base_dir, ignore_errors=True)
            self.run_git(["clone", self.remote_url, base_dir])
            # 把備份檔案移回（不覆蓋已有的同名 git 物件）
            for item in os.listdir(tmp_backup):
                src = os.path.join(tmp_backup, item)
                dst = os.path.join(base_dir, item)
                if not os.path.exists(dst):
                    shutil.move(src, dst)
            shutil.rmtree(tmp_backup, ignore_errors=True)
        else:
            # 確保 remote URL 正確
            try:
                self.run_git(["remote", "add", "origin", self.remote_url], cwd=base_dir)
            except Exception:
                self.run_git(["remote", "set-url", "origin", self.remote_url], cwd=base_dir)

        # launchd 環境下 git 沒有 user 設定會造成 commit 失敗，確保有設定
        self.run_git(["config", "user.email", "soul-sync@openclaw.local"], cwd=base_dir)
        self.run_git(["config", "user.name", "OpenClaw Soul Sync"], cwd=base_dir)
        self.run_git(["config", "http.postBuffer", "2147483648"], cwd=base_dir)

    def push_to_github(self, local_path):
        """
        [Pulse Push v2.3.1-hotfix-2]
        分批推送，防止 GitHub HTTP 500。
        使用增量更新策略，絕不覆蓋雲端歷史。
        """
        if not self.remote_url:
            print("❌ [Pulse Push] ABORTED: No GitHub token or repo configured.", flush=True)
            return False

        try:
            base_dir = os.path.dirname(local_path)
            folder_name = os.path.basename(local_path)

            print(f"🚀 [Pulse Push] Initializing Git Fortress at {base_dir}...", flush=True)
            self._ensure_git_repo(base_dir)

            # [CRITICAL] 先與遠端同步，確保是增量更新而非覆蓋
            try:
                print("📡 [Pulse Push] Syncing with remote history...", flush=True)
                self.run_git(["fetch", "origin"], cwd=base_dir)
                # 檢查 origin/main 是否存在
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", "origin/main"],
                    cwd=base_dir, capture_output=True, text=True
                )
                if result.returncode == 0:
                    # 遠端有 main 分支，rebase 到最新
                    self.run_git(["rebase", "origin/main"], cwd=base_dir)
                else:
                    print("ℹ️ [Pulse Push] First push. No remote main branch yet.", flush=True)
            except Exception as e:
                print(f"ℹ️ [Pulse Push] Remote sync skipped: {e}", flush=True)

            # 取得要上傳的檔案清單（.bin 分卷 + manifest，跳過主壓縮包本體以免超過 GitHub 100MB 限制）
            all_files = sorted([
                f for f in os.listdir(local_path)
                if f.endswith(".bin") or f == "backup_manifest.json"
            ])

            if not all_files:
                print("⚠️ [Pulse Push] No files to upload!", flush=True)
                return False

            # 分批提交與推送
            batch_size = 5
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                print(f"📦 [Pulse Push] Batch {i // batch_size + 1}: Adding {len(batch)} files...", flush=True)
                for filename in batch:
                    file_path = os.path.join(folder_name, filename)
                    self.run_git(["add", file_path], cwd=base_dir)

                self.run_git([
                    "commit", "-m",
                    f"System Sync: {folder_name} (Batch {i // batch_size + 1})"
                ], cwd=base_dir)

                print(f"📡 [Pulse Push] Transmitting batch...", flush=True)
                # [CRITICAL FIX] 不使用 -f，保護歷史數據
                self.run_git(["push", "origin", "HEAD:main"], cwd=base_dir)

            print(f"✅ [Pulse Push] ALL data successfully deployed to GitHub.", flush=True)
            return True

        except Exception as e:
            print(f"❌ [Pulse Push] FAILED: {str(e)}", flush=True)
            return False

    def list_remote_backups(self):
        """
        [Cloud Discovery] 
        列出 GitHub 倉庫中所有可用的備份，並提取日期與大小資訊。
        """
        try:
            print("📡 [Discovery] Scanning GitHub vault for available souls...", flush=True)
            # 使用 ls-tree 獲取遠端目錄結構
            output = self.run_git(["ls-tree", "-d", "origin/main"])
            lines = output.strip().split("\n")
            
            backups = []
            for line in lines:
                if not line: continue
                # 結構: 040000 tree SHA    FOLDER_NAME
                parts = line.split()
                if len(parts) >= 4:
                    folder = parts[3]
                    if folder.startswith("soul_"):
                        backups.append(folder)
            
            return sorted(backups, reverse=True)
        except Exception as e:
            print(f"⚠️ [Discovery] Failed to list remote backups: {e}")
            return []

    def pull_from_github(self, folder_name, dest_path):
        """
        [RESTORE GENE]
        從 GitHub clone 備份到本地進行沙盒驗證。
        注意：clone 後的結構為 dest_path/ 直接含所有檔案。
        folder_name 參數供上層辨識用途。
        """
        try:
            print(f"📡 [Restore] Pulling {folder_name} from GitHub...", flush=True)
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            os.makedirs(dest_path)
            self.run_git(["clone", "--depth", "1", self.remote_url, dest_path])
            return True
        except Exception as e:
            print(f"❌ [Restore] FAILED: {str(e)}", flush=True)
            return False
