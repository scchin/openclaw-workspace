import os
import re
import json
from datetime import datetime
from pathlib import Path

PATHS = {
    "Agents": Path("/Users/KS/.agents/skills/"),
    "Workspace": Path("/Users/KS/.openclaw/workspace/skills/"),
    "OpenClaw": Path("/Users/KS/.openclaw/skills/")
}

def normalize(name):
    return re.sub(r'-\d+(\.\d+)*$', '', name)

def get_skill_info(path, folder_name):
    skill_path = path / folder_name
    skill_md = skill_path / "SKILL.md"
    
    desc = "無簡介"
    mtime = None
    
    if skill_md.exists():
        mtime = skill_md.stat().st_mtime
        try:
            content = skill_md.read_text(encoding='utf-8')
            match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                yaml_block = match.group(1)
                for line in yaml_block.split('\n'):
                    if line.startswith('description:'):
                        desc = line.replace('description:', '').strip()
                        break
            if desc == "無簡介":
                lines = content.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('---'):
                        desc = line.strip()[:50] + "..."
                        break
        except Exception:
            desc = "讀取錯誤"
    elif skill_path.exists():
        mtime = skill_path.stat().st_mtime

    return {
        "description": desc,
        "mtime": mtime,
        "full_name": folder_name
    }

all_skills = {}
for path_key, path_val in PATHS.items():
    if not path_val.exists(): continue
    for item in path_val.iterdir():
        if item.is_dir():
            norm = normalize(item.name)
            if norm not in all_skills:
                all_skills[norm] = {}
            all_skills[norm][path_key] = get_skill_info(path_val, item.name)

duplicates = {norm: infos for norm, infos in all_skills.items() if len(infos) > 1}

print("| 技能名稱 | 目錄 | 詳細名稱 | 修改時間 | 簡介 | 版本分析 |")
print("| :--- | :--- | :--- | :--- | :--- | :--- |")

for norm, infos in duplicates.items():
    latest_path = None
    max_mtime = -1
    for path_key, info in infos.items():
        if info['mtime'] and info['mtime'] > max_mtime:
            max_mtime = info['mtime']
            latest_path = path_key
    
    for path_key, info in infos.items():
        dt = datetime.fromtimestamp(info['mtime']).strftime('%Y-%m-%d %H:%M') if info['mtime'] else "未知"
        is_latest = "**最新**" if path_key == latest_path else ""
        print(f"| {norm} | {path_key} | {info['full_name']} | {dt} | {info['description']} | {is_latest} |")
