import os
import tarfile
import shutil
from utils.path_resolver import PathResolver

class RestoreEngine:
    """
    Handles the decompression, physical distribution, and 
    path calibration of the soul backup.
    """
    
    def __init__(self, target_home=None):
        self.target_home = target_home or os.path.expanduser("~")

    def restore(self, archive_path, old_user_home=None):
        """
        Unpacks the archive and calibrates all paths.
        """
        temp_extract_dir = os.path.join(self.target_home, ".openclaw/restore_tmp")
        
        try:
            # 1. Decompress to temporary buffer
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=temp_extract_dir)

            # 2. Physical Distribution
            # In a real scenario, we'd map the staged files back to their 
            # original absolute paths.
            self._distribute_files(temp_extract_dir)

            # 3. Path Calibration
            if old_user_home:
                resolver = PathResolver(old_root=old_user_home, new_root=self.target_home)
                # Calibrate config and workspace
                resolver.calibrate_recursive(os.path.join(self.target_home, ".openclaw"))
                resolver.calibrate_recursive(os.path.join(self.target_home, ".openclaw/workspace"))
                resolver.calibrate_recursive(os.path.join(self.target_home, ".agents/skills"))
            
            return True
        finally:
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)

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
