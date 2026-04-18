import subprocess
import os
import shutil

TEST_PALACE = os.path.expanduser("~/.mempalace_test")

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def setup():
    if os.path.exists(TEST_PALACE):
        shutil.rmtree(TEST_PALACE)
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} init")

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
    
    noise = [f"Random noise document number {i}" for i in range(40)]
    
    for doc, _ in targets:
        with open("temp_doc.txt", "w") as f:
            f.write(doc)
        run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine temp_doc.txt")

    for doc in noise:
        with open("temp_doc.txt", "w") as f:
            f.write(doc)
        run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine temp_doc.txt")
    
    if os.path.exists("temp_doc.txt"):
        os.remove("temp_doc.txt")

    hits = 0
    for doc, query in targets:
        output = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search '{query}' --results 10")
        if doc in output:
            hits += 1
            
    return hits / len(targets)

if __name__ == "__main__":
    setup()
    r10 = test_r10()
    print(f"R@10: {r10}")
