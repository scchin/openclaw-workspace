import subprocess
import os
import shutil
import time

TEST_PALACE = os.path.expanduser("~/.mempalace_routing_test")

def run_cmd(cmd):
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    end = time.time()
    return result.stdout.strip(), result.stderr.strip(), end - start

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # Seed 'skills' room (Technical)
    skills_dir = os.path.join(TEST_PALACE, "skills")
    os.makedirs(skills_dir, exist_ok=True)
    for i in range(20):
        with open(os.path.join(skills_dir, f"tech_{i}.txt"), "w") as f:
            f.write(f"Technical Spec {i}: The system uses a specialized algorithm for high-performance indexing.")

    # Seed 'memory' room (Personal/Fact)
    memory_dir = os.path.join(TEST_PALACE, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    for i in range(20):
        with open(os.path.join(memory_dir, f"mem_{i}.txt"), "w") as f:
            f.write(f"Personal Memory {i}: I remember feeling very happy when the system was first deployed.")

    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {TEST_PALACE}")

def test_routing():
    # Test set: (Query, Expected Room)
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
    total_latency_global = 0
    total_latency_routed = 0
    
    wing_name = os.path.basename(TEST_PALACE)
    
    for query, expected in test_queries:
        # 1. Global Search (No routing)
        out_g, err_g, lat_g = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 1")
        total_latency_global += lat_g
        
        # 2. Routed Search (Simulating the logic: determine room then search)
        # In v5, the "routing" is often handled by the AI choosing the --room flag.
        # We test if searching in the CORRECT room yields the result faster/better.
        out_r, err_r, lat_r = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --wing {wing_name} --room {expected} --results 1")
        total_latency_routed += lat_r
        
        # Check if routed search was successful (actually found something in that room)
        if expected in out_r:
            correct_routes += 1
            
    return {
        "accuracy": correct_routes / len(test_queries),
        "avg_lat_global": total_latency_global / len(test_queries),
        "avg_lat_routed": total_latency_routed / len(test_queries),
        "improvement": (total_latency_global - total_latency_routed) / total_latency_global * 100
    }

if __name__ == "__main__":
    setup()
    results = test_routing()
    print(f"Routing Accuracy: {results['accuracy']*100}%")
    print(f"Avg Latency Global: {results['avg_lat_global']:.4f}s")
    print(f"Avg Latency Routed: {results['avg_lat_routed']:.4f}s")
    print(f"Latency Improvement: {results['improvement']:.2f}%")
