import json
import re
import argparse
import sys

def purify_text(text):
    # 1. 移除所有 $ 符號 (LaTeX 定界符)
    text = text.replace('$', '')
    
    # 2. 處理 \text{...} 類標籤 - 提取內容並移除標籤
    text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
    
    # 3. 定義確定性替換映射 (按長度排序，優先替換長符號)
    replacements = [
        (r'\\rightarrow', '然後'),
        (r'\\downarrow', '下降'),
        (r'\\uparrow', '上升'),
        (r'\\approx', '約等於'),
        (r'\\Rightarrow', '導致'),
        (r'\\Leftarrow', '由...得出'),
        (r'\\Leftrightarrow', '等同於'),
        ('→', '然後'),
        ('↓', '下降'),
        ('↑', '上升'),
        ('≈', '約等於'),
    ]
    
    # 執行替換
    # 注意：因為 input text 包含字面量的 \rightarrow, 
    # 我們在 Python 中使用 .replace() 時，要確保匹配的是字面量
    for pattern, replacement in replacements:
        # 處理 LaTeX 風格的 \rightarrow
        if pattern.startswith('\\'):
            # 將 \rightarrow 轉為字面量
            text = text.replace(pattern[1:], replacement) # 嘗試去掉反斜杠匹配
            # 重新嘗試帶反斜杠的匹配 (某些環境下)
            text = text.replace(pattern, replacement)
        else:
            text = text.replace(pattern, replacement)
            
    # 修正：針對 \rightarrow 等常見 LaTeX 符號的精確字面量替換
    # 由於 \ 是轉義符，直接用 replace 處理字面量
    text = text.replace('\\rightarrow', '然後')
    text = text.replace('\\downarrow', '下降')
    text = text.replace('\\uparrow', '上升')
    text = text.replace('\\approx', '約等於')
    text = text.replace('\\Rightarrow', '導致')
    text = text.replace('\\Leftarrow', '由...得出')
    text = text.replace('\\Leftrightarrow', '等同於')
        
    # 4. 物理掃蕩：移除所有殘留的 \指令 (例如 \alpha)
    text = re.sub(r'\\([a-zA-Z]+)', ' ', text)
    
    # 5. 移除殘留的 { }
    text = text.replace('{', '').replace('}', '')
    
    # 6. 清理空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=str)
    parser.add_argument("--file", type=str)
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        sys.exit(1)
    
    print(purify_text(content))

if __name__ == "__main__":
    main()
