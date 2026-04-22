import argparse
import json
import os
import subprocess
from datetime import datetime

# Constants
INTENSITY_LEVELS = {"LIGHT": 1, "STANDARD": 2, "STRICT": 3}
REGISTRY_PATH = "/Users/KS/.openclaw/workspace/system_health_registry.json"
SANITIZER_PATH = "/Users/KS/.openclaw/workspace/output_sanitizer.py"
PENDING_TASKS_PATH = "/Users/KS/.openclaw/workspace/pending_tasks.json"
SOUL_PATH = "/Users/KS/.openclaw/workspace/SOUL.md"
USER_PATH = "/Users/KS/.openclaw/workspace/USER.md"
GATEWAY_GUARD_PATH = "/Users/KS/.openclaw/workspace/bin/gateway_guardian.py"
SYSTEM_TASK_MANAGER_PATH = "/Users/KS/.openclaw/skills/system-task-manager/scripts/manager.py"

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def native_check_rec_pending_tasks():
    if not os.path.exists(PENDING_TASKS_PATH):
        return "WARN", "pending_tasks.json not found", ""
    try:
        with open(PENDING_TASKS_PATH, 'r') as f:
            data = json.load(f)
            # Assuming it's a list or a dict with tasks
            count = len(data) if isinstance(data, list) else 0
            return ("PASS" if count == 0 else "WARN"), f"Found {count} pending tasks.", str(data)
    except Exception as e:
        return "FAIL", f"Error reading pending_tasks.json: {str(e)}", ""

def native_check_ctx_persona_sync():
    checks = []
    for path in [SOUL_PATH, USER_PATH]:
        if os.path.exists(path) and os.access(path, os.R_OK):
            checks.append(f"{os.path.basename(path)}: OK")
        else:
            checks.append(f"{os.path.basename(path)}: MISSING/UNREADABLE")
    
    status = "PASS" if all("OK" in c for c in checks) else "FAIL"
    return status, " | ".join(checks), ""

def native_check_sys_process_sync():
    # Use absolute path to system-task-manager
    code, stdout, stderr = run_command(f"python3 {SYSTEM_TASK_MANAGER_PATH} list")
    if code == 0:
        return "PASS", "Process sync successful", stdout
    else:
        return "WARN", f"system-task-manager failed: {stderr.strip()}", stdout

def native_check_sec_gateway_guard():
    code, stdout, stderr = run_command(f"python3 {GATEWAY_GUARD_PATH}")
    if code == 0:
        return "PASS", "Gateway guardian active", stdout
    else:
        return "FAIL", f"Gateway guardian error: {stderr.strip()}", stdout

def main():
    parser = argparse.ArgumentParser(description="GURF System Health Check Engine")
    parser.add_argument("--intensity", choices=["LIGHT", "STANDARD", "STRICT"], default="STANDARD", help="Check intensity level")
    args = parser.parse_args()

    intensity_val = INTENSITY_LEVELS[args.intensity]

    # Load Registry
    if not os.path.exists(REGISTRY_PATH):
        print(f"Error: Registry not found at {REGISTRY_PATH}")
        return

    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)

    # Filter and Sort Modules
    modules = registry.get("modules", [])
    filtered_modules = [m for m in modules if INTENSITY_LEVELS.get(m["intensity"], 3) <= intensity_val]
    filtered_modules.sort(key=lambda x: x["priority"])

    results = []
    overall_status = "PASS"

    for mod in filtered_modules:
        mod_id = mod["id"]
        mod_type = mod["type"]
        
        if mod_type == "native":
            if mod_id == "rec_pending_tasks":
                status, msg, details = native_check_rec_pending_tasks()
            elif mod_id == "ctx_persona_sync":
                status, msg, details = native_check_ctx_persona_sync()
            elif mod_id == "sys_process_sync":
                status, msg, details = native_check_sys_process_sync()
            elif mod_id == "sec_gateway_guard":
                status, msg, details = native_check_sec_gateway_guard()
            else:
                status, msg, details = "FAIL", "Unknown native module", ""
        elif mod_type == "external":
            cmd = mod.get("command", "")
            code, stdout, stderr = run_command(cmd)
            status = "PASS" if code == 0 else "FAIL"
            msg = "External command executed" if code == 0 else f"External command failed: {stderr.strip()}"
            details = stdout if code == 0 else stderr
        else:
            status, msg, details = "FAIL", "Unknown module type", ""

        if status == "FAIL":
            overall_status = "FAIL"
        elif status == "WARN" and overall_status != "FAIL":
            overall_status = "WARN"

        results.append({
            "id": mod_id,
            "name": mod.get("name", ""),
            "status": status,
            "message": msg,
            "details": details
        })

    # Construct Status Card
    status_card = {
        "timestamp": datetime.now().isoformat(),
        "intensity": args.intensity,
        "overall_status": overall_status,
        "checks": results
    }

    # Save to temp file for sanitization
    temp_report_path = "/Users/KS/.openclaw/workspace/temp_health_report.json"
    with open(temp_report_path, 'w') as f:
        json.dump(status_card, f, indent=2)

    # Sanitize using output_sanitizer.py --file
    # We capture the output of the sanitizer
    sanitize_code, sanitize_stdout, sanitize_stderr = run_command(f"python3 {SANITIZER_PATH} --file {temp_report_path}")
    
    if sanitize_code == 0:
        print(sanitize_stdout)
    else:
        # Fallback to unsanitized if sanitizer fails, but we should probably report the error
        print(f"Sanitization failed: {sanitize_stderr}")
        print(json.dumps(status_card, indent=2))

if __name__ == "__main__":
    main()
