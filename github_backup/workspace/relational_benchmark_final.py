import subprocess
import os

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

# 1. Seed a specific relational test set into the main palace
# We use a unique prefix to avoid pollution and make it easy to find.
test_prefix = "BENCH_V5_REL_"
facts = [
    (f"{test_prefix}Project", "Project Omega-X is a quantum comms project."),
    (f"{test_prefix}Component", "Omega-X uses Quantum-Core for signal processing."),
    (f"{test_prefix}Lead", "Dr. Aris was the lead of Quantum-Core until April 10."),
    (f"{test_prefix}Current", "Sarah took over Quantum-Core on April 10."),
    (f"{test_prefix}Dependency", "Quantum-Core depends on Tachyon-Lib."),
    (f"{test_prefix}LibMaintainer", "Sarah maintains Tachyon-Lib."),
]

print("Seeding relational data...")
for prefix, text in facts:
    # We mine these as individual files
    filename = f"/tmp/{prefix}.txt"
    with open(filename, "w") as f:
        f.write(text)
    run_cmd(f"/Users/KS/.local/bin/mempalace mine {filename}")

# 2. Test Scenarios
query = "Who is currently maintaining the Quantum-Core of Omega-X?"

# Scenario A: Naive Single-Hop Search (Linear/Standard)
# Just search the query directly.
naive_out = run_cmd(f"/Users/KS/.local/bin/mempalace search '{query}' --results 5")

# Scenario B: Relational Multi-Hop Search (v5 Proposed)
# Step 1: Find the component "Quantum-Core"
step1 = run_cmd(f"/Users/KS/.local/bin/mempalace search 'Quantum-Core' --results 3")
# Step 2: Using the knowledge that Quantum-Core is the target, search for its "lead" or "maintainer"
step2 = run_cmd(f"/Users/KS/.local/bin/mempalace search 'Quantum-Core lead maintainer' --results 3")

print("\n--- Results ---")
print(f"Naive Search Output:\n{naive_out}\n")
print(f"Relational Step 1 (Entity) Output:\n{step1}\n")
print(f"Relational Step 2 (Relation) Output:\n{step2}\n")

# Evaluation
naive_hit = "Sarah" in naive_out
relational_hit = "Sarah" in step2

print(f"\nNaive Hit: {naive_hit}")
print(f"Relational Hit: {relational_hit}")
