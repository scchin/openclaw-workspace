import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_hetero_test")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # 1. Seed 'Skills' Room (Technical, Precise)
    skills_dir = os.path.join(TEST_PALACE, "skills")
    os.makedirs(skills_dir, exist_ok=True)
    for i in range(50):
        with open(os.path.join(skills_dir, f"tech_{i}.txt"), "w") as f:
            f.write(f"Technical Spec {i}: The API_Call_{i} function implements a high-performance buffer. Mode: Synchronous.")

    # 2. Seed 'Memory' Room (Semantic, Emotional)
    memory_dir = os.path.join(TEST_PALACE, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    for i in range(50):
        with open(os.path.join(memory_dir, f"mem_{i}.txt"), "w") as f:
            f.write(f"Personal Memory {i}: I felt a strong sense of excitement when I first saw the buffer implementation in the code.")

    # Mine everything
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {TEST_PALACE}")

def benchmark():
    # The "Conflict Query": Contains both Technical terms and Emotional terms
    query = "The excitement of the high-performance buffer implementation"
    
    # --- Strategy A: Global Search (Uniform Indexing / No Isolation) ---
    global_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 10")
    
    # Count hits per room
    skills_hits_global = global_out.count("skills")
    memory_hits_global = global_out.count("memory")
    
    # --- Strategy B: Scoped Search (Heterogeneous-like Isolation) ---
    # Scenario: User wants the technical spec.
    skills_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --wing .mempalace_hetero_test --room skills --results 10")
    # Scenario: User wants the personal feeling.
    memory_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --wing .mempalace_hetero_test --room memory --results 10")
    
    skills_hits_scoped = skills_out.count("skills")
    memory_hits_scoped = memory_out.count("memory")
    
    return {
        "global": {"skills": skills_hits_global, "memory": memory_hits_global},
        "scoped": {"skills": skills_hits_scoped, "memory": memory_hits_scoped},
        "global_out": global_out,
        "skills_out": skills_out,
        "memory_out": memory_out
    }

if __name__ == "__main__":
    setup()
    results = benchmark()
    print(f"Global Search Results: Skills={results['global']['skills']}, Memory={results['global']['memory']}")
    print(f"Scoped Search Results: Skills={results['scoped']['skills']}, Memory={results['scoped']['memory']}")
    print("\nGlobal Output:\n", results['global_out'])
    print("\nScoped Skills Output:\n", results['skills_out'])
    print("\nScoped Memory Output:\n", results['memory_out'])
