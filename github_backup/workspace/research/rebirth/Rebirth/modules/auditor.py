import os
import json

class SystemAuditor:
    """
    Scans the local environment to determine the system state 
    based on the new 'Immortal' structural requirements.
    """
    
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.config_path = os.path.join(self.home, ".openclaw/openclaw.json")
        self.env_path = os.path.join(self.home, ".openclaw/.env")
        self.backup_root = os.path.join(self.home, ".openclaw/backups")

    def scan(self):
        state = {
            "is_new_install": True,
            "auth_ready": False,
            "has_local_backups": False,
            "backup_list": [],
            "current_user": os.environ.get("USER", "unknown"),
            "system_paths": {
                "openclaw_root": os.path.join(self.home, ".openclaw"),
                "workspace": os.path.join(self.home, ".openclaw/workspace")
            }
        }

        if os.path.exists(self.config_path):
            state["is_new_install"] = False

        if os.path.exists(self.env_path):
            with open(self.env_path, 'r') as f:
                if "GITHUB_TOKEN" in f.read():
                    state["auth_ready"] = True

        if os.path.exists(self.backup_root):
            # Scan for compliant subdirectories
            for entry in os.listdir(self.backup_root):
                full_path = os.path.join(self.backup_root, entry)
                if os.path.isdir(full_path) and (entry.startswith("soul_full") or entry.startswith("soul_core")):
                    # Check for manifest
                    if os.path.exists(os.path.join(full_path, "backup_manifest.json")):
                        state["backup_list"].append(entry)
            
            if state["backup_list"]:
                state["has_local_backups"] = True
                state["backup_list"].sort(reverse=True)

        return state
