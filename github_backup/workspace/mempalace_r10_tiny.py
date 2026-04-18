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
    os.makedirs(TEST_PALACE, exist_ok=True)
    run_cmd(f"/Users/KS/.local/bin/mempalace init {TEST_PALACE}")

def test_r10():
    targets = [("The quick brown fox jumps over the lazy dog", "brown fox jumps")]
    noise = ["Random noise document 1"]
    
    # We need files in the palace directory for 'mine' to work if we are mining the directory?
    # No, 'mine' usually takes a file or directory. 
    # Let's try putting files INSIDE the palace directory and mining the directory.
    
    target_file = os.path.join(TEST_PALACE, "target.txt")
    with open(target_file, "w") as f: f.write("The quick brown fox jumps over the lazy dog")
    
    noise_file = os.path.join(TEST_PALACE, "noise.txt")
    with open(noise_file, "w") as f: f.write("Random noise document 1")
    
    run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} mine {TEST_PALACE}")

    output = run_cmd(f"/Users/KS/.local/bin/mempalace --palace {TEST_PALACE} search 'brown fox jumps' --results 10")
    print(f"Output: {output}")
    return 1.0 if "quick brown fox" in output else 0.0

if __name__ == "__main__":
    setup()
    print(f"R@10: {test_r10()}")
