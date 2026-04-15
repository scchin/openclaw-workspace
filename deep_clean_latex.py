import os
import glob

# Target directory
BASE_DIR = os.path.expanduser("~/.openclaw/workspace/.agents/skills/huashu-nuwa")
FILE_PATTERN = os.path.join(BASE_DIR, "examples/*/SKILL.md")

def deep_clean_latex(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Replace the most common arrow pattern
    content = content.replace(r"$\rightarrow$", "→")
    content = content.replace(r"\\rightarrow", "→")
    
    # 2. Remove LaTeX text blocks: $\text{content}$ -> content
    import re
    content = re.sub(r"\$\text\{(.*?)\}\$", r"\1", content)
    
    # 3. Clean up any remaining stray dollar signs used as delimiters
    # We only remove $ if it's not part of a price (e.g., $50)
    # Simple heuristic: if $ is not followed by a digit, it's likely LaTeX
    content = re.sub(r"\$(?!\d)", "", content)
    content = re.sub(r"(?<!\d)\$", "", content)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    files = glob.glob(FILE_PATTERN)
    print(f"🚀 Starting deep clean on {len(files)} files...")
    
    changed_count = 0
    for f in files:
        if deep_clean_latex(f):
            changed_count += 1
            print(f"✅ Cleaned: {os.path.basename(f)}")
            
    # Also clean the main Nuwa skill file
    main_skill = os.path.join(BASE_DIR, "SKILL.md")
    if os.path.exists(main_skill) and deep_clean_latex(main_skill):
        changed_count += 1
        print(f"✅ Cleaned: SKILL.md")

    print(f"\n✨ Total files cleaned: {changed_count}")

if __name__ == "__main__":
    main()
