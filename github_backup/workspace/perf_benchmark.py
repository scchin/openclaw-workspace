import os
import time
import subprocess
import numpy as np

def measure_load_time(module_path):
    # Use a small node script to measure the time it takes to require a module
    # We use a specific path to bypass normal resolution and test the 'direct' vs 'nested' speed
    cmd = f"node -e \"console.time('load'); require('{module_path}'); console.timeEnd('load');\""
    start = time.perf_counter()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end = time.perf_counter()
    return (end - start) * 1000 # Convert to ms

# Define paths
# Experimental: Bundled path (New Structure)
bundled_path = "/Users/KS/.openclaw/repo/dist-runtime/extensions/openai/node_modules/openai/index.js"
# Control: Deeply nested path (Simulating old monolithic resolution overhead)
nested_dir = "/tmp/perf_test/deep/nested/path/node_modules"
os.makedirs(nested_dir, exist_ok=True)
# Copy openai to the nested path for a fair comparison of the same file
subprocess.run(f"cp -R /Users/KS/.openclaw/repo/dist-runtime/extensions/openai/node_modules/openai {nested_dir}/", shell=True)
nested_path = f"{nested_dir}/openai/index.js"

trials = 20
bundled_results = []
nested_results = []

print(f"Running {trials} trials for each structure...")
for i in range(trials):
    bundled_results.append(measure_load_time(bundled_path))
    nested_results.append(measure_load_time(nested_path))

def analyze(data):
    return {
        "mean": np.mean(data),
        "std": np.std(data),
        "p95": np.percentile(data, 95)
    }

print("\n--- FINAL STATISTICAL DATA ---")
print(f"Bundled (New): {analyze(bundled_results)}")
print(f"Nested (Old):  {analyze(nested_results)}")
