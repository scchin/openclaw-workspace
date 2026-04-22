import argparse
import os
import shutil
import uuid
import json
import subprocess
from datetime import datetime

WORKSPACE = "/Users/KS/.openclaw/workspace"
TEMP_ROOT = os.path.join(WORKSPACE, "sources", "swarm_temp")
MANAGER_SCRIPT = "/Users/KS/.openclaw/skills/system-task-manager/scripts/manager.py"

def ensure_temp_root():
    if not os.path.exists(TEMP_ROOT):
        os.makedirs(TEMP_ROOT, exist_ok=True)

def run_manager(action, *args):
    try:
        cmd = ["python3", MANAGER_SCRIPT, action] + list(args)
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Manager Error: {e.stderr}")
        return False

def init_swarm(task_name, session_key="main"):
    ensure_temp_root()
    task_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_name.replace(' ', '_').lower()}"
    task_dir = os.path.join(TEMP_ROOT, task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    # Create tiered memory rooms for the swarm
    os.makedirs(os.path.join(task_dir, "transient"), exist_ok=True)
    os.makedirs(os.path.join(task_dir, "distilled"), exist_ok=True)
    
    # Bind with system-task-manager
    if run_manager("register", task_id, f"swarm-governor:{task_name}", session_key):
        print(f"LOG: Task {task_id} registered in system-task-manager.")
    
    # Create metadata for the swarm
    meta = {
        "task_id": task_id,
        "task_name": task_name,
        "created_at": datetime.now().isoformat(),
        "status": "ACTIVE",
        "agents": {}
    }
    with open(os.path.join(task_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    
    return task_id, task_dir

def dispatch_swarm(task_id, agent_id, role):
    task_dir = os.path.join(TEMP_ROOT, task_id)
    if not os.path.exists(task_dir):
        return f"Error: Task ID {task_id} not found."
    
    # Create specific isolation paths for this agent (Tiered Memory)
    agent_root = os.path.join(task_dir, f"agent_{agent_id}")
    transient_dir = os.path.join(agent_root, "transient")
    distilled_dir = os.path.join(agent_root, "distilled")
    
    os.makedirs(transient_dir, exist_ok=True)
    os.makedirs(distilled_dir, exist_ok=True)
    
    # Define target files
    transient_file = os.path.join(transient_dir, "process.md")
    distilled_file = os.path.join(distilled_dir, "conclusion.md")
    
    with open(transient_file, "w") as f:
        f.write(f"# Process Log for {role}\n\nStarted at {datetime.now().isoformat()}\n")
    with open(distilled_file, "w") as f:
        f.write(f"# Distilled Conclusion for {role}\n\n(Awaiting distilled insights...)\n")
    
    # Update meta with tiered paths
    with open(os.path.join(task_dir, "meta.json"), "r+") as f:
        meta = json.load(f)
        meta["agents"][agent_id] = {
            "role": role, 
            "transient_path": transient_file,
            "distilled_path": distilled_file
        }
        f.seek(0)
        json.dump(meta, f, indent=2)
        f.truncate()
    
    return f"Agent {agent_id} dispatched. Transient: {transient_file} | Distilled: {distilled_file}"

def finalize_swarm(task_id, output_path):
    task_dir = os.path.join(TEMP_ROOT, task_id)
    if not os.path.exists(task_dir):
        return f"Error: Task ID {task_id} not found."
    
    with open(os.path.join(task_dir, "meta.json"), "r") as f:
        meta = json.load(f)
    
    # Synthesize results - ONLY read from distilled paths (Physical Noise Block)
    synthesis = f"# Swarm Synthesis: {meta['task_name']}\n\n"
    for agent_id, info in meta["agents"].items():
        path = info.get("distilled_path")
        if path and os.path.exists(path):
            with open(path, "r") as rf:
                synthesis += f"## Pure Perspective: {info['role']}\n\n{rf.read()}\n\n---\n\n"
        else:
            synthesis += f"## Perspective: {info['role']}\n\n(No distilled conclusion recorded)\n\n---\n\n"
    
    # Write to final destination
    with open(output_path, "w") as f:
        f.write(synthesis)
    
    # Clear from system-task-manager
    if run_manager("clear", task_id):
        print(f"LOG: Task {task_id} cleared from system-task-manager.")
    
    # Physical Purge (Destroy all transient and distilled data)
    shutil.rmtree(task_dir)
    
    return f"Synthesis complete. Results written to {output_path}. Temporary tiered directories {task_dir} purged."

def main():
    parser = argparse.ArgumentParser(description="Swarm Governor - Multi-Agent Isolation Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # init_swarm
    init_p = subparsers.add_parser("init")
    init_p.add_argument("--name", required=True, help="Task name")
    init_p.add_argument("--session", default="main", help="Session key for task manager")
    
    # dispatch_swarm
    disp_p = subparsers.add_parser("dispatch")
    disp_p.add_argument("--id", required=True, help="Task ID")
    disp_p.add_argument("--agent", required=True, help="Agent ID")
    disp_p.add_argument("--role", required=True, help="Role/Perspective")
    
    # finalize_swarm
    final_p = subparsers.add_parser("finalize")
    final_p.add_argument("--id", required=True, help="Task ID")
    final_p.add_argument("--out", required=True, help="Final output path")
    
    args = parser.parse_args()
    
    if args.command == "init":
        tid, tdir = init_swarm(args.name, args.session)
        print(f"TASK_ID:{tid}\nDIR:{tdir}")
    elif args.command == "dispatch":
        print(dispatch_swarm(args.id, args.agent, args.role))
    elif args.command == "finalize":
        print(finalize_swarm(args.id, args.out))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
