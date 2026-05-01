import os
import sys
import subprocess
import time
import tarfile
import shutil
from datetime import datetime
import math
import re
import json
import hashlib

class Packer:
    """
    Industrial-grade backup engine for OpenClaw.
    [Precision Lockdown Version] - Focuses on minimal volume with maximum state retention.
    """
    
    def __init__(self, backup_root=None):
        self.home = os.path.expanduser("~")
        self.workspace = os.path.join(self.home, ".openclaw/workspace")
        self.backup_root = backup_root or os.path.join(self.home, ".openclaw/backups")
        
        # 精確排除清單 (系統級)
        self.exclusions = {
            "logs", "cache", ".DS_Store", "__pycache__", "backups", 
            "tmp", "temp"
        }
        
        # 瀏覽器「去脂」排除清單 (針對 Browser Profile)
        self.browser_fat_exclusions = {
            "Cache", "Code Cache", "GPUCache", "Service Worker/CacheStorage",
            "Media Cache", "GrShaderCache", "GraphiteDawnCache", "ShaderCache"
        }
        
        self.modes = {
            "core": ["config", "memory", "workspace", "skills", "lockfiles"],
            "full": ["config", "memory", "workspace", "skills", "canvas", "browser_profile", "repo", "lockfiles"]
        }
        self.targets = {
            "config": [
                os.path.join(self.home, "Library/LaunchAgents/ai.openclaw.gateway.plist"),
                os.path.join(self.home, ".openclaw/.env"),
                os.path.join(self.home, ".openclaw/agents/main/agent/auth-profiles.json"),
                os.path.join(self.home, ".openclaw/agents/main/agent/models.json"),
                os.path.join(self.home, ".openclaw/openclaw.json"),
                os.path.join(self.home, ".openclaw/exec-approvals.json"),
                os.path.join(self.home, ".openclaw/system_clone_config.json"),
            ],
            "memory": [os.path.join(self.home, ".openclaw/memory")],
            "workspace": [self.workspace],
            "skills": [
                os.path.join(self.home, ".openclaw/skills"),
                os.path.join(self.home, ".agents/skills"),
            ],
            "canvas": [os.path.join(self.home, ".openclaw/canvas")],
            "browser_profile": [os.path.join(self.home, ".openclaw/browser/openclaw")],
            "repo": [os.path.join(self.home, ".openclaw/repo")],
            "lockfiles": "auto"
        }

    def _get_all_lockfiles(self):
        locks = []
        for root, dirs, files in os.walk(self.workspace):
            if "lock.json" in files:
                locks.append(os.path.join(root, "lock.json"))
        return locks

    def _calculate_sha256(self, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _sanitize_secrets(self, src_path, dst_path):
        secret_pattern = re.compile(r'(_KEY|API_KEY|TOKEN|SECRET)', re.IGNORECASE)
        try:
            with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if src_path.endswith('.json'):
                try:
                    data = json.loads(content)
                    def mask_dict(d):
                        if isinstance(d, dict):
                            return {k: (mask_dict(v) if isinstance(v, (dict, list)) else 
                                    ("YOUR_TOKEN_HERE" if secret_pattern.search(k) else v)) for k, v in d.items()}
                        elif isinstance(d, list):
                            return [mask_dict(i) if isinstance(i, (dict, list)) else i for i in d]
                        return d
                    sanitized = json.dumps(mask_dict(data), indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    sanitized = self._sanitize_text(content)
            elif src_path.endswith('.plist'):
                sanitized = re.sub(
                    r'(<key>[^<]*(_KEY|API_KEY)[^<]*</key>\s*<string>)([^<]*)(</string>)',
                    r'\1YOUR_TOKEN_HERE\4',
                    content, flags=re.IGNORECASE
                )
            else:
                sanitized = self._sanitize_text(content)

            with open(dst_path, 'w', encoding='utf-8') as f:
                f.write(sanitized)
            return True
        except Exception as e:
            print(f"🚨 SECURITY CRITICAL ERROR: Failed to sanitize {src_path}: {e}")
            return False

    def _sanitize_text(self, content):
        lines = content.splitlines()
        sanitized_lines = []
        secret_pattern = re.compile(r'(_KEY|API_KEY|TOKEN|SECRET)', re.IGNORECASE)
        for line in lines:
            if "=" in line and secret_pattern.search(line.split("=")[0]):
                key = line.split("=")[0]
                sanitized_lines.append(f"{key}=YOUR_TOKEN_HERE")
            else:
                sanitized_lines.append(line)
        return "\n".join(sanitized_lines)

    def estimate_size(self, mode="core"):
        total_bytes = 0
        target_keys = self.modes.get(mode, self.modes["core"])
        for key in target_keys:
            paths = self.targets.get(key)
            if not paths: continue
            if key == "lockfiles":
                for lock in self._get_all_lockfiles():
                    if os.path.exists(lock): total_bytes += os.path.getsize(lock)
            elif isinstance(paths, list):
                for path in paths:
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            is_browser = (key == "browser_profile")
                            for root, dirs, files in os.walk(path):
                                root_lower = root.lower()
                                # 系統排除
                                if any(ex in root_lower.split(os.sep) for ex in self.exclusions): continue
                                # 瀏覽器去脂排除
                                if is_browser:
                                    rel_root = os.path.relpath(root, path)
                                    if any(ex in rel_root.split(os.sep) for ex in self.browser_fat_exclusions): continue
                                
                                for f in files:
                                    f_lower = f.lower()
                                    if any(ex == f_lower for ex in self.exclusions) or f_lower.startswith(("tmp", "temp")): continue
                                    total_bytes += os.path.getsize(os.path.join(root, f))
                        else:
                            total_bytes += os.path.getsize(path)
        
        # 壓縮率預估調整 (瀏覽器去脂後，剩餘多為 SQL 檔，壓縮率較低)
        estimated_compressed = int(total_bytes * 0.75)
        chunk_size = 50 * 1024 * 1024 
        num_chunks = math.ceil(estimated_compressed / chunk_size)
        return {
            "raw_size": total_bytes,
            "compressed_size": estimated_compressed,
            "num_chunks": num_chunks,
            "chunk_size_limit": chunk_size
        }

    def pack(self, mode="core"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "soul_core" if mode == "core" else "soul_full"
        folder_name = f"{prefix}_{timestamp}"
        target_dir = os.path.join(self.backup_root, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        archive_name = f"{folder_name}.tar.gz"
        archive_path = os.path.join(target_dir, archive_name)
        staging_dir = os.path.join(target_dir, "staging")
        os.makedirs(staging_dir, exist_ok=True)

        manifest = {
            "version": "1.2.0",
            "timestamp": timestamp,
            "mode": mode,
            "files": {},
            "chunks": []
        }

        try:
            target_keys = self.modes.get(mode, self.modes["core"])
            for key in target_keys:
                paths = self.targets.get(key)
                if not paths: continue
                targets = self._get_all_lockfiles() if key == "lockfiles" else (paths if isinstance(paths, list) else [])
                
                for path in targets:
                    if os.path.exists(path):
                        rel_path = os.path.basename(path)
                        dest = os.path.join(staging_dir, rel_path)
                        if os.path.isdir(path):
                            is_browser = (key == "browser_profile")
                            self._smart_copy(path, dest, is_browser=is_browser)
                        elif any(x in path for x in ["config", ".env", ".json", ".plist"]):
                            if not self._sanitize_secrets(path, dest): continue
                        else:
                            shutil.copy2(path, dest)

            # Create the main archive
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(staging_dir, arcname=".")
            
            manifest["main_archive"] = {
                "name": archive_name,
                "sha256": self._calculate_sha256(archive_path)
            }

            # Split into chunks if needed (GitHub logic)
            if os.path.getsize(archive_path) > 100 * 1024 * 1024:
                chunks = self.chunk_archive(archive_path, target_dir)
                for c in chunks:
                    manifest["chunks"].append({
                        "name": os.path.basename(c),
                        "sha256": self._calculate_sha256(c)
                    })
            
            # Save manifest
            with open(os.path.join(target_dir, "backup_manifest.json"), "w") as f:
                json.dump(manifest, f, indent=2)
            
            return target_dir
        finally:
            if os.path.exists(staging_dir):
                self._rmtree_robust(staging_dir)

    def _rmtree_robust(self, path):
        """
        [不朽級清理] 強制解鎖並刪除目錄，解決 macOS uchg 導致的 PermissionError。
        """
        def handle_error(func, path, exc_info):
            # 1. [FIX] 優先解除 macOS 不可變標籤 (否則 chmod 會報錯)
            subprocess.run(["chflags", "nouchg", path], capture_output=True)
            # 2. 嘗試物理改權
            try:
                os.chmod(path, 0o777)
            except Exception:
                pass
            # 3. 再次嘗試原定的刪除動作
            try:
                func(path)
            except Exception:
                pass

        if os.path.exists(path):
            shutil.rmtree(path, onerror=handle_error)

    def _smart_copy(self, src, dst, is_browser=False):
        """
        [正規軍嚴格模式] 逐檔搬運，確保靈魂數據 100% 完整，不容許任何遺漏。
        [v2.3.1-hotfix] 加入 uchg 防護：遇到 PermissionError 時自動解鎖後重試，
        最終仍失敗則跳過並印出警告，確保單一鎖定檔不崩潰整個備份進程。
        """
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(src):
                item_lower = item.lower()
                
                # 系統排除
                if item_lower in self.exclusions or item_lower.startswith(("tmp", "temp")): continue
                
                # 瀏覽器去脂排除
                if is_browser and item in self.browser_fat_exclusions: continue
                
                s, d = os.path.join(src, item), os.path.join(dst, item)
                self._smart_copy(s, d, is_browser=is_browser)
        else:
            # 確保父目錄存在後執行嚴格拷貝
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            # [v2.3.1-hotfix] uchg 防護：第一次嘗試 → 失敗則解鎖重試 → 最終失敗才跳過
            try:
                shutil.copy2(src, dst)
            except (PermissionError, OSError):
                try:
                    subprocess.run(["chflags", "nouchg", src], capture_output=True, check=False)
                    shutil.copy2(src, dst)
                except Exception as e2:
                    print(f"⚠️  [SmartCopy SKIP] Cannot copy {src}: {e2} (skipping, non-fatal)")

    def chunk_archive(self, archive_path, output_dir, chunk_size_mb=50):
        chunk_size = chunk_size_mb * 1024 * 1024
        chunks = []
        with open(archive_path, 'rb') as f:
            part_num = 1
            while True:
                chunk = f.read(chunk_size)
                if not chunk: break
                chunk_name = f"{os.path.basename(archive_path)}.part{part_num}.bin"
                chunk_path = os.path.join(output_dir, chunk_name)
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                
                chunks.append(chunk_path)
                part_num += 1
        return chunks
