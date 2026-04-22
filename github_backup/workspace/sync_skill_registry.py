import os
import json
import subprocess
from pathlib import Path

# ==========================================
# 不朽註冊同步器 (Immortal Registry Synchronizer) v1.0
# ==========================================
# 邏輯：
# 1. 物理偵測 /workspace 下所有的 .skill 文件與目錄。
# 2. 自動下達 chflags nouchg 解鎖主設定檔。
# 3. 比對並將缺失的技能補進 openclaw.json。
# 4. 重新下達 chflags uchg 鎖死設定檔，恢復「不朽架構」。

OPENCLAW_DIR = Path("/Users/KS/.openclaw")
WORKSPACE_DIR = OPENCLAW_DIR / "workspace"
CONFIG_FILE = OPENCLAW_DIR / "openclaw.json"

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True, shell=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}\n{e.stderr.decode()}")

def get_installed_skills():
    # 偵測 .skill 檔案
    skills = [f.stem for f in WORKSPACE_DIR.glob("*.skill")]
    
    # 偵測 /skills/ 目錄下的資料夾
    skills_dir = WORKSPACE_DIR / "skills"
    if skills_dir.exists():
        skills += [d.name for d in skills_dir.iterdir() if d.is_dir()]
        
    # 加入手動定義的 openclaw-soul-sync
    skills.append("openclaw-soul-sync")
    
    # 去重
    return sorted(list(set(skills)))

def sync_registry():
    print("🧬 Initiating Immortal Registry Sync...")
    
    # 1. 採集物理技能
    physical_skills = get_installed_skills()
    print(f"Found {len(physical_skills)} physical skills in workspace.")

    # 2. 解鎖設定檔
    print("🔓 Unlocking openclaw.json...")
    run_cmd(f"chflags nouchg {CONFIG_FILE}")

    try:
        # 3. 讀取並更新 JSON
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        if "skills" not in config: config["skills"] = {"allowBundled": [], "entries": {}}
        
        allow_bundled = config["skills"].get("allowBundled", [])
        entries = config["skills"].get("entries", {})

        added_count = 0
        for skill_id in physical_skills:
            if skill_id not in entries:
                print(f"➕ Registering NEW skill: {skill_id}")
                entries[skill_id] = {"enabled": True}
                if skill_id not in allow_bundled:
                    allow_bundled.append(skill_id)
                added_count += 1
            else:
                # 確保已啟動
                if not entries[skill_id].get("enabled"):
                    entries[skill_id]["enabled"] = True
                    print(f"🆙 Re-enabled skill: {skill_id}")

        config["skills"]["allowBundled"] = allow_bundled
        config["skills"]["entries"] = entries

        # 4. 寫回並鎖死
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Sync complete. Added {added_count} skills to registry.")

    except Exception as e:
        print(f"❌ Failed to sync: {e}")
    finally:
        print("🔒 Re-locking openclaw.json (Permanent Armor Active)...")
        run_cmd(f"chflags uchg {CONFIG_FILE}")

if __name__ == "__main__":
    sync_registry()
