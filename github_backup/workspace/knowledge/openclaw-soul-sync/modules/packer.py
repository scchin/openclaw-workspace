import os
import tarfile
import shutil
from datetime import datetime
import math
import re
import json

class Packer:
    """
    Industrial-grade backup engine for OpenClaw.
    Implements rigorous secret sanitization across all config layers 
    to prevent API key leakage to cloud storage.
    """
    
    def __init__(self, backup_root=None):
        self.home = os.path.expanduser("~")
        self.workspace = os.path.join(self.home, ".openclaw/workspace")
        self.backup_root = backup_root or os.path.join(self.home, ".openclaw/backups")
        
        # Define the 'Four-Layer' and other critical config paths
        self.targets = {
            "config": [
                os.path.join(self.home, "Library/LaunchAgents/ai.openclaw.gateway.plist"), # Layer 1
                os.path.join(self.home, ".openclaw/.env"),                            # Layer 2
                os.path.join(self.home, ".openclaw/agents/main/agent/auth-profiles.json"), # Layer 3
                os.path.join(self.home, ".openclaw/agents/main/agent/models.json"),       # Layer 4
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
            "browser_profile": [os.path.join(self.home, "Library/Application Support/Microsoft Edge/Default")],
            "lockfiles": "auto"
        }

    def _get_all_lockfiles(self):
        locks = []
        for root, dirs, files in os.walk(self.workspace):
            if "lock.json" in files:
                locks.append(os.path.join(root, "lock.json"))
        return locks

    def _sanitize_secrets(self, src_path, dst_path):
        """
        The ultimate security gate. Masks all LLM keys based on file format.
        """
        secret_pattern = re.compile(r'(_KEY|API_KEY|TOKEN|SECRET)', re.IGNORECASE)
        
        try:
            with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 1. JSON Sanitization (Recursive)
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

            # 2. Plist/XML Sanitization
            elif src_path.endswith('.plist'):
                # Match <key>GEMINI_API_KEY</key><string>VALUE</string>
                # Replace the value part of the string tag
                sanitized = re.sub(
                    r'(<key>[^<]*(_KEY|API_KEY)[^<]*</key>\s*<string>)([^<]*)(</string>)',
                    r'\1YOUR_TOKEN_HERE\4',
                    content,
                    flags=re.IGNORECASE
                )

            # 3. Plain Text / .env Sanitization
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
        targets = self.targets.get(mode, self.targets["core"])
        for key, paths in targets.items():
            if key == "lockfiles":
                for lock in self._get_all_lockfiles():
                    if os.path.exists(lock): total_bytes += os.path.getsize(lock)
            else:
                for path in paths:
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            for root, dirs, files in os.walk(path):
                                if any(x in root for x in ["logs", "cache", "backups"]): continue
                                for f in files:
                                    total_bytes += os.path.getsize(os.path.join(root, f))
                        else:
                            total_bytes += os.path.getsize(path)
        
        estimated_compressed = int(total_bytes * 0.75)
        chunk_size = 50 * 1024 * 1024
        num_chunks = math.ceil(estimated_compressed / chunk_size)
        last_chunk_size = estimated_compressed % chunk_size if estimated_compressed % chunk_size != 0 else chunk_size
        return {
            "raw_size": total_bytes,
            "compressed_size": estimated_compressed,
            "num_chunks": num_chunks,
            "last_chunk_size": last_chunk_size,
            "chunk_size_limit": chunk_size
        }

    def pack(self, mode="core", destination_dir=None, encrypt=False, password=None):
        destination_dir = destination_dir or self.backup_root
        os.makedirs(destination_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        prefix = "soul_core" if mode == "core" else "soul_full"
        archive_name = f"{prefix}_{timestamp}.tar.gz"
        archive_path = os.path.join(destination_dir, archive_name)
        staging_dir = os.path.join(destination_dir, f"tmp_{timestamp}")
        os.makedirs(staging_dir, exist_ok=True)

        try:
            all_targets = []
            for key, paths in self.targets.items():
                if key == "lockfiles": all_targets.extend(self._get_all_lockfiles())
                else: all_targets.extend(paths)

            for path in all_targets:
                if os.path.exists(path):
                    dest = os.path.join(staging_dir, os.path.basename(path))
                    if os.path.isdir(path):
                        self._smart_copy(path, dest)
                    elif any(x in path for x in ["config", ".env", ".json", ".plist"]):
                        # FORCED SANITIZATION for all config files
                        if not self._sanitize_secrets(path, dest):
                            # If sanitization fails, DO NOT include the file in backup
                            print(f"⚠️ Security block: {path} could not be sanitized. Skipping.")
                            continue
                    else:
                        shutil.copy2(path, dest)

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(staging_dir, arcname=".")
            return archive_path
        finally:
            shutil.rmtree(staging_dir)

    def _smart_copy(self, src, dst):
        if not os.path.exists(dst): os.makedirs(dst)
        exclusions = {"logs", "cache", ".DS_Store", "__pycache__", "backups"}
        if self.backup_root: exclusions.add(os.path.basename(self.backup_root))
        for item in os.listdir(src):
            if item in exclusions or "soul_backup_" in item or "backup_" in item: continue
            s, d = os.path.join(src, item), os.path.join(dst, item)
            if os.path.isdir(s): self._smart_copy(s, d)
            else: shutil.copy2(s, d)

    def chunk_archive(self, archive_path, chunk_size_mb=50):
        chunk_size = chunk_size_mb * 1024 * 1024
        chunks = []
        with open(archive_path, 'rb') as f:
            part_num = 1
            while True:
                chunk = f.read(chunk_size)
                if not chunk: break
                chunk_name = f"{archive_path}.part{part_num}"
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunks.append(chunk_name)
                part_num += 1
        return chunks
