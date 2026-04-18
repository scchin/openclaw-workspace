import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_temporal_test")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # Seed a chronological series of state changes
    # We use a clear "State: [Value]" format to test retrieval
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
            
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {data_dir}")

def test_temporal_retrieval():
    # Scenario 1: Current State Query
    # "Who is the current CEO?"
    # A naive system might return all CEOs. A temporal system should prioritize the latest.
    current_query = "Current Company CEO State"
    current_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{current_query}' --results 5")
    
    # Scenario 2: Historical State Query
    # "Who was the CEO in January?"
    # This is the real test for Temporal Validity.
    history_query = "Company CEO State in January 2026"
    history_out = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{history_query}' --results 5")
    
    return {
        "current_out": current_out,
        "history_out": history_out,
        "current_hit": "Diana" in current_out and "Alice" not in current_out.split('\n')[0:10], # Simplified check
        "history_hit": "Alice" in history_out
    }

if __name__ == "__main__":
    setup()
    results = test_temporal_retrieval()
    print(f"Current State Hit: {results['current_hit']}")
    print(f"Historical State Hit: {results['history_hit']}")
    print("\n--- Current Query Output ---\n", results['current_out'])
    print("\n--- Historical Query Output ---\n", results['history_out'])
