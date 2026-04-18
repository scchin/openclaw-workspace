import argparse
import re
import sys

# 映射表：將 LaTeX 代碼映射為純粹的 Unicode 符號
# 為了避免正則表達式的轉義地獄，我們使用簡單的字串替換
SYMBOL_MAP = [
    ('$\\rightarrow$', '→'),
    (r'\rightarrow', '→'),
    ('$\\downarrow$', '↓'),
    (r'\downarrow', '↓'),
    ('$\\uparrow$', '↑'),
    (r'\uparrow', '↑'),
    ('$\\approx$', '≈'),
    (r'\approx', '≈'),
]

def filter_symbols(text):
    """
    物理清洗函數：將所有 LaTeX 樣式的代碼強制替換為純符號或純文字
    """
    filtered_text = text
    
    # 1. 處理明確的符號對應 (先處理帶 $ 的，再處理單純反斜槓的)
    for pattern, replacement in SYMBOL_MAP:
        filtered_text = filtered_text.replace(pattern, replacement)

    # 2. 處理 \text{...} 結構
    filtered_text = re.sub(r'\\text\{(.+?)\}', r'\1', filtered_text)
    
    # 3. 移除所有殘留的美元符號 $ (最後一道防線)
    filtered_text = filtered_text.replace('$', '')
    
    return filtered_text

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Symbol Filter")
    parser.add_argument("--text", type=str, required=True, help="The text to filter")
    args = parser.parse_args()
    
    print(filter_symbols(args.text))

if __name__ == "__main__":
    main()
