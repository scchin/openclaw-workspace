import sys
import re

def physical_filter(text):
    # 1. 處理 \rightarrow 或 $\rightarrow$
    text = re.sub(r'\\rightarrow', '→', text)
    text = re.sub(r'\$\rightarrow\$', '→', text)
    
    # 2. 處理 $\text{...}$
    text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
    
    # 3. 移除所有剩餘的 $ 符號 (物理刪除)
    text = text.replace('$', '')
    
    # 4. 處理常見的 LaTeX 數學包圍
    text = re.sub(r'\[.*?\]', '', text) # 移除 display math (簡單處理)
    
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    input_text = sys.argv[1]
    print(physical_filter(input_text))
