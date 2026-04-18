import subprocess
import os
import shutil
import json

# Use a fresh directory for each run to avoid "already filed" issues
TEST_PALACE = os.path.expanduser("~/.mempalace_v5_benchmark")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip(), result.stderr.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    os.makedirs(TEST_PALACE, exist_ok=True)
    
    # Create test files inside the palace directory
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
    
    # Put targets in a subfolder to mine
    data_dir = os.path.join(TEST_PALACE, "data")
    os.makedirs(data_dir, exist_ok=True)
    for i, (doc, _) in enumerate(targets):
        with open(os.path.join(data_dir, f"target_{i}.txt"), "w") as f:
            f.write(doc)
            
    noise = [f"Random noise document number {i}" for i in range(40)]
    for i, doc in enumerate(noise):
        with open(os.path.join(data_dir, f"noise_{i}.txt"), "w") as f:
            f.write(doc)

    # Initialize palace
    # Use --yes to avoid interactive prompt
    out, err = run_cmd(f"/Users/KS/.local/bin/mempalace init --yes {TEST_PALACE}")
    
    # Mine the data directory
    out, err = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {data_dir}")
    print(f"Mine output: {out}")
    print(f"Mine error: {err}")

def test_r10():
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
    
    hits = 0
    for doc, query in targets:
        out, err = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 10")
        if doc in out:
            hits += 1
            
    return hits / len(targets)

if __name__ == "__main__":
    setup()
    r10 = test_r10()
    print(f"R@10: {r10}")
