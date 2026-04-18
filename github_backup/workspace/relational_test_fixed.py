import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_rel_test")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    # 1. Init Palace
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # 2. Seed Data
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
    
    # We must put files INSIDE the palace dir or a dir we mine
    data_dir = os.path.join(TEST_PALACE, "data")
    os.makedirs(data_dir, exist_ok=True)
    for i, (date, text) in enumerate(facts):
        with open(os.path.join(data_dir, f"log_{i}.txt"), "w") as f:
            f.write(f"Date: {date}\n{text}")
            
    # 3. Mine
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {data_dir}")

def test():
    # Scenario: "Who is currently maintaining the Quantum-Core of Omega-X?"
    
    # A. Linear Wake-up (Simulated: last 3 logs)
    # Log 6, 7, 8: (Tachyon bug, Sarah fix, System update)
    linear_context = "Log 6: Tachyon-Lib bug. Log 7: Sarah fixed it. Log 8: System update."
    linear_hit = "Sarah" in linear_context and "Quantum-Core" in linear_context # False
    
    # B. Relational Wake-up (Multi-hop search)
    # Hop 1: Find "Quantum-Core"
    hop1 = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search 'Quantum-Core' --results 5")
    # Hop 2: Find "lead" or "maintainer" related to results
    hop2 = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search 'Quantum-Core lead maintainer' --results 5")
    
    relational_hit = "Sarah" in hop2
    
    return linear_hit, relational_hit, hop2

if __name__ == "__main__":
    setup()
    l_hit, r_hit, r_out = test()
    print(f"Linear Hit: {l_hit}")
    print(f"Relational Hit: {r_hit}")
    print(f"Relational Output:\n{r_out}")
