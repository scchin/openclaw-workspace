import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_benchmark_v5_ext")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    # 1. Init Palace
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # 2. Seed Data (Relational)
    # We create a set of diaries/logs with timestamps to simulate a timeline
    facts = [
        ("2026-01-01", "Project Omega-X started. Goal: Quantum Communication."),
        ("2026-01-05", "Quantum-Core component initialized. Lead: Dr. Aris."),
        ("2026-01-10", "Quantum-Core depends on Tachyon-Lib. Maintained by Sarah."),
        ("2026-02-01", "Sarah updated Tachyon-Lib to v2.0."),
        ("2026-04-10", "Dr. Aris left the company. Sarah took over the lead of Quantum-Core."),
        ("2026-04-12", "Omega-X entered beta testing phase."),
        ("2026-04-15", "Tachyon-Lib reported a bug in the synchronization layer."),
        ("2026-04-16", "Sarah fixed the Tachyon-Lib bug."),
        ("2026-04-17", "General system update completed."),
    ]
    
    data_dir = os.path.join(TEST_PALACE, "data")
    os.makedirs(data_dir, exist_ok=True)
    for i, (date, text) in enumerate(facts):
        with open(os.path.join(data_dir, f"log_{i}.txt"), "w") as f:
            f.write(f"Date: {date}\n{text}")
            
    # Noise
    for i in range(50):
        with open(os.path.join(data_dir, f"noise_{i}.txt"), "w") as f:
            f.write(f"Random noise fact {i}: The weather in city {i} is sunny.")
            
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {data_dir}")

def test_linear_wakeup():
    # Simulate Linear Wake-up: get last 3 entries by filename/time
    # In a real scenario, this would be the last 3 entries in the diary.
    # Here we just simulate the result of a "tail -n 3" on the palace.
    # We assume the model gets the last 3 logs (April 15, 16, 17).
    context = "Log 2026-04-15: Tachyon-Lib reported a bug. Log 2026-04-16: Sarah fixed the bug. Log 2026-04-17: System update completed."
    query = "Who is currently maintaining the Quantum-Core of Omega-X?"
    # If the answer (Sarah took over on April 10) is not in the context, it's a miss.
    return "Sarah" in context

def test_relational_wakeup():
    # Simulate Relational Wake-up:
    # 1. Search for "Quantum-Core"
    # 2. Find the most recent state/maintainer from the graph or search results
    # For this test, we check if a graph-based search for "Quantum-Core" 
    # can retrieve the "Sarah took over" fact from April 10th.
    output = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search 'Quantum-Core maintainer' --results 5")
    return "Sarah" in output

if __name__ == "__main__":
    setup()
    linear_hit = test_linear_wakeup()
    relational_hit = test_relational_wakeup()
    print(f"Linear Wake-up Hit: {linear_hit}")
    print(f"Relational Wake-up Hit: {relational_hit}")
