import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_hetero_test_v2")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    # 1. Init Palace first
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # 2. Create specific Room folders
    # MemPalace detects rooms from subfolder names
    skills_dir = os.path.join(TEST_PALACE, "skills")
    memory_dir = os.path.join(TEST_PALACE, "memory")
    os.makedirs(skills_dir, exist_ok=True)
    os.makedirs(memory_dir, exist_ok=True)
    
    # Seed 'Skills' Room
    for i in range(50):
        with open(os.path.join(skills_dir, f"tech_{i}.txt"), "w") as f:
            f.write(f"Technical Spec {i}: The API_Call_{i} function implements a high-performance buffer. Mode: Synchronous.")

    # Seed 'Memory' Room
    for i in range(50):
        with open(os.path.join(memory_dir, f"mem_{i}.txt"), "w") as f:
            f.write(f"Personal Memory {i}: I felt a strong sense of excitement when I first saw the buffer implementation in the code.")

    # Mine the palace (this should trigger room detection for 'skills' and 'memory')
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {TEST_PALACE}")

def benchmark():
    query = "The excitement of the high-performance buffer implementation"
    
    # --- Strategy A: Global Search ---
    global_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 10")
    
    # We count the source path to determine which room the result came from
    skills_hits = 0
    memory_hits = 0
    for line in global_out.split('\n'):
        if "/ skills" in line: skills_hits += 1
        if "/ memory" in line: memory_hits += 1
    
    # --- Strategy B: Scoped Search ---
    # Note: The wing name is the folder name of the palace
    wing_name = os.path.basename(TEST_PALACE)
    
    skills_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --wing {wing_name} --room skills --results 10")
    memory_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --wing {wing_name} --room memory --results 10")
    
    # Evaluation of scoped results
    # If we search 'skills', we should NOT see 'memory' results and vice versa.
    skills_pure = "memory" not in skills_out and "skills" in skills_out
    memory_pure = "skills" not in memory_out and "memory" in memory_out
    
    return {
        "global": {"skills": skills_hits, "memory": memory_hits},
        "scoped": {"skills_pure": skills_pure, "memory_pure": memory_pure},
        "global_out": global_out,
        "skills_out": skills_out,
        "memory_out": memory_out
    }

if __name__ == "__main__":
    setup()
    # Verify rooms first
    status = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} status")
    print(f"Palace Status:\n{status}\n")
    
    results = benchmark()
    print(f"Global Search: Skills={results['global']['skills']}, Memory={results['global']['memory']}")
    print(f"Scoped Purity: Skills={results['scoped']['skills_pure']}, Memory={results['scoped']['memory_pure']}")
    print("\nGlobal Output:\n", results['global_out'])
    print("\nScoped Skills Output:\n", results['skills_out'])
    print("\nScoped Memory Output:\n", results['memory_out'])
