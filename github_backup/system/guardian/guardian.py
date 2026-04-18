#!/usr/bin/env python3
"""
System Guardian — 自動化自癒守護者 (v4.0 - Self-Healing Edition)
整合：斷路器、狀態機、以及「Lan & Auth」環境自癒機制。

修復 (v4.0)：
1. 自動校對 openclaw.json 白名單 (allowedOrigins)
2. 自動校對 .plist 環境變數 (API Keys)
3. 自動同步三層金鑰 (.env, models.json, auth-profiles.json)
4. 防止 OpenClaw 版本更新後重置設定。
"""

import json, os, time, subprocess, urllib.request, urllib.error, threading, re
from datetime import datetime

# ─── 設定 ───────────────────────────────────────────────────────────────────
PROXY_HEALTH_URL = "http://127.0.0.1:18799/health"
SYNC_URL         = "http://127.0.0.1:18790/sync"
SYNC_INTERVAL    = 10
GUARDIAN_LOG     = os.path.expanduser("~/.openclaw/logs/system-guardian.log")
STATE_FILE       = os.path.expanduser("~/.openclaw/hooks/google-model-guard/state.json")
RECOVERY_EVENT   = os.path.expanduser("~/.openclaw/guardian/recovery_event.json")
CHECK_INTERVAL   = 30  # 每 30 秒執行一次自癒校對

# ─── 被守護的資產路徑 ────────────────────────────────────────────────────────
OPENCLAW_CONFIG  = os.path.expanduser("~/.openclaw/openclaw.json")
GATEWAY_PLIST    = os.path.expanduser("~/Library/LaunchAgents/ai.openclaw.gateway.plist")
DOT_ENV          = os.path.expanduser("~/.openclaw/.env")
MODELS_JSON      = os.path.expanduser("~/.openclaw/agents/main/agent/models.json")
AUTH_PROFILES    = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")

GATEWAY_PORT     = 18792
GATEWAY_REVIVE_COOLDOWN = 120 

# ─── 核心認證金鑰 (守護目標) ──────────────────────────────────────────────────
# 這裡儲存系統應有的正確 API Key，用於自動修復
TARGET_API_KEY = "AQ.Ab8RN6LFQjb5LQYxUfDn41Dsu-31Ii0ZWi3GEB5ENw4asExkyw"
ALLOWED_ORIGINS = [
    "http://127.0.0.1:18789", "http://127.0.0.1:18791", "http://127.0.0.1:18792",
    "http://localhost:18789", "http://localhost:18791", "http://localhost:18792",
    "http://192.168.0.68:18789", "http://192.168.0.68:18791",
    "http://192.168.196.11:18789", "http://192.168.196.11:18791"
]

# ─── 工具 ───────────────────────────────────────────────────────────────────
def log(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {message}"
    print(entry)
    try:
        os.makedirs(os.path.dirname(GUARDIAN_LOG), exist_ok=True)
        with open(GUARDIAN_LOG, "a") as f:
            f.write(entry + "\n")
    except Exception: pass

def record_event(action: str, detail: str):
    try:
        event = {"ts": datetime.now().isoformat(), "action": action, "detail": detail, "status": "healed"}
        with open(RECOVERY_EVENT, "w") as f:
            json.dump(event, f, indent=2)
    except Exception: pass

# ─── 自癒核心 1：設定檔自癒 ─────────────────────────────────────────────────
def patch_openclaw_json():
    """檢查並修補 openclaw.json 的 allowedOrigins"""
    try:
        if not os.path.exists(OPENCLAW_CONFIG): return
        with open(OPENCLAW_CONFIG, "r") as f:
            config = json.load(f)
        
        changed = False
        gateway = config.setdefault("gateway", {})
        ui_settings = gateway.setdefault("controlUi", {})
        existing_origins = ui_settings.get("allowedOrigins", [])
        
        # 檢查是否有任何 target origin 遺失
        for origin in ALLOWED_ORIGINS:
            if origin not in existing_origins:
                existing_origins.append(origin)
                changed = True
        
        if changed:
            ui_settings["allowedOrigins"] = existing_origins
            with open(OPENCLAW_CONFIG, "w") as f:
                json.dump(config, f, indent=2)
            log("🔧 [自癒] 已修復 openclaw.json 的 allowedOrigins 白名單")
            return True
    except Exception as e: log(f"❌ [自癒] 修復 openclaw.json 失敗: {e}")
    return False

# ─── 自癒核心 2：Plist 環境變數自癒 ───────────────────────────────────────────
def patch_gateway_plist():
    """檢查並修補 ai.openclaw.gateway.plist 中的 API Keys"""
    try:
        if not os.path.exists(GATEWAY_PLIST): return False
        with open(GATEWAY_PLIST, "r") as f:
            content = f.read()
        
        # 檢查是否存在金鑰字串
        if TARGET_API_KEY not in content:
            log("🔧 [自癒] 偵測到 Plist 環境變數遺失，開始執行正規表達式修復...")
            # 這是比較暴力的置換方式，確保三個變數都正確
            new_content = content
            keys = ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_AI_API_KEY"]
            for k in keys:
                # 尋找 <key>KEY</key><string>VAL</string>
                pattern = f"<key>{k}</key>\\s*<string>.*?</string>"
                replacement = f"<key>{k}</key><string>{TARGET_API_KEY}</string>"
                new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)
            
            if new_content != content:
                with open(GATEWAY_PLIST, "w") as f:
                    f.write(new_content)
                log("✅ [自癒] Plist 環境變數修復完成")
                return True
    except Exception as e: log(f"❌ [自癒] 修復 Plist 失敗: {e}")
    return False

# ─── 自癒核心 3：三層金鑰同步自癒 ───────────────────────────────────────────
def sync_all_agent_keys():
    """確保 .env, models.json, auth-profiles.json 全部使用 TARGET_API_KEY"""
    try:
        changed = False
        # 1. .env
        if os.path.exists(DOT_ENV):
            with open(DOT_ENV, "r") as f: env_data = f.read()
            if TARGET_API_KEY not in env_data:
                # 簡單的全域置換
                lines = []
                for line in env_data.split("\n"):
                    if "API_KEY=" in line:
                        prefix = line.split("=")[0]
                        lines.append(f"{prefix}={TARGET_API_KEY}")
                    else: lines.append(line)
                with open(DOT_ENV, "w") as f: f.write("\n".join(lines))
                changed = True
        
        # 2. models.json
        if os.path.exists(MODELS_JSON):
            with open(MODELS_JSON, "r") as f: m_data = json.load(f)
            p = m_data.get("providers", {})
            for provider in ["google", "google-ai"]:
                if p.get(provider, {}).get("apiKey") != TARGET_API_KEY:
                    p.setdefault(provider, {})["apiKey"] = TARGET_API_KEY
                    changed = True
            if changed:
                with open(MODELS_JSON, "w") as f: json.dump(m_data, f, indent=2)

        # 3. auth-profiles.json
        if os.path.exists(AUTH_PROFILES):
            with open(AUTH_PROFILES, "r") as f: a_data = json.load(f)
            prof = a_data.get("profiles", {})
            for p_name in ["google:default", "google-ai:default"]:
                if prof.get(p_name, {}).get("key") != TARGET_API_KEY:
                   prof.setdefault(p_name, {})["key"] = TARGET_API_KEY
                   changed = True
            if changed:
                with open(AUTH_PROFILES, "w") as f: json.dump(a_data, f, indent=2)

        if changed: log("🔧 [自癒] 已同步三層 Agent 金鑰架構")
        return changed
    except Exception as e: log(f"❌ [自癒] 金鑰同步失敗: {e}")
    return False

# ─── 監控與修復行為 ─────────────────────────────────────────────────────────
def check_gateway_alive() -> bool:
    try:
        result = subprocess.run(["lsof", "-i", f":{GATEWAY_PORT}", "-sTCP:LISTEN"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0 and str(GATEWAY_PORT) in result.stdout
    except Exception: return False

def restart_gateway_service():
    log("🚀 [自癒] 正在重啟 Gateway 服務...")
    try:
        uid = os.getuid()
        subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/ai.openclaw.gateway"], check=True)
        return True
    except Exception: return False

# ─── 全域循環 ────────────────────────────────────────────────────────────────
_last_heal_ts = 0

def monitor_loop():
    global _last_heal_ts
    log("🛡️ System Guardian v4.0 已啟動，自癒防護網已就緒。")
    
    while True:
        try:
            now = time.time()
            heal_needed = False
            
            # 每隔 30 秒執行一次深層環境校對
            # 1. 校對 openclaw.json
            if patch_openclaw_json(): heal_needed = True
            
            # 2. 校對 Plist
            if patch_gateway_plist(): heal_needed = True
            
            # 3. 校對金鑰同步
            if sync_all_agent_keys(): heal_needed = True
            
            # 如果有執行過任何修補，重啟 Gateway 確保生效
            if heal_needed:
                restart_gateway_service()
                record_event("SELF_HEAL_PATCH", "Environmental discrepancy detected and patched automatically.")
            
            # 4. 存活檢查 (舊有的功能)
            if not check_gateway_alive():
                log(f"🚨 [Gateway守護] 偵測到服務離線 (Port {GATEWAY_PORT})")
                uid = os.getuid()
                subprocess.run(["launchctl", "load", "-w", GATEWAY_PLIST], capture_output=True)
                time.sleep(5)
            
        except Exception as e: log(f"❌ 監控異常: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_loop()
