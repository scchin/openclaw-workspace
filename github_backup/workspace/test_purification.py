import subprocess

def test_purification():
    # 定義包含 LaTeX 洩漏的測試文本 (使用 raw strings 以保留反斜槓)
    test_cases = [
        r"步驟 A $\rightarrow$ 步驟 B",
        r"邏輯流轉：$\rightarrow$ 物理執行 $\rightarrow$ 結案",
        r"這裡有一個 LaTeX 文本 $\text{重要內容}$ 以及箭頭 $\rightarrow$",
        r"複雜案例：$\Rightarrow$ 且包含孤立的 $ 符號",
        r"無 LaTeX 的文本 → 正常箭頭"
    ]
    
    print(f"{'Original':<40} | {'Purified':<40}")
    print("-" * 85)
    
    for case in test_cases:
        # 調用物理腳本
        result = subprocess.run(
            ["python3", "/Users/KS/.openclaw/workspace/purify_output.py", "--text", case],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        purified = result.stdout.strip()
        print(f"{case:<40} | {purified:<40}")

if __name__ == "__main__":
    test_purification()
