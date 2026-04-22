import os
import glob
import re

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/.agents/skills/huashu-nuwa")
FILE_PATTERN = os.path.join(BASE_DIR, "examples/*/SKILL.md")

def total_purge_v2(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. 獵殺所有包含 'arrow' 的碎片 (處理 $$ightarrow$, \rightarrow, $\rightarrow$, ightarrow 等所有變體)
    # 匹配任何包含 arrow 的序列，且其周圍有非字母數字字符
    content = re.sub(r'[^a-zA-Z0-9\s]*arrow[^a-zA-Z0-9\s]*', ' → ', content)
    
    # 2. 移除 \text{...} 結構
    content = re.sub(r'\\text\{', '', content)
    content = content.replace('}', '') # 暴力清除所有花括號，因為 Nuwa 框架中基本不使用
    
    # 3. 徹底清除所有殘留的 $ 符號 (除非後接數字)
    content = re.sub(r'\$(?!\d)', '', content)
    content = re.sub(r'(?<!\d)\$', '', content)
    
    # 4. 修復可能產生的雙空格
    content = content.replace('  ', ' ').strip()

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    files = glob.glob(FILE_PATTERN)
    print(f"🚀 Executing Total Purge v2 on {len(files)} files...")
    
    changed_count = 0
    for f in files:
        if total_purge_v2(f):
            changed_count += 1
            print(f"💥 Purged: {os.path.basename(f)}")
            
    main_skill = os.path.join(BASE_DIR, "SKILL.md")
    if os.path.exists(main_skill) and total_purge_v2(main_skill):
        changed_count += 1
        print(f"💥 Purged: SKILL.md")

    print(f"\n✨ Total files purged: {changed_count}")

if __name__ == "__main__":
    main()
