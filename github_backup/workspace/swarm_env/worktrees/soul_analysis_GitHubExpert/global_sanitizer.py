import os
import glob
import re

# Target all markdown and json files in the workspace
WORKSPACE_DIR = os.path.expanduser("~/.openclaw/workspace")
FILE_PATTERN = os.path.join(WORKSPACE_DIR, "**/*.md") 
# Also include config files and hidden files if necessary
JSON_PATTERN = os.path.join(WORKSPACE_DIR, "**/*.json")

def global_purge(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Target all variations of arrows and LaTeX math delimiters
        # Match any sequence containing 'arrow' wrapped in non-alphanumeric chars
        content = re.sub(r'[^a-zA-Z0-9\s]*arrow[^a-zA-Z0-9\s]*', ' → ', content)
        
        # 2. Remove \text{...} and other LaTeX commands
        content = re.sub(r'\\text\{', '', content)
        content = content.replace('}', '') 
        
        # 3. Remove all stray dollar signs (not followed by digits for price)
        content = re.sub(r'\$(?!\d)', '', content)
        content = re.sub(r'(?<!\d)\$', '', content)
        
        # 4. Clean up excessive spaces
        content = content.replace('  ', ' ').strip()

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False

def main():
    # Use recursive glob for all .md files
    md_files = glob.glob(FILE_PATTERN, recursive=True)
    json_files = glob.glob(JSON_PATTERN, recursive=True)
    all_files = md_files + json_files
    
    print(f"🚀 Starting Workspace-Wide Sanitization on {len(all_files)} files...")
    
    changed_count = 0
    for f in all_files:
        if global_purge(f):
            changed_count += 1
            print(f"💥 Purged: {f}")

    print(f"\n✨ Total files sanitized: {changed_count}")

if __name__ == "__main__":
    main()
