import subprocess
import os

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

# Unique prefix to avoid pollution in main palace
prefix = "V5_REL_TEST_2026"

facts = [
    (f"{prefix}_Project", "Project Omega-X is a quantum comms project."),
    (f"{prefix}_Component", "Omega-X uses Quantum-Core for signal processing."),
    (f"{prefix}_Lead", "Dr. Aris was the lead of Quantum-Core until April 10."),
    (f"{prefix}_Current", "Sarah took over Quantum-Core on April 10."),
    (f"{prefix}_Dependency", "Quantum-Core depends on Tachyon-Lib."),
    (f"{prefix}_LibMaintainer", "Sarah maintains Tachyon-Lib."),
]

print("Seeding relational data into main palace...")
for p, text in facts:
    filename = f"/tmp/{p}.txt"
    with open(filename, "w") as f:
        f.write(text)
    run_cmd(f"/Users/KS/.local/bin/mempalace mine {filename}")

# Testing
query = "Who is currently maintaining the Quantum-Core of Omega-X?"

# Scenario A: Linear Wake-up (Last 3 entries)
# We simulate this by just checking the most recent 3 seeded facts.
# The answer "Sarah took over" is in fact [3]. The last 3 are [6, 5, 4].
# Sarah is mentioned in [3] and [5]. 
# But for the a " Linear Wake-up" we usually just get the last N.
linear_context = " ".join([f[1] for f in facts[-3:]])
linear_hit = "Sarah" in linear_context and "Quantum-Core" in linear_context

# Scenario B: Relational Multi-hop (v5 Proposed)
# Hop 1: Find the component "Quantum-Core"
hop1 = run_cmd(f"/Users/KS/.local/bin/mempalace search 'Quantum-Core' --results 5")
# Hop 2: Find the maintainer
hop2 = run_cmd(f"/Users/KS/.local/bin/mempalace search 'Quantum-Core maintainer' --results 5")

relational_hit = "Sarah" in hop2

print("\n--- Final Benchmark Results ---")
print(f"Linear Wake-up Hit: {linear_hit}")
print(f"Relational Wake-up Hit: {relational_hit}")
print(f"Relational Output:\n{hop2}")
