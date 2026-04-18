import argparse
import re
import sys

def scan_for_banned_symbols(text):
    # 禁用符號清單 (2026-04-17 更新版：禁代碼，許符號)
    banned_patterns = [
        r'\$',                 # 任何 $ 符號 (LaTeX 定界符) - 絕對禁止
        r'\\text',             # \text 標記 - 絕對禁止
        r'\\rightarrow',        # LaTeX 箭頭代碼 - 絕對禁止
        r'\\downarrow',        # LaTeX 箭頭代碼 - 絕對禁止
        r'\\uparrow',           # LaTeX 箭頭代碼 - 絕對禁止
        r'\\approx',           # LaTeX 近似代碼 - 絕對禁止
    ]
    
    for pattern in banned_patterns:
        if re.search(pattern, text):
            return False  # 發現禁項 (代碼污染)
            
    return True  # 完全乾淨 (僅含純文字或許可之 Unicode 符號)

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Output Guardrail")
    parser.add_argument("--text", type=str, required=True, help="The text to scan")
    args = parser.parse_args()
    
    if scan_for_banned_symbols(args.text):
        print("CLEAN")
        sys.exit(0)
    else:
        print("REJECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()
