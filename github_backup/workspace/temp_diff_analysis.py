import os

def get_file_list(root_dir):
    file_set = set()
    for root, dirs, files in os.walk(root_dir):
        # Skip the backup folder itself to avoid recursion
        if 'github_backup' in root:
            continue
        for file in files:
            # Get relative path
            rel_path = os.path.relpath(os.path.join(root, file), root_dir)
            file_set.add(rel_path)
    return file_set

local_root = "/Users/KS/.openclaw/workspace"
github_root = "/Users/KS/.openclaw/workspace/github_backup/workspace"

local_files = get_file_list(local_root)
github_files = get_file_list(github_root)

missing_in_github = local_files - github_files
extra_in_github = github_files - local_files

print(f"Local files count: {len(local_files)}")
print(f"GitHub files count: {len(github_files)}")
print(f"Missing in GitHub: {len(missing_in_github)}")
print("\n--- Missing Files in GitHub ---")
for f in sorted(list(missing_in_github)):
    print(f)

print("\n--- Extra Files in GitHub ---")
for f in sorted(list(extra_in_github)):
    print(f)
