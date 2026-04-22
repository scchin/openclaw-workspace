#!/usr/bin/env python3
import os
import subprocess
import shutil
import hashlib
import sys
from datetime import datetime
import json

# =============================================================================
# 🛡️ system-clone-local: Physical Clone Manager
# =============================================================================

DEFAULT_BACKUP_ROOT = os.path.expanduser("~/Documents/OpenClaw-Clone-Backup")
CONFIG_FILE = os.path.expanduser("~/.openclaw/system_clone_config.json")

# 物理封裝路徑清單 (絕對路徑)
TARGET_PATHS = [
    os.path.expanduser("~/.openclaw"),
    os.path.expanduser("~/.openclaw/workspace"),
    os.path.expanduser("~/.agents/skills"),
    "/opt/homebrew/lib/node_modules/openclaw",
    os.path.expanduser("~/Library/LaunchAgents") # Note: We'll filter for ai.openclaw.* inside the tar
]

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"backup_root": DEFAULT_BACKUP_ROOT}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clone(custom_name=None, custom_path=None):
    config = get_config()
    root = custom_path if custom_path else config["backup_root"]
    os.makedirs(root, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = custom_name if custom_name else "system_snapshot"
    filename = f"openclaw_clone_{timestamp}_{name}.tar.gz"
    full_path = os.path.join(root, filename)
    
    print(f"🚀 Starting 1:1 Physical Clone...")
    
    # 1. Stop Gateway
    print("Stopping Gateway for consistency...")
    run_cmd("openclaw gateway stop")
    
    try:
        # 2. Create Archive
        # Using -C / to store relative paths from root, avoiding absolute path warnings on macOS
        print("Packing paths relative to root...")
        paths_to_pack = " ".join([p.lstrip("/") for p in TARGET_PATHS])
        cmd = f"tar -C / -cpzf {full_path} {paths_to_pack}"
        success, output = run_cmd(cmd)
        
        if not success:
            raise Exception(f"Tar failed: {output}")
            
        # 3. Sign Archive
        checksum = get_sha256(full_path)
        manifest = {
            "filename": filename,
            "timestamp": timestamp,
            "sha256": checksum,
            "paths": TARGET_PATHS
        }
        with open(f"{full_path}.json", 'w') as f:
            json.dump(manifest, f, indent=4)
            
        print(f"✅ Clone completed successfully: {filename}")
        return True, full_path
    
    finally:
        # 4. Wake Gateway
        print("Restarting Gateway...")
        run_cmd("openclaw gateway start")

def list_backups(custom_path=None):
    config = get_config()
    root = custom_path if custom_path else config["backup_root"]
    if not os.path.exists(root):
        return []
    
    backups = []
    for f in os.listdir(root):
        if f.endswith(".tar.gz"):
            meta_path = os.path.join(root, f + ".json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as meta_f:
                    meta = json.load(meta_f)
                    backups.append({"filename": f, "timestamp": meta["timestamp"], "sha256": meta["sha256"]})
    
    return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

def restore(backup_filename, custom_path=None):
    config = get_config()
    root = custom_path if custom_path else config["backup_root"]
    full_path = os.path.join(root, backup_filename)
    
    if not os.path.exists(full_path):
        return False, "Backup file not found."
    
    # Verify Signature
    meta_path = full_path + ".json"
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            if get_sha256(full_path) != meta["sha256"]:
                return False, "SIGNATURE MISMATCH: Backup file is corrupted or tampered!"

    print(f"🚀 Starting 1:1 Physical Restore from {backup_filename}...")
    
    # 1. Stop Gateway
    run_cmd("openclaw gateway stop")
    
    try:
        # 2. Restore with absolute paths
        # -x: extract, -p: preserve permissions, -z: gzip, -f: file
        # -C / ensures absolute paths in tar are restored to root
        print("Restoring files to original positions...")
        cmd = f"tar -xpzf {full_path} -C /"
        success, output = run_cmd(cmd)
        
        if not success:
            raise Exception(f"Restore failed: {output}")
            
        print("✅ System restored to original state.")
        return True, "Success"
    
    finally:
        # 3. Wake Gateway
        run_cmd("openclaw gateway start")

if __name__ == "__main__":
    # Basic CLI for integration
    if len(sys.argv) < 2:
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == "clone":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        clone(name)
    elif mode == "list":
        print(json.dumps(list_backups()))
    elif mode == "restore":
        fname = sys.argv[2] if len(sys.argv) > 2 else None
        restore(fname)
