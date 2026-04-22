import argparse
import re
import sys
import json
import os

RULES_PATH = "/Users/KS/.openclaw/workspace/Sutra_Library/S-Swarm_Hybrid_System/intercept_rules.json"

def load_rules():
    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get("latex_to_unicode", {})
    except Exception:
        return {}

def sanitize_latex_block(match):
    """處理被 $ 包圍的 LaTeX 塊內容"""
    content = match.group(1)
    replacements = load_rules()
    sorted_patterns = sorted(replacements.keys(), key=len, reverse=True)
    for pattern in sorted_patterns:
        clean_pattern = pattern.replace('\\\\', '\\')
        content = content.replace(clean_pattern, replacements[pattern])
    content = re.sub(r'\\([a-zA-Z]+)', ' ', content)
    content = content.replace('{', '').replace('}', '')
    return content

def sanitize_text(text):
    """
    Perform deterministic string replacement to eliminate LaTeX artifacts.
    This version is hardened against shell escaping and varied LaTeX styles.
    """
    if not text:
        return ""

    # 1. 物理級強效清除 \text{...} (處理空格, 嵌套, 及-raw-格式)
    # 使用迭代方式處理，直到沒有 \text{ 殘留
    # 匹配模式: \text 之後可能有空格，然後是 { ... }
    for _ in range(15): 
        new_text = re.sub(r'\\text\s*\{([^{}]*)\}', r'\1', text)
        if new_text == text:
            break
        text = new_text
    
    # 2. 處理雙美元符號塊 $$...$$
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: sanitize_latex_block(m), text, flags=re.DOTALL)
    
    # 3. 處理單美元符號塊 $...$
    text = re.sub(r'\$(.*?)\$', lambda m: sanitize_latex_block(m), text)
    
    # 4. 全域清理殘留的 raw LaTeX 符號 (例如 \rightarrow, \le 等)
    replacements = load_rules()
    sorted_patterns = sorted(replacements.keys(), key=len, reverse=True)
    for pattern in sorted_patterns:
        clean_pattern = pattern.replace('\\\\', '\\')
        text = text.replace(clean_pattern, replacements[pattern])
    
    # 5. 物理抹除所有剩餘的 \command 格式 (如 \mathbf, \textit, \text)
    # 使用更強力的正則匹配，確保所有 \字母 序列都被清除
    text = re.sub(r'\\([a-zA-Z]+)', ' ', text)
    
    # 6. 最後清理殘留的美元符號與特殊轉義符號
    text = text.replace('$', '')
    text = text.replace('\\%', '%')
    
    # 7. 清理多餘空格 (由 \command 替換產生)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Deterministic Output Sanitizer v2.3")
    parser.add_argument("--text", type=str, help="The text to sanitize")
    parser.add_argument("--file", type=str, help="Path to the file to sanitize")
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        input_text = args.text
    else:
        parser.print_help()
        sys.exit(1)
    
    result = sanitize_text(input_text)
    print(result)

if __name__ == "__main__":
    main()
