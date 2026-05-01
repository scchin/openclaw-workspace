# [system_gene_sentry.py] - v2.0.0 (Guardian Edition)
# 說明：大統一治理之核心引擎。整合恢復 (Recovery) 與 基因修復 (Healing)。
# 變更：1. 加入基因完整性比對邏輯。2. 支持 --heal 自動癒合模式。3. 實作 --update-genome 同步機制。
# 修正：精緻化比對算法，防止因路徑差異導致的誤判。

import argparse
import json
import os
import sys
import subprocess
import shutil
import filecmp
from datetime import datetime

# --- [FORTRESS INTEGRATION] ---
sys.path.append(os.path.expanduser("~/.openclaw/lib"))
try:
    from workspace_guardian import WorkspaceGuardian
except ImportError:
    WorkspaceGuardian = None
# ------------------------------

class RegistryAligner:
    """[v12.6] 註冊表對齊哨兵：負責物理更名與地圖對位。"""
    def __init__(self, openclaw_json_path):
        self.config_path = openclaw_json_path

    def align_skill(self, skill_id, current_path, target_version):
        new_path = os.path.join(os.path.dirname(current_path), f"{skill_id}-{target_version}")
        if current_path == new_path: return True
        
        update_progress(f"Aligning {skill_id}: {os.path.basename(current_path)} -> {target_version}")
        try:
            # 1. 物理更名
            if os.path.exists(current_path):
                # 處理可能的 uchg 鎖定
                subprocess.run(["chflags", "nouchg", current_path], capture_output=True)
                os.rename(current_path, new_path)
            
            # 2. 自動建立軟連結 (Legacy Support)
            if not os.path.exists(current_path):
                os.symlink(new_path, current_path)
                
            return True
        except Exception as e:
            update_progress(f"❌ Alignment failed for {skill_id}: {e}")
            return False

# --- 配置區 ---
OPENCLAW_DIR = "/Users/KS/.openclaw/"
WORKSPACE_PATH = "/Users/KS/.openclaw/workspace/"
GENOME_PATH = os.path.join(WORKSPACE_PATH, ".genome/")
INTENSITY_LEVELS = {"LIGHT": 1, "STANDARD": 2, "STRICT": 3}
REGISTRY_PATH = os.path.join(WORKSPACE_PATH, "system_health_registry.json")
SANITIZER_PATH = os.path.join(WORKSPACE_PATH, "output_sanitizer.py")

def update_progress(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"📡 [{timestamp}] {message}")

# 基因監控名單 (Key: 實際路徑, Value: DNA檔名)
GENOME_MAP = {
    "AGENTS.md": "AGENTS.md.dna",
    "system_health_registry.json": "system_health_registry.json.dna",
    "bin/gateway_guardian.py": "gateway_guardian.py.dna",
    "SOUL.md": "SOUL.md.dna"
}

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_and_heal_genetics(heal=True):
    """檢查基因完整性，並在需要時進行自動癒合"""
    healing_reports = []
    overall_genetic_status = "PASS"
    
    for relative_path, dna_name in GENOME_MAP.items():
        actual_file = os.path.join(WORKSPACE_PATH, relative_path)
        dna_file = os.path.join(GENOME_PATH, dna_name)
        
        if not os.path.exists(dna_file):
            healing_reports.append(f"❌ GENOME MISSING: {dna_name}")
            overall_genetic_status = "FAIL"
            continue
            
        if not os.path.exists(actual_file):
            if heal:
                shutil.copy2(dna_file, actual_file)
                healing_reports.append(f"♻️ HEALED (Restored): {relative_path}")
            else:
                healing_reports.append(f"❌ MISSING: {relative_path}")
                overall_genetic_status = "FAIL"
        else:
            # 比對內容
            if not filecmp.cmp(actual_file, dna_file, shallow=False):
                if heal:
                    shutil.copy2(dna_file, actual_file)
                    healing_reports.append(f"♻️ HEALED (Corrected): {relative_path}")
                else:
                    healing_reports.append(f"⚠️ DIVERGED: {relative_path}")
                    if overall_genetic_status != "FAIL":
                        overall_genetic_status = "WARN"
            else:
                healing_reports.append(f"✅ INTACT: {relative_path}")
                
    return overall_genetic_status, healing_reports

def update_genome():
    """將當前文件同步為新的基因樣本 (Commit DNA)"""
    print("🧬 Initiating Genome Sync (DNA Commit)...")
    success_count = 0
    for relative_path, dna_name in GENOME_MAP.items():
        actual_file = os.path.join(WORKSPACE_PATH, relative_path)
        dna_file = os.path.join(GENOME_PATH, dna_name)
        
        if os.path.exists(actual_file):
            shutil.copy2(actual_file, dna_file)
            print(f"✅ Updated DNA for: {relative_path}")
            success_count += 1
        else:
            print(f"❌ Cannot update DNA: {relative_path} not found.")
            
    print(f"🧬 Genome Synchronization complete. {success_count} assets committed.")

# --- Native Health Checks (繼承自 GURF) ---
def native_check_rec_pending_tasks():
    path = os.path.join(WORKSPACE_PATH, "pending_tasks.json")
    if not os.path.exists(path):
        return "WARN", "pending_tasks.json not found", ""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            count = len(data) if isinstance(data, list) else 0
            return ("PASS" if count == 0 else "WARN"), f"Found {count} pending tasks.", str(data)
    except Exception as e:
        return "FAIL", f"Error reading pending_tasks.json: {str(e)}", ""

def native_check_backup_robustness():
    """檢查 GitHub 備份的穩健性狀態"""
    backup_path = os.path.join(OPENCLAW_DIR, "backups")
    if not os.path.exists(backup_path):
        return "WARN", "Local backup folder missing", ""
    
    # 檢查是否存在不符合規範的根目錄分卷 (應已在清理階段刪除)
    # 這裡我們檢查是否有任何 .bin 在根目錄下
    root_bins = [f for f in os.listdir(backup_path) if f.endswith(".bin") and os.path.isfile(os.path.join(backup_path, f))]
    if root_bins:
        return "WARN", f"Found {len(root_bins)} non-isolated files in local backups", str(root_bins)
        
    return "PASS", "Backup structure is isolated", ""

def native_check_ctx_persona_sync():
    checks = []
    for f in ["SOUL.md", "USER.md"]:
        path = os.path.join(WORKSPACE_PATH, f)
        if os.path.exists(path) and os.access(path, os.R_OK):
            checks.append(f"{f}: OK")
        else:
            checks.append(f"{f}: MISSING")
    status = "PASS" if all("OK" in c for c in checks) else "FAIL"
    return status, " | ".join(checks), ""

def native_check_disk_space():
    """檢查工作區所在的磁碟空間"""
    try:
        usage = shutil.disk_usage(OPENCLAW_DIR)
        free_gb = usage.free / (1024**3)
        status = "PASS" if free_gb > 1.0 else "WARN"
        return status, f"Disk space: {free_gb:.2f} GB free", f"Total: {usage.total/(1024**3):.2f} GB"
    except Exception as e:
        return "FAIL", f"Disk check error: {str(e)}", ""

def native_check_process_status():
    """檢查核心進程狀態 (以網關為例)"""
    # 這裡使用 launchctl list 檢查是否在運行
    code, stdout, stderr = run_command("launchctl list | grep openclaw")
    if code == 0 and "ai.openclaw.gateway" in stdout:
        return "PASS", "OpenClaw Gateway is running", stdout.strip()
    else:
        return "WARN", "OpenClaw Gateway process not found in launchctl", stderr

def native_check_permissions():
    """檢查工作區權限"""
    paths = [WORKSPACE_PATH, GENOME_PATH]
    issues = []
    for p in paths:
        if not os.access(p, os.W_OK):
            issues.append(f"No write access: {p}")
    status = "PASS" if not issues else "FAIL"
    return status, ("Permissions OK" if status == "PASS" else " | ".join(issues)), ""

def main():
    parser = argparse.ArgumentParser(description="Immortal Gene Sentry - System Life Guardian")
    parser.add_argument("--intensity", choices=["LIGHT", "STANDARD", "STRICT"], default="STANDARD")
    parser.add_argument("--heal", action="store_true", default=True, help="Auto-heal deviations")
    parser.add_argument("--no-heal", action="store_false", dest="heal", help="Check only, do not heal")
    parser.add_argument("--update-genome", action="store_true", help="Commit current files as DNA")
    args = parser.parse_args()

    if args.update_genome:
        update_genome()
        return

    intensity_val = INTENSITY_LEVELS[args.intensity]
    results = []
    overall_status = "PASS"

    # 0. 身分堡壘：工作區主動獵殺 (Fortress Purge)
    if WorkspaceGuardian:
        update_progress("Initiating Fortress Hunter: Workspace Purge...")
        guardian = WorkspaceGuardian()
        guardian.hunt()
    
    # 0.5 註冊表對位手術 (Registry Aligner)
    aligner = RegistryAligner(os.path.join(OPENCLAW_DIR, "openclaw.json"))
    # 這裡我們硬編碼目前需要對齊的關鍵技能
    official_sync_path = "/Users/KS/.agents/skills/openclaw-soul-sync-1.0.0"
    if os.path.exists(official_sync_path):
        aligner.align_skill("openclaw-soul-sync", official_sync_path, "2.3.1")
    
    # 1. 基因哨兵檢查 (Healing Phase)
    gen_status, gen_reports = check_and_heal_genetics(heal=args.heal)
    if gen_status == "FAIL": overall_status = "FAIL"
    elif gen_status == "WARN" and overall_status != "FAIL": overall_status = "WARN"
    
    results.append({
        "id": "gen_integrity_sentry",
        "name": "Genetic Integrity & Auto-Healing",
        "status": gen_status,
        "message": " | ".join(gen_reports),
        "details": ""
    })

    # 2. 恢復項檢查 (Checking Phase)
    if not os.path.exists(REGISTRY_PATH):
        print(json.dumps({"overall_status": "FAIL", "message": "Registry missing"}, indent=2))
        return

    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)

    modules = registry.get("modules", [])
    filtered_modules = [m for m in modules if INTENSITY_LEVELS.get(m["intensity"], 3) <= intensity_val]
    filtered_modules.sort(key=lambda x: x["priority"])

    for mod in filtered_modules:
        mod_id = mod["id"]
        if mod["type"] == "native":
            if mod_id == "rec_pending_tasks": status, msg, details = native_check_rec_pending_tasks()
            elif mod_id == "ctx_persona_sync": status, msg, details = native_check_ctx_persona_sync()
            elif mod_id == "soul_sync_robustness": status, msg, details = native_check_backup_robustness()
            elif mod_id == "disk_space_check": status, msg, details = native_check_disk_space()
            elif mod_id == "process_status_check": status, msg, details = native_check_process_status()
            elif mod_id == "permission_check": status, msg, details = native_check_permissions()
            # 其他 Native 略 (可根據需要補完)
            else: status, msg, details = "PASS", "Module active", "" 
        elif mod["type"] == "external":
            # 特別處理：註冊表同步器
            if mod_id == "registry_sync_sentry":
                update_progress("Executing Immortal Registry Sync...")
                sync_cmd = f"python3 {os.path.join(WORKSPACE_PATH, 'sync_skill_registry.py')}"
                code, stdout, stderr = run_command(sync_cmd)
            else:
                code, stdout, stderr = run_command(mod.get("command", ""))
            
            status = "PASS" if code == 0 else "FAIL"
            msg = "External check complete" if code == 0 else f"External failed: {stderr.strip()}"
            details = stdout if code == 0 else stderr
        else: status, msg, details = "FAIL", "Unknown type", ""

        if status == "FAIL": overall_status = "FAIL"
        elif status == "WARN" and overall_status != "FAIL": overall_status = "WARN"

        results.append({"id": mod_id, "name": mod.get("name", ""), "status": status, "message": msg, "details": details})

    # 3. 輸出報告與純化
    status_card = {
        "timestamp": datetime.now().isoformat(),
        "intensity": args.intensity,
        "overall_status": overall_status,
        "checks": results
    }
    
    temp_report_path = os.path.join(WORKSPACE_PATH, "temp_health_report.json")
    with open(temp_report_path, 'w') as f:
        json.dump(status_card, f, indent=2)

    code, stdout, stderr = run_command(f"python3 {SANITIZER_PATH} --file {temp_report_path}")
    print(stdout if code == 0 else json.dumps(status_card, indent=2))

if __name__ == "__main__":
    main()
