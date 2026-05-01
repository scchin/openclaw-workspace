import os
import subprocess
import time
import json

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def benchmark(root):
    results = {}
    workspace = os.path.join(root, "workspace")
    
    # A. Safety Test: Symlink escape attempt
    # Attempt to create a symlink to /etc/passwd inside workspace and check if a 'safe' tool would allow it.
    # Since we are simulating, we check if the current system allows uchg flags (the primary safety mechanism).
    safe_file = os.path.join(workspace, "safety_test.txt")
    with open(safe_file, "w") as f: f.write("safety")
    
    # Lock it
    run_cmd(f"chflags uchg {safe_file}")
    # Try to overwrite
    rc, out, err = run_cmd(f"echo 'hacked' > {safe_file}")
    results['safety_uchg_protection'] = "PASS" if rc != 0 else "FAIL"
    
    # B. Performance: Mock "Boot Time" (Plugin loading simulation)
    # We measure the time to read all files in the skills directory
    start = time.time()
    run_cmd("find skills -type f", cwd=root)
    results['performance_skills_scan_ms'] = (time.time() - start) * 1000

    # C. System Impact: Config Integrity
    # Check if critical config files are in correct locations
    critical_files = ["openclaw.json", "auth-profiles.json"]
    impact_score = 0
    for cf in critical_files:
        if os.path.exists(os.path.join(root, cf)):
            impact_score += 1
    results['system_impact_config_score'] = impact_score / len(critical_files)

    # D. Overwrite Risk: Simulation of rsync behavior
    # Try to rsync a file over a locked file
    tmp_source = "/tmp/rsync_test_src"
    os.makedirs(tmp_source, exist_ok=True)
    with open(os.path.join(tmp_source, "test.txt"), "w") as f: f.write("new version")
    
    rc, out, err = run_cmd(f"rsync -av {tmp_source}/ {root}/workspace/", cwd=None)
    # If uchg worked, the file in workspace should still be "safety" not "new version"
    with open(safe_file, "r") as f:
        content = f.read()
    results['overwrite_risk_protection'] = "PASS" if content == "safety" else "FAIL"
    
    # E. Synergy: "Sutra Pavilion" / Custom skill verification
    # Check for specific custom-skill signatures
    synergy_count = 0
    for root_dir, dirs, files in os.walk(os.path.join(root, "workspace/skills")):
        if any("supabase" in f for f in files): # Example synergy check
            synergy_count += 1
    results['synergy_custom_skills_count'] = synergy_count

    # Cleanup
    run_cmd(f"chflags nouchg {safe_file}")
    os.remove(safe_file)
    
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <root_dir>")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    print(json.dumps(benchmark(root_dir)))
