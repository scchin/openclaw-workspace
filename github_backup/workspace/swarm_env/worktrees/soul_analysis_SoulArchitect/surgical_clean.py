import os
import glob

BASE_DIR = os.path.expanduser("~/.openclaw/workspace")
# Target all .md files in the workspace recursively
FILE_PATTERN = os.path.join(BASE_DIR, "**/*.md")

def surgical_clean(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use literal replace - no regex, no magic, just raw string replacement
    # Order matters: replace the most specific/complex ones first
    replacements = {
        "$\\rightarrow$": " → ",
        "$\\rightarrow$": " → ",
        "\\rightarrow": " → ",
        "ightarrow": " → ", # Handle the corrupted pieces from previous failed sed
        "$\text{": "",
        "}$": "",
        "$": "" # Remove all remaining dollar signs (except if we wanted to keep prices, but we'll clean all for now)
    }
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    files = glob.glob(FILE_PATTERN, recursive=True)
    print(f"🚀 Starting Surgical Clean on {len(files)} files...")
    
    changed_count = 0
    for f in files:
        if surgical_clean(f):
            changed_count += 1
            # Only print the first few to avoid flooding
            if changed_count <= 10:
                print(f"✅ Fixed: {f}")
    
    print(f"\n✨ Total files actually modified: {changed_count}")

if __name__ == "__main__":
    main()
