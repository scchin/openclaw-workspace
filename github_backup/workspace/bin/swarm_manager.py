import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

class SwarmManager:
    def __init__(self):
        self.base_dir = Path("~/.openclaw/workspace/swarm_env").expanduser()
        self.inbox_dir = self.base_dir / "inboxes"
        self.ledger_file = self.base_dir / "tasks.json"
        self.repo_root = Path("~/.openclaw/workspace").expanduser() # Assume main workspace is the git repo
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        if not self.ledger_file.exists():
            self._save_ledger({})

    def _save_ledger(self, data):
        with open(self.ledger_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_ledger(self):
        with open(self.ledger_file, 'r') as f:
            return json.load(f)

    def init_task(self, task_id, agents):
        print(f"🚀 Initializing Hybrid Swarm for task: {task_id}")
        
        ledger = self._load_ledger()
        ledger[task_id] = {
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING",
            "agents": {}
        }

        for agent in agents:
            # 1. Create Worktree
            worktree_path = self.base_dir / "worktrees" / f"{task_id}_{agent}"
            worktree_path.parent.mkdir(parents=True, exist_ok=True)
            
            # git worktree add <path> -b <branch>
            branch_name = f"swarm/{task_id}_{agent}"
            try:
                subprocess.run(
                    ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
                    cwd=self.repo_root, check=True, capture_output=True
                )
                print(f"✅ Created worktree for {agent} at {worktree_path}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Git worktree failed for {agent}: {e.stderr.decode()}")
                continue

            # 2. Create Inbox
            agent_inbox = self.inbox_dir / agent
            agent_inbox.mkdir(parents=True, exist_ok=True)
            
            # 3. Update Ledger
            ledger[task_id]["agents"][agent] = {
                "path": str(worktree_path),
                "status": "RUNNING",
                "branch": branch_name
            }

        self._save_ledger(ledger)
        print(f"✨ Task {task_id} infrastructure ready.")
        return ledger[task_id]

    def update_status(self, task_id, agent, status):
        ledger = self._load_ledger()
        if task_id in ledger and agent in ledger[task_id]["agents"]:
            ledger[task_id]["agents"][agent]["status"] = status
            self._save_ledger(ledger)
            print(f"📈 Status updated: {agent} -> {status}")
        else:
            print(f"❌ Task or Agent not found in ledger.")

    def finalize_task(self, task_id):
        print(f"🏁 Finalizing task: {task_id}")
        ledger = self._load_ledger()
        if task_id not in ledger: return
        
        # Merge all agent branches into main
        for agent, info in ledger[task_id]["agents"].items():
            branch = info["branch"]
            try:
                subprocess.run(["git", "checkout", "main"], cwd=self.repo_root, check=True, capture_output=True)
                subprocess.run(["git", "merge", branch], cwd=self.repo_root, check=True, capture_output=True)
                subprocess.run(["git", "branch", "-D", branch], cwd=self.repo_root, check=True, capture_output=True)
                
                # Remove worktree
                subprocess.run(["git", "worktree", "remove", "-f", info["path"]], cwd=self.repo_root, check=True, capture_output=True)
                print(f"✅ Merged and cleaned up {agent}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Conflict or error merging {agent}: {e.stderr.decode()}")

        ledger[task_id]["status"] = "COMPLETED"
        self._save_ledger(ledger)
        print(f"✨ Task {task_id} fully archived.")

if __name__ == "__main__":
    import sys
    manager = SwarmManager()
    if len(sys.argv) < 2:
        print("Usage: swarm_manager.py [init|update|finalize] [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "init":
        # init <task_id> <agent1,agent2...>
        manager.init_task(sys.argv[2], sys.argv[3].split(","))
    elif cmd == "update":
        # update <task_id> <agent> <status>
        manager.update_status(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "finalize":
        # finalize <task_id>
        manager.finalize_task(sys.argv[2])
