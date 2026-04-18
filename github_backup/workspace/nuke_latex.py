import os
import glob
import re

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/.agents/skills/huashu-nuwa")
FILE_PATTERN = os.path.join(BASE_DIR, "examples/*/SKILL.md")

def nuke_latex(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. 暴力替換所有包含 'rightarrow' 的組合 (不管前後有幾個 $ 或 \)
    # 匹配如 $\rightarrow$, $$ightarrow$, \rightarrow, $\rightarrow$ 等
    content = re.sub(r'[^a-zA-Z0-9\s]*rightarrow[^a-zA-Z0-9\s]*', ' → ', content)
    
    # 2. 移除 \text{...} 結構
    content = re.sub(r'\\text\{(.*?)\}', r'\1', content)
    
    # 3. 移除所有殘留的 $ 符號 (除非後面跟著數字，判定為價格)
    # 匹配所有不接數字的 $
    content = re.sub(r'\$(?!\d)', '', content)
    # 匹配所有不接在數字後的 $
    content = re.sub(r'(?<!\d)\$', '', content)
    
    # 4. 清理多餘的空格
    content = content.replace('  ', ' ').strip()

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    files = glob.glob(FILE_PATTERN)
    print(f"🚀 Executing Nuke-Clean on {len(files)} files...")
    
    changed_count = 0
    for f in files:
        if nuke_latex(f):
            changed_count += 1
            print(f"💥 Nuked: {os.path.basename(f)}")
            
    main_skill = os.path.join(BASE_DIR, "SKILL.md")
    if os.path.exists(main_skill) and nuke_latex(main_skill):
        changed_count += 1
        print(f"💥 Nuked: SKILL.md")

    print(f"\n✨ Total files purged: {changed_count}")

if __name__ == "__main__":
    main()
