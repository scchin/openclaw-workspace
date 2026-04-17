import subprocess
import os

def run_test(text):
    print(f"Input: {text}")
    # 1. Run purification
    try:
        result = subprocess.run(
            ['python3', '/Users/KS/.openclaw/workspace/purify_output.py', '--text', text],
            capture_output=True, text=True, encoding='utf-8'
        )
        cleaned = result.stdout.strip()
        print(f"Cleaned: {cleaned}")
        
        # 2. Run guardrail
        audit = subprocess.run(
            ['python3', '/Users/KS/.openclaw/workspace/guardrail.py', '--text', cleaned],
            capture_output=True, text=True, encoding='utf-8'
        )
        status = audit.stdout.strip()
        print(f"Audit: {status}")
        return status == "CLEAN"
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    test_cases = [
        # Case 1: Mixed LaTeX and Unicode
        " la lteX $\rightarrow$ Unicode → 混合測試",
        # Case 2: Complex Nested text and symbols
        "複雜度 $\\approx$ 高 $\\downarrow$ 且 $\\text{結論是}\\Rightarrow$ 成功",
        # Case 3: Extreme leakage attempt
        "$\\alpha + \\beta \\approx \\gamma$ 且 $\\uparrow$ 趨勢",
        # Case 4: Pure text (Should stay clean)
        "這是一個完全正常的純文字句子，沒有任何符號。",
        # Case 5: Edge case with curly braces
        "測試 { 殘留括號 } 與 $\\rightarrow$ 符號",
    ]
    
    passed = 0
    for i, case in enumerate(test_cases):
        print(f"--- Test {i+1} ---")
        if run_test(case):
            passed += 1
        print("\n")
        
    print(f"Final Result: {passed}/{len(test_cases)} passed.")

if __name__ == "__main__":
    main()
