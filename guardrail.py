import sys
import re

def check_output(text):
    # 定義禁忌符號 (LaTeX 相關)
    forbidden_patterns = [
        r'\$',                # 禁止任何 $ 符號
        r'\\rightarrow',       # 禁止 \rightarrow
        r'\\text',            # 禁止 \text
        r'\\begin',           # 禁止 \begin
        r'\\end',             # 禁止 \end
    ]
    
    violations = []
    for pattern in forbidden_patterns:
        if re.search(pattern, text):
            violations.append(pattern)
            
    if violations:
        return False, violations
    return True, []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No text provided for scanning.")
        sys.exit(1)
        
    input_text = sys.argv[1]
    is_clean, found = check_output(input_text)
    
    if not is_clean:
        print(f"REJECTED: Forbidden symbols found: {found}")
        sys.exit(1) # 返回非零狀態碼表示攔截
    else:
        print("CLEAN: No forbidden symbols found.")
        sys.exit(0)
