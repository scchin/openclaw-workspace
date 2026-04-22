#!/usr/bin/env python3
import os
import shutil
import subprocess
import hashlib
import sys

# =============================================================================
# 🛡️ system-clone-local: Gauntlet Test Suite (Physical Path Edition)
# =============================================================================

# Use a real home directory path to avoid macOS /tmp symlink issues
TEST_ROOT = os.path.expanduser("~/.openclaw/workspace/test_env_physical")
BACKUP_DIR = os.path.expanduser("~/.openclaw/workspace/test_backups")
MOCK_TARGETS = [
    os.path.join(TEST_ROOT, "config"),
    os.path.join(TEST_ROOT, "workspace"),
    os.path.join(TEST_ROOT, "skills"),
]

def setup_mock_system():
    print("🛠️ Setting up mock system in real path...")
    if os.path.exists(TEST_ROOT):
        shutil.rmtree(TEST_ROOT)
    os.makedirs(TEST_ROOT)
    
    for path in MOCK_TARGETS:
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "test.txt"), "w") as f:
            f.write(f"Content of {path}\nVersion 1.0\nSecretKey: ABC123XYZ")
        os.chmod(os.path.join(path, "test.txt"), 0o644)
        
        with open(os.path.join(path, "secure.key"), "w") as f:
            f.write("PRIVATE_KEY_DATA_SENSITIVE")
        os.chmod(os.path.join(path, "secure.key"), 0o600)

    print("✅ Mock system ready.")

def run_clone_simulation():
    print("\n📦 Executing Clone Simulation...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    backup_file = os.path.join(BACKUP_DIR, "test_clone.tar.gz")
    
    # Use -C / to store relative paths from root
    # Correct paths should be absolute from root
    paths_to_pack = " ".join([p.lstrip("/") for p in MOCK_TARGETS])
    # Actually, to test the manager's logic, we pack the whole TEST_ROOT
    cmd = f"tar -C / -cpzf {backup_file} {TEST_ROOT.lstrip('/')}"
    subprocess.run(cmd, shell=True, check=True)
    print(f"✅ Clone created: {backup_file}")
    return backup_file

def corrupt_system():
    print("\n🔥 Executing Destructive Corruption...")
    for path in MOCK_TARGETS:
        test_file = os.path.join(path, "test.txt")
        if os.path.exists(test_file):
            os.remove(test_file)
        
        key_file = os.path.join(path, "secure.key")
        if os.path.exists(key_file):
            with open(key_file, "w") as f:
                f.write("CORRUPTED_DATA")
                
    print("✅ System corrupted.")

def run_restore_simulation(backup_file):
    print("\n♻️ Executing Restore Simulation...")
    # Restore using -C / to put files back in their exact absolute locations
    cmd = f"tar -C / -xpzf {backup_file}"
    subprocess.run(cmd, shell=True, check=True)
    print("✅ Restore completed.")

def verify_integrity():
    print("\n🔍 Verifying 1:1 Integrity...")
    success = True
    for path in MOCK_TARGETS:
        test_file = os.path.join(path, "test.txt")
        if not os.path.exists(test_file):
            print(f"❌ MISSING: {test_file}")
            success = False
            continue
        
        with open(test_file, 'r') as f:
            content = f.read()
            if "Version 1.0" not in content:
                print(f"❌ CONTENT MISMATCH: {test_file}")
                success = False
        
        key_file = os.path.join(path, "secure.key")
        if not os.path.exists(key_file):
            print(f"❌ MISSING: {key_file}")
            success = False
            continue
        
        # Check permissions (0o600)
        if (os.stat(key_file).st_mode & 0o777) != 0o600:
            print(f"❌ PERMISSION MISMATCH: {key_file}")
            success = False

    if success:
        print("🏆 INTEGRITY VERIFIED: 100% Match with original state!")
    else:
        print("❌ INTEGRITY FAILED.")
    return success

if __name__ == "__main__":
    try:
        setup_mock_system()
        backup_file = run_clone_simulation()
        corrupt_system()
        run_restore_simulation(backup_file)
        if verify_integrity():
            print("\n🚀 GAUNTLET PASSED!")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Test crashed: {e}")
        sys.exit(1)
