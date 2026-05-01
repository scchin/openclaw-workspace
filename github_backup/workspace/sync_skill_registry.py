import shutil
import os
import json
import subprocess
from pathlib import Path

# ==========================================
# 不朽註冊同步器 (Immortal Registry Synchronizer) v2.0
# ==========================================
# 升級亮點：
# 1. 自動從 /Users/KS/.agents/skills/ 導引正規軍技能。
# 2. 自動在 workspace/skills/ 建立物理連結。
# 3. 自動執行註冊表注入與 uchg 鎖定。

OPENCLAW_DIR = Path("/Users/KS/.openclaw")
WORKSPACE_DIR = OPENCLAW_DIR / "workspace"
CONFIG_FILE = OPENCLAW_DIR / "openclaw.json"
OFFICIAL_SKILLS_SOURCE = Path("/Users/KS/.agents/skills")
WORKSPACE_SKILLS_DIR = WORKSPACE_DIR / "skills"

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True, shell=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}\n{e.stderr.decode()}")

def ensure_official_alignment():
    """
    [不朽基因] 自動校準：將 .agents/下的正規軍連結至工作區。
    """
    print("🛡️ Checking Official Skill Alignment...")
    if not WORKSPACE_SKILLS_DIR.exists():
        WORKSPACE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    
    if OFFICIAL_SKILLS_SOURCE.exists():
        for item in OFFICIAL_SKILLS_SOURCE.iterdir():
            if item.is_dir():
                # 處理版本號後綴 (例如 openclaw-soul-sync-1.0.0 -> openclaw-soul-sync)
                skill_id = item.name.split("-1.0.0")[0] if "-1.0.0" in item.name else item.name
                target_link = WORKSPACE_SKILLS_DIR / skill_id
                
                if not target_link.exists():
                    print(f"🔗 [Immortal Link] Creating symlink for {skill_id}...")
                    shutil.copytree(item, target_link)
                else:
                    # 確保連結指向正確
                    if target_link.is_symlink() and str(os.readlink(target_link)) != str(item):
                        print(f"🔄 [Immortal Update] Updating symlink for {skill_id}...")
                        target_link.unlink()
                        shutil.copytree(item, target_link)

def get_installed_skills():
    # 1. 先執行物理對齊
    ensure_official_alignment()
    
    # 2. 偵測 .skill 檔案
    skills = [f.stem for f in WORKSPACE_DIR.glob("*.skill")]
    
    # 3. 偵測 /skills/ 目錄下的資料夾與連結
    if WORKSPACE_SKILLS_DIR.exists():
        skills += [d.name for d in WORKSPACE_SKILLS_DIR.iterdir() if d.is_dir() or d.is_symlink()]
        
    return sorted(list(set(skills)))

def sync_registry():
    print("🧬 Initiating Immortal Registry Sync v2.0...")
    
    # 採集物理技能 (包含已對齊的正規軍)
    physical_skills = get_installed_skills()
    print(f"Found {len(physical_skills)} physical skills in workspace.")

    # 解鎖設定檔
    print("🔓 Unlocking openclaw.json...")
    run_cmd(f"chflags nouchg {CONFIG_FILE}")

    try:
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
                if not entries[skill_id].get("enabled"):
                    entries[skill_id]["enabled"] = True
                    print(f"🆙 Re-enabled skill: {skill_id}")

        config["skills"]["allowBundled"] = allow_bundled
        config["skills"]["entries"] = entries

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
