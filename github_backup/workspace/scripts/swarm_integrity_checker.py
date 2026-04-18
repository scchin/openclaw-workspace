import argparse
import os
import sys

WORKSPACE = "/Users/KS/.openclaw/workspace"
TEMP_ROOT = os.path.join(WORKSPACE, "sources", "swarm_temp")

def check_isolation(task_id, file_path):
    # Normalize paths
    abs_file_path = os.path.abspath(file_path)
    task_dir = os.path.abspath(os.path.join(TEMP_ROOT, task_id))
    
    if not abs_file_path.startswith(task_dir):
        return False, f"CRITICAL VIOLATION: File {abs_file_path} is outside the task directory {task_dir}."
    
    # Check if it's in a sub-directory designated for an agent
    # Correct path: swarm_temp/[task_id]/agent_[agent_id]/...
    relative_path = os.path.relpath(abs_file_path, task_dir)
    path_parts = relative_path.split(os.sep)
    
    if len(path_parts) < 2:
        return False, f"CRITICAL VIOLATION: File {abs_file_path} is in the task root. Direct shared writes are forbidden."
    
    if not path_parts[0].startswith("agent_"):
        return False, f"CRITICAL VIOLATION: File {abs_file_path} is not within an agent-specific isolation folder (expected 'agent_*')."
    
    return True, "ISOLATION VERIFIED: Write path is valid."

def main():
    parser = argparse.ArgumentParser(description="Swarm Integrity Checker - Behavioral Interception Tool")
    parser.add_argument("--id", required=True, help="Swarm Task ID")
    parser.add_argument("--path", required=True, help="Target file path to verify")
    
    args = parser.parse_args()
    
    success, message = check_isolation(args.id, args.path)
    print(message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
