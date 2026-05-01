import os
import argparse
import fnmatch

def doc_master(path, query, extension="*", limit=5):
    print(f"🔍 [PowerSkill] Scanning '{path}' for '{query}'...")
    
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, extension):
            full_path = os.path.join(root, filename)
            try:
                with open(full_path, "r", errors="ignore") as f:
                    content = f.read()
                    if query in content:
                        matches.append(full_path)
            except Exception:
                continue

    if not matches:
        print("❌ No matches found.")
        return

    print(f"✅ Found {len(matches)} files. Reading top {limit}...")
    
    report = []
    for m in matches[:limit]:
        with open(m, "r", errors="ignore") as f:
            lines = f.readlines()
            # 找到匹配行
            found_lines = [f"L{i+1}: {line.strip()}" for i, line in enumerate(lines) if query in line]
            report.append({
                "file": m,
                "snippets": found_lines[:3] # 每個檔案只取前三個片段
            })

    print("--- SEARCH REPORT ---")
    for item in report:
        print(f"\n📄 File: {item['file']}")
        for snip in item['snippets']:
            print(f"  {snip}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DocMaster: Search and read multiple files in one turn.")
    parser.add_argument("path", help="Search path")
    parser.add_argument("query", help="Text query")
    parser.add_argument("--ext", default="*", help="File extension filter")
    parser.add_argument("--limit", type=int, default=5, help="Max files to read")
    args = parser.parse_args()
    
    doc_master(args.path, args.query, args.ext, args.limit)
