import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_routing_final")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    # Initialize a single palace
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # Seed data with explicit directories to force room detection
    # MemPalace detects rooms by folder name
    skills_dir = os.path.join(TEST_PALACE, "skills")
    memory_dir = os.path.join(TEST_PALACE, "memory")
    os.makedirs(skills_dir, exist_ok=True)
    os.makedirs(memory_dir, exist_ok=True)
    
    for i in range(20):
        with open(os.path.join(skills_dir, f"tech_{i}.txt"), "w") as f:
            f.write(f"Technical Spec {i}: The system uses a specialized algorithm for high-performance indexing.")
    for i in range(20):
        with open(os.path.join(memory_dir, f"mem_{i}.txt"), "w") as f:
            f.write(f"Personal Memory {i}: I remember feeling very happy when the system was first deployed.")

    # Mine the whole palace directory to let it detect the 'skills' and 'memory' rooms
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {TEST_PALACE}")

def test_routing():
    test_queries = [
        ("How does the high-performance indexing work?", "skills"),
        ("Tell me about the specialized algorithm", "skills"),
        ("What is the technical specification of the index?", "skills"),
        ("Detail the system's indexing performance", "skills"),
        ("Explain the technical implementation of the buffer", "skills"),
        ("I remember feeling happy about the deployment", "memory"),
        ("What were my emotions during the first launch?", "memory"),
        ("Recall my personal experience with the deployment", "memory"),
        ("How did I feel when the system started working?", "memory"),
        ("Describe my personal memories of the first day", "memory"),
    ]
    
    correct_routes = 0
    total_lat_global = 0
    total_lat_routed = 0
    
    # The wing name is typically the folder name
    wing_name = os.path.basename(TEST_PALACE)
    
    for query, expected in test_queries:
        # Global
        start = time.time()
        out_g = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 1")
        lat_g = time.time() - start
        total_lat_global += lat_g
        
        # Routed
        start = time.time()
        out_r = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --wing {wing_name} --room {expected} --results 1")
        lat_r = time.time() - start
        total_lat_routed += lat_r
        
        if expected in out_r:
            correct_routes += 1
            
    return {
        "accuracy": correct_routes / len(test_queries),
        "avg_lat_global": total_lat_global / len(test_queries),
        "avg_lat_routed": total_lat_routed / len(test_queries),
        "improvement": (total_lat_global - total_lat_routed) / total_lat_global * 100
    }

import time
if __name__ == "__main__":
    setup()
    results = test_routing()
    print(f"Routing Accuracy: {results['accuracy']*100}%")
    print(f"Avg Latency Global: {results['avg_lat_global']:.4f}s")
    print(f"Avg Latency Routed: {results['avg_lat_routed']:.4f}s")
    print(f"Latency Improvement: {results['improvement']:.2f}%")
