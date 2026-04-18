import sys, json, os
from datetime import datetime

STATE_FILE = os.path.expanduser("~/.openclaw/runtime/active_tasks.json")

def load_tasks():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_tasks(tasks):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "list"
    tasks = load_tasks()

    if action == "register":
        tid, cmd, skey = sys.argv[2], sys.argv[3], sys.argv[4]
        tasks[tid] = {"command": cmd, "session": skey, "start": datetime.now().isoformat(), "status": "running"}
        save_tasks(tasks)
        print(f"Registered task {tid}")
    elif action == "update":
        tid, status = sys.argv[2], sys.argv[3]
        if tid in tasks:
            tasks[tid]["status"] = status
            save_tasks(tasks)
            print(f"Updated task {tid} to {status}")
    elif action == "clear":
        tid = sys.argv[2]
        if tid in tasks:
            del tasks[tid]
            save_tasks(tasks)
            print(f"Cleared task {tid}")
    elif action == "list":
        print(json.dumps(tasks, indent=2))

if __name__ == "__main__":
    main()
