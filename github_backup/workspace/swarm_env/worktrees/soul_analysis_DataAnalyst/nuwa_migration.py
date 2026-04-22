#!/usr/bin/env python3
import os
import re
import subprocess
from datetime import datetime

# =============================================================================
# Nuwa-Skill Architecture Migration Tool
# Goal: Decouple "Static Framework" from "Dynamic Examples"
# =============================================================================

EXAMPLES_DIR = os.path.expanduser("~/.openclaw/workspace/.agents/skills/huashu-nuwa/examples")
MP_CLI = "mp" # Assuming 'mp' CLI is available for MemPalace operations

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def migrate_figure(figure_dir):
    figure_name = os.path.basename(figure_dir)
    skill_path = os.path.join(figure_dir, "SKILL.md")
    if not os.path.exists(skill_path):
        return False

    with open(skill_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Extract Dynamic Examples (Cases, Long quotes, Research data)
    # We define "Dynamic" as anything in the "Research" or "Example" sections
    # For simplicity in this script, we will migrate the entire references/research folder
    research_dir = os.path.join(figure_dir, "references/research")
    room_name = f"nuwa-{figure_name.replace('-perspective', '')}"
    
    print(f"📦 Migrating {figure_name} to room: {room_name}...")
    
    # Create room and push research data
    if os.path.exists(research_dir):
        for file in os.listdir(research_dir):
            if file.endswith(".md"):
                file_path = os.path.join(research_dir, file)
                with open(file_path, "r", encoding="utf-8") as rf:
                    data = rf.read()
                    # Use mp add to push to memory
                    run_cmd(f"mp add '{data}' --room {room_name}")

    # 2. Rewrite SKILL.md (The "Lean-up" process)
    # We keep the Framework (Identity, Models, Heuristics, DNA, Boundaries)
    # and remove the verbose Examples/Research sections.
    
    # Simple regex-based pruning for the prototype:
    # Remove sections like "示例对话" or "调研来源" but keep the Core Models
    lines = content.splitlines()
    new_lines = []
    skip = False
    for line in lines:
        if "### 示例对话" in line or "## 调研信息源" in line:
            skip = True
            continue
        if skip and line.startswith("---") or line.startswith("## "):
            # Stop skipping when a new major section starts that isn't a pruned one
            if "调研" not in line and "示例" not in line:
                skip = False
        if not skip:
            new_lines.append(line)

    # Inject the Token-Saving Workflow
    workflow_injection = "\n\n---\n## ⚡ 高效調用流程 (Token-Saving Workflow)\n**強制執行路徑**：\n1. **激活框架**：加載本 Skill 的靜態框架 $\\rightarrow$ 定義思考路徑。\n2. **精準檢索**：調用 `mp search \"關鍵字\" --room " + room_name + "` $\\rightarrow$ 僅檢索最相關的 2-3 個真實案例。\n3. **動態合成**：$\\text{靜態框架} + \\text{精準實例} \\rightarrow \\text{生成高質量回答}$。\n"
    
    final_content = "\n".join(new_lines) + workflow_injection
    
    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    return True

def main():
    if not os.path.exists(EXAMPLES_DIR):
        print(f"Error: Examples directory not found at {EXAMPLES_DIR}")
        return

    figures = [d for d in os.listdir(EXAMPLES_DIR) if os.path.isdir(os.path.join(EXAMPLES_DIR, d))]
    print(f"🚀 Found {len(figures)} figures to migrate.")
    
    success_count = 0
    for fig in figures:
        if migrate_figure(os.path.join(EXAMPLES_DIR, fig)):
            success_count += 1
            print(f"✅ {fig} migrated.")
    
    print(f"\n✨ Migration complete. {success_count}/{len(figures)} figures processed.")

if __name__ == "__main__":
    main()
