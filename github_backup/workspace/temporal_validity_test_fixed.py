import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_temporal_fixed")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    # CORRECT INIT FLOW
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    facts = [
        ("2026-01-01", "Company CEO State: Alice. Strategy: Market Expansion."),
        ("2026-02-15", "Company CEO State: Bob. Strategy: Product Pivot."),
        ("2026-03-10", "Company CEO State: Charlie. Strategy: Efficiency First."),
        ("2026-04-01", "Company CEO State: Diana. Strategy: Global Scaling."),
    ]
    
    data_dir = os.path.join(TEST_PALACE, "data")
    os.makedirs(data_dir, exist_ok=True)
    for i, (date, text) in enumerate(facts):
        with open(os.path.join(data_dir, f"state_{i}.txt"), "w") as f:
            f.write(f"Timestamp: {date}\n{text}")
            
    # Mine using the correct palace flag
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {data_dir}")

def test_temporal_retrieval():
    # Test 1: Current State
    current_query = "Current Company CEO State"
    current_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{current_query}' --results 5")
    
    # Test 2: Historical State
    history_query = "Company CEO State in January 2026"
    history_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{history_query}' --results 5")
    
    return current_out, history_out

if __name__ == "__main__":
    setup()
    c_out, h_out = test_temporal_retrieval()
    print(f"--- Current Query Output ---\n{c_out}")
    print(f"\n--- Historical Query Output ---\n{h_out}")
