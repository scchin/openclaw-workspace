import os
import subprocess
import shutil

class SyncHandler:
    """
    Handles the synchronization of soul backups between local storage 
    and a private GitHub repository with deterministic binary enforcement.
    [Immortal Edition v2.3.1 - Pulse Push]
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

    def push_to_github(self, local_path):
        """
        [Pulse Push v2.3.1]
        Pushes chunks in batches of 5 to avoid GitHub HTTP 500 errors.
        """
        try:
            base_dir = os.path.dirname(local_path)
            folder_name = os.path.basename(local_path)
            
            print(f"🚀 [Pulse Push] Initializing Git Fortress at {base_dir}...", flush=True)
            if not os.path.exists(os.path.join(base_dir, ".git")):
                self.run_git(["init"], cwd=base_dir)
            self.run_git(["config", "http.postBuffer", "2147483648"], cwd=base_dir)
            
            try:
                self.run_git(["remote", "add", "origin", self.remote_url], cwd=base_dir)
            except:
                self.run_git(["remote", "set-url", "origin", self.remote_url], cwd=base_dir)

            all_files = sorted([f for f in os.listdir(local_path) if f.endswith(".bin") or f == "backup_manifest.json" or f.endswith(".tar.gz")])
            batch_files = [f for f in all_files if not f.endswith(".tar.gz") or os.path.getsize(os.path.join(local_path, f)) < 200*1024*1024]
            
            batch_size = 5
            for i in range(0, len(batch_files), batch_size):
                batch = batch_files[i:i + batch_size]
                print(f"📦 [Pulse Push] Batch {i//batch_size + 1}: Adding {len(batch)} files...", flush=True)
                for filename in batch:
                    file_path = os.path.join(folder_name, filename)
                    self.run_git(["add", file_path], cwd=base_dir)
                
                self.run_git(["commit", "-m", f"Pulse Push {i//batch_size + 1}: {folder_name}"], cwd=base_dir)
                print(f"📡 [Pulse Push] Transmitting batch...", flush=True)
                self.run_git(["push", "-f", "origin", "HEAD:main"], cwd=base_dir)
            
            print(f"✅ [Pulse Push] ALL data successfully deployed to GitHub.", flush=True)
            return True
        except Exception as e:
            print(f"❌ [Pulse Push] FAILED: {str(e)}", flush=True)
            return False

    def pull_from_github(self, folder_name, dest_path):
        """
        [RESTORE GENE]
        Pulls data back from GitHub for sandbox verification.
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
