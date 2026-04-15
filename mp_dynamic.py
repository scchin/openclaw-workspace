#!/usr/bin/env python3
"""
MemPalace Dynamic Search Wrapper
根據系統可靠性狀態 (Reliability Guardian) 自動調整記憶檢索深度。
"""

import sys, json, urllib.request, subprocess, os

# ─── 設定 ───────────────────────────────────────────────────────────────────
PROXY_HEALTH_URL = "http://127.0.0.1:18799/health"
MP_SCRIPT = "/Users/KS/.openclaw/hooks/mempalace-memory/mp"

def get_system_health() -> str:
    """獲取目前系統健康狀態"""
    try:
        with urllib.request.urlopen(PROXY_HEALTH_URL, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return data.get("health", "Normal")
    except Exception:
        return "Critical"

def map_health_to_limit(health: str) -> int:
    """將健康狀態映射為檢索深度 (Limit)"""
    mapping = {
        "Normal": 5,
        "Warning": 3,
        "Critical": 1
    }
    return mapping.get(health, 1)

def main():
    if len(sys.argv) < 2:
        print("Usage: mp-dynamic <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    health = get_system_health()
    limit = map_health_to_limit(health)
    
    print(f"📡 [Dynamic Search] System Health: {health} -> Setting MP_LIMIT to {limit}")
    
    # 使用環境變數 MP_LIMIT 呼叫 mp 腳本
    env = os.environ.copy()
    env["MP_LIMIT"] = str(limit)
    
    try:
        # 使用絕對路徑呼叫 mp 腳本
        result = subprocess.run([MP_SCRIPT, "search", query], env=env, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error executing search: {str(e)}")

if __name__ == "__main__":
    main()
