import subprocess
import os
import shutil

# Use a fresh directory for v5 test
TEST_PALACE = os.path.expanduser("~/.mempalace_test_v5")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    # Use --yes to skip interactive prompts
    run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")

def test_r10():
    # 10 targets, 40 noise
    targets = [
        ("The quick brown fox jumps over the lazy dog", "brown fox jumps"),
        ("Quantum computing uses qubits for processing", "quantum computing qubits"),
        ("The Eiffel Tower is in Paris, France", "Eiffel Tower location"),
        ("Photosynthesis converts sunlight to energy", "photosynthesis energy"),
        ("The Great Wall of China is a massive fortification", "Great Wall China"),
        ("Python is a versatile programming language", "Python language"),
        ("The Mona Lisa was painted by Leonardo da Vinci", "Mona Lisa artist"),
        ("Water boils at 100 degrees Celsius", "water boiling point"),
        ("The capital of Japan is Tokyo", "capital of Japan"),
        ("Albert Einstein developed the theory of relativity", "Einstein relativity"),
    ]
    
    noise = [f"Random noise document number {i}" for i in range(40)]
    
    # Insert targets
    for doc, _ in targets:
        target_file = os.path.join(TEST_PALACE, f"target_{targets.index((doc, _))}.txt")
        with open(target_file, "w") as f:
            f.write(doc)
    
    # Insert noise
    for i, doc in enumerate(noise):
        noise_file = os.path.join(TEST_PALACE, f"noise_{i}.txt")
        with open(noise_file, "w") as f:
            f.write(doc)
            
    # Mine the whole directory
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {TEST_PALACE}")

    hits = 0
    for doc, query in targets:
        # Search top 10
        output = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 10")
        if doc in output:
            hits += 1
            
    return hits / len(targets)

if __name__ == "__main__":
    setup()
    r10 = test_r10()
    print(f"R@10: {r10}")
