import os
import re
import json

class SystemAuditor:
    """
    Scans the local environment to determine the system state, 
    auth status, and available backups without user intervention.
    """
    
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.config_path = os.path.join(self.home, ".openclaw/openclaw.json")
        self.env_path = os.path.join(self.home, ".openclaw/.env")
        self.backup_root = os.path.join(self.home, ".openclaw/backups")

    def scan(self):
        """
        Performs a full system audit.
        """
        state = {
            "is_new_install": True,
            "auth_ready": False,
            "has_local_backups": False,
            "backup_list": [],
            "current_user": os.getlogin(),
            "system_paths": {
                "openclaw_root": os.path.join(self.home, ".openclaw"),
                "workspace": os.path.join(self.home, ".openclaw/workspace")
            }
        }

        # 1. Check if it's a previously backed-up system
        if os.path.exists(self.config_path) and os.path.exists(self.backup_root):
            state["is_new_install"] = False

        # 2. Check Auth Status
        if os.path.exists(self.env_path):
            with open(self.env_path, 'r') as f:
                content = f.read()
                if "GITHUB_TOKEN" in content:
                    state["auth_ready"] = True

        # 3. Scan Local Backups
        if os.path.exists(self.backup_root):
            backups = [f for f in os.listdir(self.backup_root) if "soul_backup_" in f]
            if backups:
                state["has_local_backups"] = True
                state["backup_list"] = sorted(backups, reverse=True)

        return state
