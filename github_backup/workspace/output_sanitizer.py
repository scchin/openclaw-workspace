import argparse
import re
import sys

def sanitize_latex_block(match):
    """處理被 $ 包圍的 LaTeX 塊內容"""
    content = match.group(1)
    
    # 符號映射表 (優先處理長符號)
    replacements = {
        r'\\longrightarrow': '→',
        r'\\rightarrow': '→',
        r'\\Rightarrow': '⇒',
        r'\\leftrightarrow': '↔',
        r'\\Leftrightarrow': '⇔',
        r'\\downarrow': '↓',
        r'\\uparrow': '↑',
        r'\\approx': '≈',
        r'\\neq': '≠',
        r'\\geq': '≥',
        r'\\leq': '≤',
        r'\\pm': '±',
        r'\\infty': '∞',
    }
    
    # 1. 替換已知符號
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    # 2. 移除殘留的 LaTeX 指令 (如 \alpha)
    content = re.sub(r'\\([a-zA-Z]+)', ' ', content)
    
    # 3. 移除大括號 { }
    content = content.replace('{', '').replace('}', '')
    
    return content

def sanitize_text(text):
    """
    Perform deterministic string replacement to eliminate LaTeX artifacts
    while preserving the intended meaning (e.g., arrows).
    """
    # 1. 處理雙美元符號塊 $$...$$
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: sanitize_latex_block(m), text, flags=re.DOTALL)
    
    # 2. 處理單美元符號塊 $...$
    text = re.sub(r'\$(.*?)\$', lambda m: sanitize_latex_block(m), text)
    
    # 3. 最後清理可能殘留的孤立美元符號
    text = text.replace('$', '')
    
    return text

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Deterministic Output Sanitizer v2.0")
    parser.add_argument("--text", type=str, required=True, help="The text to sanitize")
    args = parser.parse_args()
    
    result = sanitize_text(args.text)
    print(result)

if __name__ == "__main__":
    main()
