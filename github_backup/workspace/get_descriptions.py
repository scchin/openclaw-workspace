import os
from pathlib import Path

folders = [
    "agents", "backups", "browser", "canvas", "completions", "cron", "devices",
    "dna", "flows", "guardian", "hooks", "identity", "lib", "logs", "media",
    "memory", "prompts", "qqbot", "rate-limit-proxy", "repo", "runtime",
    "skills", "subagents", "tasks", "test_dir", "workspace"
]

root = Path('/Users/KS/.openclaw')

def get_desc(folder):
    path = root / folder
    if not path.exists(): return "不存在"
    for readme in ['README.md', 'SKILL.md', 'description.txt']:
        readme_path = path / readme
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    line = f.readline().strip()
                    if line.startswith('#'): line = line.lstrip('# ').strip()
                    return line[:100]
            except: pass
    return "無簡介"

for f in folders:
    print(f"{f}: {get_desc(f)}")
