import os
import sys
import subprocess
from pathlib import Path

# Ensure the skill directory is in the path
SKILL_PATH = "/Users/KS/.agents/skills/openclaw-soul-sync-1.0.0/"
sys.path.append(SKILL_PATH)

try:
    from soul_sync import SoulSyncOrchestrator
except ImportError as e:
    print(f"Failed to import SoulSyncOrchestrator: {e}")
    sys.exit(1)

def main():
    # 1. Get GitHub token and repo
    try:
        token = subprocess.check_output(["gh", "auth", "token"]).decode().strip()
        repo = "scchin/openclaw-soul-backups"
    except Exception as e:
        print(f"Failed to get GitHub token: {e}")
        sys.exit(1)

    # 2. Initialize Orchestrator
    orchestrator = SoulSyncOrchestrator()

    # 3. Execute Full Soul Backup to GitHub
    # This will handle estimation, chunking (<= 50MB), subdirectory isolation, and SHA-256 manifest.
    try:
        print("🚀 Initiating Mandated Full Soul Backup...")
        print("⏳ Estimating size (this may take a minute for large profiles)...")
        orchestrator.execute_backup(
            mode="full", 
            destination="github", 
            token=token, 
            repo=repo
        )
        print("✅ Mandated Backup Execution Successful.")
    except Exception as e:
        print(f"❌ Mandated Backup Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
