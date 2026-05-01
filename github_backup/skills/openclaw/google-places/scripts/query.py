#!/usr/bin/env python3
import subprocess, json, sys, os, time

AUTOCLI_BIN = os.path.expanduser("~/.openclaw/bin/autocli")
ADAPTER_DIR = os.path.expanduser("~/.autocli/adapters/google-places")

def reset_system():
    print("🔄 [System] 正在重置 AutoCLI 服務以確保連線穩定...")
    subprocess.run(["killall", "autocli"], capture_output=True)
    # 背景啟動 Daemon
    subprocess.Popen([AUTOCLI_BIN, "--daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

def ensure_adapter(query, pid=None):
    os.makedirs(ADAPTER_DIR, exist_ok=True)
    
    # 搜尋模式
    # 第一步使用 navigate 確保視窗開啟，第二步使用 exec 確保跳轉成功
    search_yaml = f"""
site: google-places
name: search
browser: true
pipeline:
  - navigate: "https://www.google.com"
  - wait: 2000
  - exec: "window.location.href = 'https://www.google.com/maps/search/{query}/'"
  - wait: 10000
  - evaluate: |
      (function(){{
        var items = Array.from(document.querySelectorAll('a[href*="/maps/place/"]'));
        return items.map(el => ({{
          name: el.getAttribute('aria-label') || el.innerText || 'Unknown',
          url: el.href
        }})).filter(x => x.url.includes('place/')).slice(0, 3);
      }})()
  - select: "$item"
"""
    
    # 詳情模式
    detail_yaml = f"""
site: google-places
name: detail
browser: true
pipeline:
  - navigate: "https://www.google.com/maps/place/?q=place_id:{pid}"
  - wait: 8000
  - evaluate: |
      (function(){{
        return {{
          name: document.querySelector('h1')?.innerText || 'N/A',
          address: document.querySelector('button[data-item-id="address"]')?.innerText || 'N/A'
        }};
      }})()
"""
    
    with open(os.path.join(ADAPTER_DIR, "search.yaml"), "w", encoding="utf-8") as f:
        f.write(search_yaml.strip())
    if pid:
        with open(os.path.join(ADAPTER_DIR, "detail.yaml"), "w", encoding="utf-8") as f:
            f.write(detail_yaml.strip())

def run_command(name):
    cmd = [AUTOCLI_BIN, "google-places", name, "--format", "json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        return json.loads(res.stdout)
    except Exception as e:
        # print(f"Error: {e}")
        return None

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "台中燒肉"
    
    # 1. 重置服務
    reset_system()
    
    print(f"🚀 [AutoCLI] 正在啟動 Google Maps 搜尋：{query}")
    print("📢 請確保您的 Chrome 是開啟的，且擴充功能顯示 Connected")
    
    # 2. 生成適配器
    ensure_adapter(query)
    
    # 3. 執行搜尋
    results = run_command("search")
    
    if not results:
        print("❌ 抓取失敗。嘗試執行簡單導航...")
        # 嘗試第二次救援：直接打開網頁
        subprocess.run(["open", "-a", "Google Chrome", f"https://www.google.com/maps/search/{query}/"])
        print("💡 已嘗試強制開啟 Chrome，請查看網頁是否已出現結果。")
        sys.exit(1)
        
    print(f"✅ 成功找到 {len(results)} 間地點！開始抓取詳情...\n")
    
    for item in results:
        url = item.get('url', '')
        try:
            pid = url.split('/place/')[1].split('/')[0]
        except:
            continue
            
        print(f"📍 正在獲取詳情：{item.get('name')}")
        ensure_adapter(query, pid)
        detail = run_command("detail")
        
        if detail:
            d = detail[0] if isinstance(detail, list) else detail
            print(f"[SENSITIVE_TOKEN_HARD_REDACTED]")
            print(f"店名：{d.get('name')}")
            print(f"地址：{d.get('address')}")
            print(f"[SENSITIVE_TOKEN_HARD_REDACTED]\n")
        time.sleep(2)
