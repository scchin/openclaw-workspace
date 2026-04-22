import subprocess
import json
import os

def run_purification_and_audit(text):
    with open('temp_test_input.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    
    try:
        purify_res = subprocess.run(
            ['python3', '/Users/KS/.openclaw/workspace/purify_output.py', '--file', 'temp_test_input.txt'],
            capture_output=True, text=True, encoding='utf-8'
        )
        cleaned_text = purify_res.stdout.strip()
        
        audit_res = subprocess.run(
            ['python3', '/Users/KS/.openclaw/workspace/guardrail.py', '--text', cleaned_text],
            capture_output=True, text=True, encoding='utf-8'
        )
        audit_status = audit_res.stdout.strip()
        
        return {
            "input": text,
            "output": cleaned_text,
            "status": audit_status,
            "passed": audit_status == "CLEAN"
        }
    except Exception as e:
        return {"input": text, "output": f"Error: {str(e)}", "status": "ERROR", "passed": False}

def main():
    # Use raw strings r"..." to prevent unicodeescape errors
    test_cases = [
        r"測試 \rightarrow 和 \downarrow 與 \uparrow",
        r"混合 $\rightarrow$ 與 →，以及 $\approx$ 與 ≈",
        r"複雜度 $\approx$ 高 $\downarrow$ 且 \text{結論是}\Rightarrow 成功",
        r"公式 $\alpha + \beta \approx \gamma$",
        r"測試 { 殘留 } 符號與 $\rightarrow$ ",
        r"這是一個長句子，其中包含 \rightarrow 第一點，然後是 \downarrow 第二點，最後是 \approx 第三點，結論是 \text{完成}。",
        r"這是一個完全正常的句子，不應該被修改。",
        r"$\Leftarrow$ $\Leftrightarrow$ $\Rightarrow$ 組合測試",
    ]
    
    results = []
    for case in test_cases:
        results.append(run_purification_and_audit(case))
        
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
