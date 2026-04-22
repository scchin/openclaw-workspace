import os
import glob
import re

BASE_DIR = os.path.expanduser("~/.openclaw/workspace")
# Scan EVERYTHING in workspace
FILE_PATTERN = os.path.join(BASE_DIR, "**/*.md") 

def final_purge(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Target any combination of $ and arrow
        content = re.sub(r'[^a-zA-Z0-9\s]*arrow[^a-zA-Z0-9\s]*', ' → ', content)
        # 2. Remove any remaining $ that aren't part of a price
        content = re.sub(r'\$(?!\d)', '', content)
        content = re.sub(r'(?<!\d)\$', '', content)
        # 3. Remove LaTeX text wrappers
        content = re.sub(r'\\text\{', '', content)
        content = content.replace('}', '') 
        
        if content != f.read(): # This logic is slightly wrong, should use stored content
            pass
    except:
        pass

# I will use a simpler, more robust version
def robust_clean(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Replace all common LaTeX arrow forms with a plain arrow
    text = re.sub(r'(\\\rightarrow|\$\rightarrow\$|\$\rightarrow|\rightarrow\$|\$\rightarrow)', ' → ', text)
    # Remove any remaining $ and \text{}
    text = re.sub(r'\$(?!\d)', '', text)
    text = re.sub(r'(?<!\d)\$', '', text)
    text = re.sub(r'\\text\{', '', text)
    text = text.replace('}', '')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def main():
    files = glob.glob(FILE_PATTERN, recursive=True)
    for f in files:
        robust_clean(f)
    print(f"Done cleaning {len(files)} files.")

if __name__ == "__main__":
    main()
