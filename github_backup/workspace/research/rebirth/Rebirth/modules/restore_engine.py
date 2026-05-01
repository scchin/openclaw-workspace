import os
import tarfile
import shutil
import re
from utils.path_resolver import PathResolver

class RestoreEngine:
    """
    Handles the decompression, physical distribution, and 
    path calibration of the soul backup.
    """
    
    def __init__(self, target_home=None):
        self.target_home = target_home or os.path.expanduser("~")

    def restore(self, archive_dir, old_user_home=None):
        """
        Unpacks the archive and calibrates all paths.
        archive_dir: 包含分卷檔案與 manifest 的目錄
        """
        temp_extract_dir = os.path.join(self.target_home, ".openclaw/restore_tmp")
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        try:
            manifest_path = os.path.join(archive_dir, "backup_manifest.json")
            if not os.path.exists(manifest_path):
                raise RuntimeError("Restore Error: backup_manifest.json not found.")
            
            with open(manifest_path, 'r') as f:
                import json
                manifest = json.load(f)
            
            main_archive_name = manifest["main_archive"]["name"]
            final_archive_path = os.path.join(archive_dir, main_archive_name)
            
            # 1. 如果是分卷備份，先執行重組
            if manifest.get("chunks"):
                print(f"🔍 [Restore] Reassembling {len(manifest['chunks'])} chunks...", flush=True)
                self._reassemble_chunks(archive_dir, manifest, final_archive_path)

            # 2. 解壓縮到暫存緩衝區
            print(f"📦 [Restore] Extracting {main_archive_name}...", flush=True)
            with tarfile.open(final_archive_path, "r:gz") as tar:
                tar.extractall(path=temp_extract_dir)

            # 3. 物理分發 (Physical Distribution)
            self._distribute_files(temp_extract_dir)

            # 3. Path Calibration
            if old_user_home:
                resolver = PathResolver(old_root=old_user_home, new_root=self.target_home)
                # Calibrate config, workspace, skills and LaunchAgents
                resolver.calibrate_recursive(os.path.join(self.target_home, ".openclaw"))
                resolver.calibrate_recursive(os.path.join(self.target_home, ".agents"))
                resolver.calibrate_recursive(os.path.join(self.target_home, "Library", "LaunchAgents"))
            
            return True
        except Exception as e:
            print(f"❌ [Restore] CRITICAL FAILURE: {e}")
            return False
        finally:
            if os.path.exists(temp_extract_dir):
                self._rmtree_robust(temp_extract_dir)

    def _reassemble_chunks(self, archive_dir, manifest, output_path):
        """將 .bin 分卷重組回原始的 .tar.gz"""
        chunks = sorted(manifest["chunks"], key=lambda x: int(re.search(r'part(\d+)', x["name"]).group(1)))
        with open(output_path, 'wb') as outfile:
            for chunk_info in chunks:
                chunk_path = os.path.join(archive_dir, chunk_info["name"])
                with open(chunk_path, 'rb') as infile:
                    outfile.write(infile.read())
        print(f"✅ [Restore] Reassembly complete: {output_path}")

    def _rmtree_robust(self, path):
        def handle_error(func, path, exc_info):
            os.chmod(path, 0o777)
            subprocess.run(["chflags", "nouchg", path], capture_output=True)
            try: func(path)
            except: pass
        if os.path.exists(path):
            shutil.rmtree(path, onerror=handle_error)

    def _distribute_files(self, staging_dir):
        """
        [不朽級分發] 將檔案精確送回原始物理路徑，確保一鍵啟動。
        """
        for item in os.listdir(staging_dir):
            src = os.path.join(staging_dir, item)
            dst = None
            
            # --- 精準路徑對位 ---
            if item.endswith(".plist"):
                dst = os.path.join(self.target_home, "Library/LaunchAgents", item)
            elif item == "openclaw.json":
                dst = os.path.join(self.target_home, ".openclaw/openclaw.json")
            elif item == ".env":
                dst = os.path.join(self.target_home, ".openclaw/.env")
            elif item == "workspace":
                dst = os.path.join(self.target_home, ".openclaw/workspace")
            elif item == "repo":
                dst = os.path.join(self.target_home, ".openclaw/repo")
            elif item == "skills":
                dst = os.path.join(self.target_home, ".openclaw/skills")
            elif item == "agents":
                # [FIX] ~/.agents/skills/ 目錄（含技能本體，如 soul-sync）
                dst = os.path.join(self.target_home, ".agents")
            else:
                # 預設歸位於 .openclaw 核心目錄
                dst = os.path.join(self.target_home, ".openclaw", item)
            
            # --- 物理部署執行 ---
            if dst:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isdir(src):
                    if os.path.exists(dst): shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                print(f"✅ [Restore] {item} -> {dst}")
