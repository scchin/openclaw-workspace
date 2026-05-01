import time
import re
import os
import json
from output_sanitizer import sanitize_text

def test_performance(size_mb=1):
    print(f"--- Testing Performance (Text Size: {size_mb}MB) ---")
    text = "This is a test. " * (size_mb * 1024 * 1024 // 20) 
    start = time.time()
    sanitize_text(text)
    end = time.time()
    print(f"Time taken: {end - start:.4f}s")

def test_nesting():
    print("\n--- Testing Deep Nesting (\\text) ---")
    # 10 levels (should be cleaned)
    text_10 = "\\text{L1\\text{L2\\text{L3\\text{L4\\text{L5\\text{L6\\text{L7\\text{L8\\text{L9\\text{L10}}}}}}}}}}"
    # 20 levels (should be partially cleaned)
    text_20 = "\\text{" + "text{" * 19 + "Deep" + "}" * 19 + "}"
    
    print(f"10 levels result: {sanitize_text(text_10)}")
    print(f"20 levels result: {sanitize_text(text_20)}")

def test_malformed():
    print("\n--- Testing Malformed LaTeX ---")
    cases = [
        "Single dollar $ sign",
        "Unmatched open brace { content",
        "Unmatched close brace content }",
        "Interleaved dollars $ $ $",
        "Very long string of symbols: " + "\\" * 1000 + "text{...}",
    ]
    for i, case in enumerate(cases):
        print(f"Case {i}: {case} -> {sanitize_text(case)}")

def test_system_chars():
    print("\n--- Testing System Character Preservation ---")
    case = 'Path: /Users/KS/.openclaw/workspace, JSON: {"key": "value", "list": [1, 2, 3]}, Equation: $x=1$'
    result = sanitize_text(case)
    print(f"Original: {case}")
    print(f"Result:   {result}")
    # Check if JSON brackets survived
    if '"key": "value"' in result and '[1, 2, 3]' in result:
        print("SUCCESS: System characters preserved.")
    else:
        print("FAILURE: System characters stripped!")

def test_io_bottleneck():
    print("\n--- Testing I/O Bottleneck (Many blocks) ---")
    # Create 100 small LaTeX blocks
    text = "Block: $x=1$ " * 100
    start = time.time()
    sanitize_text(text)
    end = time.time()
    print(f"Time taken for 100 blocks: {end - start:.4f}s")

if __name__ == "__main__":
    # Ensure rules file exists to avoid errors during load_rules()
    rules_path = "/Users/KS/.openclaw/workspace/Sutra_Library/S-Swarm_Hybrid_System/intercept_rules.json"
    os.makedirs(os.path.dirname(rules_path), exist_ok=True)
    if not os.path.exists(rules_path):
        with open(rules_path, 'w') as f:
            json.dump({"latex_to_unicode": {"\\rightarrow": "→", "\\le": "≤"}}, f)

    test_performance(1)
    test_nesting()
    test_malformed()
    test_system_chars()
    test_io_bottleneck()
