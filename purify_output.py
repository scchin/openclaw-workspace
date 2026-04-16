import re
import sys
import argparse

def purify_text(text: str) -> str:
    """
    物理級輸出淨化函數：將 LaTeX 符號強制替換為 Unicode 符號。
    """
    cleaned_text = text
    
    # 1. 處理 LaTeX 箭頭 (優先處理，因為它們最容易被模型優先生成)
    # 匹配 $\rightarrow$, $\Rightarrow$, $\longrightarrow$ 以及不帶 $ 的 \rightarrow
    latex_arrows = [
        (r'\$\s*\\rightarrow\s*\$', '→'),
        (r'\$\s*\\Rightarrow\s*\$', '⇒'),
        (r'\$\s*\\longrightarrow\s*\$', '⟶'),
        (r'\$\s*\\Leftarrow\s*\$', '⇐'),
        (r'\$\s*\\leftrightarrow\s*\$', '↔'),
        (r'\\rightarrow', '→'),
        (r'\\Rightarrow', '⇒'),
        (r'\\longrightarrow', '⟶'),
        (r'\\Leftarrow', '⇐'),
        (r'\\leftrightarrow', '↔'),
    ]
    
    for pattern, replacement in latex_arrows:
        cleaned_text = re.sub(pattern, replacement, cleaned_text)
    
    # 2. 處理 \text{...} 標記
    # 使用非貪婪匹配，將 \text{內容} 替換為 內容
    # 處理多次出現的情況
    cleaned_text = re.sub(r'\\text\{([^}]*)\}', r'\1', cleaned_text)
    
    # 3. 清理殘餘的 LaTeX 定界符
    # 移除所有的 $ 符號
    cleaned_text = cleaned_text.replace('$', '')
    
    # 4. 清理可能殘留的 LaTeX 大括號 (僅在沒有對應開括號時)
    # 簡單處理：移除孤立的 { 或 }
    # 但為了安全，我們優先處理成對的-這裡暫不處理，除非看到明顯問題
    
    return cleaned_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenClaw Output Purifier")
    parser.add_argument("--text", type=str, help="Text to purify", required=True)
    args = parser.parse_args()
    
    print(purify_text(args.text))
