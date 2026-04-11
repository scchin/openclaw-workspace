---
name: google-rate-limiter
description: 當使用 Google 系列模型（gemma-4-31b-it、gemma-4-26b-a4b-it 等）發生 429 配額錯誤或 500 內部錯誤時，自動重試並提供防止配額用盡的策略。觸發時機：使用 Google 模型、429 錯誤、500 錯誤、API 配額、rate limit、gemma、INTERNAL。
author: King Sean of KS
---

# Google Rate Limiter

> **2026-04-11 更新：新增 Rate-Limit Proxy 實體防火牆（Layer 1）**
> 代理層位於所有 Google API 流量最前端，確保 429 錯誤在 Gateway 之前就被攔截，不再泄漏到 Agent 層。

---

## 🏗️ 架構總覽

```
┌─────────────────────────────────────────────────────────┐
│                      Agent / OpenClaw                    │
└──────────────────────┬────────────────────────────────┘
                       │ 使用 Google 模型
                       ▼
          ┌────────────────────────┐
          │  Rate-Limit Proxy      │  ← 實體防火牆（Layer 1）
          │  127.0.0.1:18799        │
          │                         │
          │  ├── Backoff 阻擋       │   直接回 429，不送往 Google
          │  ├── RPM 滑動窗口       │   10 RPM 上限，超過直接阻擋
          │  └── 格式轉換           │   OpenAI ↔ Google 自動轉換
          └──────────┬─────────────┘
                     │ 正常流量（state=normal, RPM < 10）
                     ▼
          ┌────────────────────────┐
          │   Google Gemini API    │
          │  generativelanguage... │
          └────────────────────────┘
```

**兩層防護機制：**

| 層級 | 組件 | 職責 |
|------|------|------|
| **Layer 1（實體防火牆）** | `rate-limit-proxy/proxy.py` | 所有流量最前端，backoff 直接阻擋，RPM 超限直接阻擋 |
| **Layer 2（ Hook + rate_guard）** | `google-model-guard/handler.ts` + `rate_guard.py` | 模型切換偵測、錯誤紀錄、補全重試 |

---

## 📦 元件清單

| 檔案 | 用途 |
|------|------|
| `~/.openclaw/rate-limit-proxy/proxy.py` | 代理 server（本體） |
| `~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist` | macOS 開機自動啟動 |
| `~/.openclaw/hooks/google-model-guard/state.json` | Guard 狀態（Proxy 讀取） |
| `~/.openclaw/hooks/google-model-guard/handler.ts` | Hook（模型切換偵測） |
| `~/.openclaw/logs/rate-limit-proxy.log` | Proxy 日誌 |
| `~/.openclaw/openclaw.json` | Google provider `baseUrl` 指向 proxy |

---

## 🚀 安裝與部署（單機）

### Step 1｜複製 proxy.py

```bash
mkdir -p ~/.openclaw/rate-limit-proxy
# 將 proxy.py 複製到這個目錄
```

### Step 2｜建立 launchd plist（macOS 開機自動啟動）

```bash
cat > ~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.openclaw.rate-limit-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/KS/.openclaw/rate-limit-proxy/proxy.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/KS/.openclaw/logs/rate-limit-proxy.launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/KS/.openclaw/logs/rate-limit-proxy.launchd.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF
```

> ⚠️ 注意：路徑中的 `/Users/KS/` 需替換成實際的使用者家目錄。

### Step 3｜啟動 proxy

```bash
# 立即啟動（不等開機）
python3 ~/.openclaw/rate-limit-proxy/proxy.py &

# 或透過 launchd 載入
launchctl load ~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist
```

### Step 4｜修改 openclaw.json（讓 Gateway 流量經過 proxy）

在 `models.providers.google.baseUrl` 處：

```json
"google": {
  "baseUrl": "http://127.0.0.1:18799/v1beta",
  "api": "google-generative-ai",
  "models": [
    { "id": "gemma-4-26b-a4b-it", ... },
    { "id": "gemma-4-31b-it", ... }
  ]
}
```

### Step 5｜重啟 Gateway

```bash
# 找到 gateway PID 並重啟
kill $(ps aux | grep '[o]penclaw-gateway' | awk '{print $2}')
# Gateway 會透過 launchd 自動重啟
```

---

## 🖥️ 跨電腦一鍵部署腳本

在**新電腦**上，只需執行以下步驟即可無痛部署全部元件：

### 前提條件
- macOS
- 安裝了 OpenClaw（已設定好 `~/.openclaw/`）
- 有 `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`

### 一鍵部署指令

```bash
# Step 1：建立目錄
mkdir -p ~/.openclaw/rate-limit-proxy

# Step 2：寫入 proxy.py（本技能的本體）
# （見下方 proxy.py 完整內容）

# Step 3：寫入 launchd plist
cat > ~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.openclaw.rate-limit-proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/$(whoami)/.openclaw/rate-limit-proxy/proxy.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$(whoami)/.openclaw/logs/rate-limit-proxy.launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$(whoami)/.openclaw/logs/rate-limit-proxy.launchd.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF

# Step 4：啟動 proxy（不等開機）
python3 ~/.openclaw/rate-limit-proxy/proxy.py &

# Step 5：確認健康檢查
curl http://127.0.0.1:18799/health
# 預期：{"status":"ok","guard_active":true,"guard_status":"normal","proxy_port":18799}

# Step 6：修改 openclaw.json（假設使用 jq）
USER=$(whoami)
python3 - << 'PYEOF'
import json, os
path = os.path.expanduser("~/.openclaw/openclaw.json")
with open(path) as f:
    cfg = json.load(f)
if "models" in cfg and "providers" in cfg["models"] and "google" in cfg["models"]["providers"]:
    cfg["models"]["providers"]["google"]["baseUrl"] = "http://127.0.0.1:18799/v1beta"
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print("✅ openclaw.json 已更新")
else:
    print("⚠️ 未找到 google provider，請手動檢查")
PYEOF

# Step 7：重啟 Gateway（讓設定生效）
kill $(ps aux | grep '[o]penclaw-gateway' | awk '{print $2}')
echo "Gateway 重啟中（約 10 秒）..."
sleep 10

# Step 8：確認一切正常
curl http://127.0.0.1:18799/health
```

---

## 📋 proxy.py 完整內容

（位於 `~/.openclaw/rate-limit-proxy/proxy.py`）

```python
#!/usr/bin/env python3
"""
Google Rate-Limit Proxy — 實體防火牆（Layer 1）
所有通往 Google Gemini 的 API 流量必經之路。
根據 state.json 決定放行或阻擋。
"""

import json, os, re, sys, time, threading, ssl
import urllib.request, urllib.error, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── 設定 ───────────────────────────────────────────────────────────────────
STATE_FILE    = os.path.expanduser("~/.openclaw/hooks/google-model-guard/state.json")
LOG_FILE      = os.path.expanduser("~/.openclaw/logs/rate-limit-proxy.log")
PROXY_PORT    = 18799
AUTH_FILE     = os.path.expanduser("~/.openclaw/openclaw.json")
GOOGLE_BASE   = "https://generativelanguage.googleapis.com/v1beta"

# ─── SSL（Mac Python 3.13 需加此行）────────────────────────────────────────
ssl._create_default_https_context = ssl._create_unverified_context

# ─── 日誌 ───────────────────────────────────────────────────────────────────
def log(entry: dict):
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}) + "\n")
    except Exception:
        pass

# ─── State 讀取 ──────────────────────────────────────────────────────────────
def load_guard_state() -> dict:
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"active": False, "status": "normal", "intervalSecs": 6.0}

def is_backoff(state: dict) -> bool:
    if not state.get("active", False):
        return False
    return state.get("status", "normal") in ("backoff", "emergency")

# ─── RPM 追蹤（滑動窗口 60s）─────────────────────────────────────────────────
class RpmTracker:
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.lock = threading.Lock()
        self.timestamps: list[float] = []
        self._load()

    def _load(self):
        state = load_guard_state()
        now = time.time()
        cutoff = now - 60
        self.timestamps = [t for t in state.get("callTimestamps", []) if t > cutoff]

    def can_proceed(self, target_rpm: int = 10) -> tuple[bool, float]:
        with self.lock:
            now = time.time()
            cutoff = now - 60
            self.timestamps = [t for t in self.timestamps if t > cutoff]
            if len(self.timestamps) < target_rpm:
                return True, 0.0
            oldest = min(self.timestamps)
            wait = max(0.0, 60 - (now - oldest))
            return False, wait

    def record_call(self):
        with self.lock:
            now = time.time()
            cutoff = now - 60
            self.timestamps = [t for t in self.timestamps if t > cutoff]
            self.timestamps.append(now)
            self._save()

    def _save(self):
        try:
            state = load_guard_state()
            state["callTimestamps"] = self.timestamps
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

rpm_tracker = RpmTracker(STATE_FILE)

# ─── API Key 取得 ─────────────────────────────────────────────────────────────
def resolve_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    if key:
        return key
    try:
        raw = open(AUTH_FILE).read()
        for pat in [r'"GEMINI_API_KEY"\s*:\s*"([^"]+)"', r'"GOOGLE_API_KEY"\s*:\s*"([^"]+)"']:
            m = re.search(pat, raw)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""

# ─── 格式轉換（OpenAI ↔ Google）──────────────────────────────────────────────
def transform_request(body: dict, model: str) -> tuple[dict, str]:
    messages = body.get("messages", [])
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        if role == "system":
            role = "user"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    google_model = model.split("/")[-1] if "/" in model else model

    payload = {"contents": contents}
    gen_cfg = {}
    for key, gkey in [("max_tokens", "maxOutputTokens"), ("temperature", "temperature"),
                       ("top_p", "topP"), ("stop", "stopSequences")]:
        if key in body:
            gen_cfg[gkey] = body[key]
    if gen_cfg:
        payload["generationConfig"] = gen_cfg

    return payload, google_model

def transform_response(google_resp: dict, model: str) -> dict:
    candidates = google_resp.get("candidates", [])
    if not candidates:
        raise ValueError(f"Google API 無 candidates: {google_resp}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    usage = google_resp.get("usageMetadata", {})
    return {
        "id": f"gemini-{int(time.time()*1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        }
    }

def error_resp(message: str, code: int = 429) -> dict:
    return {"error": {"message": message, "type": "rate_limit_error", "code": code}}

# ─── 請求處理 ────────────────────────────────────────────────────────────────
def handle_request(method: str, path: str, body: bytes, headers: dict):
    state = load_guard_state()

    # ① Backoff 阻擋
    if is_backoff(state):
        wait = state.get("intervalSecs", 15)
        log({"action": "blocked", "reason": "backoff", "wait": wait})
        return {"status": 429, "content_type": "application/json",
                "body": json.dumps(error_resp(f"API rate limit reached. Try again in {int(wait)}s")).encode()}

    # ② RPM 阻擋
    can_proceed, wait_secs = rpm_tracker.can_proceed(target_rpm=10)
    if not can_proceed:
        log({"action": "blocked", "reason": "rpm_limit", "wait": f"{wait_secs:.1f}s"})
        return {"status": 429, "content_type": "application/json",
                "body": json.dumps(error_resp(f"RPM limit reached. Try again in {int(wait_secs)}s")).encode()}

    # ③ 轉發到 Google
    if "chat/completions" not in path:
        return {"status": 404, "content_type": "application/json",
                "body": json.dumps({"error": {"message": f"Unsupported path: {path}"}}).encode()}

    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        return {"status": 400, "content_type": "application/json",
                "body": json.dumps({"error": {"message": "Invalid JSON body"}}).encode()}

    model = data.get("model", "gemma-4-31b-it")
    payload, google_model = transform_request(data, model)
    api_key = resolve_api_key()
    if not api_key:
        return {"status": 500, "content_type": "application/json",
                "body": json.dumps({"error": {"message": "No Google API key"}}).encode()}

    url = f"{GOOGLE_BASE}/models/{google_model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                  headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_data = json.loads(resp.read().decode())
            openai_resp = transform_response(resp_data, model)
            rpm_tracker.record_call()
            log({"action": "forwarded", "model": google_model, "status": 200})
            return {"status": 200, "content_type": "application/json",
                    "body": json.dumps(openai_resp).encode()}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8")
        if e.code == 429:
            # Google 429 → 更新 state.json 進入 backoff
            try:
                gs = load_guard_state()
                gs["consecutive429"] = gs.get("consecutive429", 0) + 1
                gs["last429Ts"] = time.time()
                if gs["consecutive429"] >= 2:
                    gs["status"] = "emergency"
                    gs["intervalSecs"] = 30
                else:
                    gs["status"] = "backoff"
                    gs["intervalSecs"] = 15
                with open(STATE_FILE, "w") as f:
                    json.dump(gs, f, indent=2)
                log({"action": "429_detected", "consecutive429": gs["consecutive429"]})
            except Exception as ex:
                log({"action": "state_write_error", "error": str(ex)})
            return {"status": 429, "content_type": "application/json",
                    "body": json.dumps(error_resp("API rate limit reached. Please try again later.")).encode()}
        try:
            err_data = json.loads(body_err)
            msg = err_data.get("error", {}).get("message", body_err[:200])
        except Exception:
            msg = body_err[:200]
        return {"status": e.code, "content_type": "application/json",
                "body": json.dumps({"error": {"message": msg}}).encode()}
    except Exception as e:
        log({"action": "proxy_error", "error": str(e)})
        return {"status": 500, "content_type": "application/json",
                "body": json.dumps({"error": {"message": f"Proxy error: {str(e)}"}}).encode()}

# ─── HTTP Server ─────────────────────────────────────────────────────────────
class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        log({"action": "request", "path": self.path, "method": self.command})

    def do_POST(self):
        cl = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(cl) if cl > 0 else b""
        result = handle_request(self.command, self.path, body, dict(self.headers))
        self.send_response(result["status"])
        self.send_header("Content-Type", result["content_type"])
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(result["body"])

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            state = load_guard_state()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "guard_active": state.get("active", False),
                "guard_status": state.get("status", "unknown"),
                "proxy_port": PROXY_PORT
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')

def run_server(port: int):
    srv = HTTPServer(("127.0.0.1", port), ProxyHandler)
    log({"action": "started", "port": port})
    print(f"[RateLimitProxy] 監聽 127.0.0.1:{port}")
    srv.serve_forever()

if __name__ == "__main__":
    run_server(PROXY_PORT)
```

---

## 🧪 驗證與測試

### 快速驗證指令

```bash
# 1. Proxy 運行狀態
ps aux | grep "[p]roxy.py" | grep -v grep

# 2. 健康檢查
curl http://127.0.0.1:18799/health
# 預期：{"status":"ok","guard_active":true,"guard_status":"normal","proxy_port":18799}

# 3. Guard State
cat ~/.openclaw/hooks/google-model-guard/state.json | python3 -m json.tool

# 4. 正常轉發測試
curl -s -X POST http://127.0.0.1:18799/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-31b-it","messages":[{"role":"user","content":"OK"}],"max_tokens":3}'
# 預期：回傳 OpenAI 格式的回應

# 5. Backoff 阻擋測試
python3 -c "
import json
s = {'active':True,'status':'backoff','intervalSecs':15,'consecutive429':1,'callTimestamps':[]}
with open('/Users/KS/.openclaw/hooks/google-model-guard/state.json','w') as f:
    json.dump(s, f)
"
curl -s -X POST http://127.0.0.1:18799/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-31b-it","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
# 預期：{"error":{"message":"API rate limit reached...","code":429}}

# 6. 恢復正常
python3 -c "
import json
s = {'active':True,'status':'normal','intervalSecs':6,'consecutive429':0,'callTimestamps':[]}
with open('/Users/KS/.openclaw/hooks/google-model-guard/state.json','w') as f:
    json.dump(s, f)
"

# 7. 確認 openclaw.json 指向 proxy
grep -A2 '"google":' ~/.openclaw/openclaw.json | grep baseUrl
# 預期："baseUrl": "http://127.0.0.1:18799/v1beta",

# 8. Gateway 狀態
ps aux | grep "[o]penclaw-gateway" | awk '{print "Gateway PID:", $2, "| 正常運行"}'
```

### 查看日誌

```bash
# Proxy 日誌（JSONL）
tail -f ~/.openclaw/logs/rate-limit-proxy.log

# Launchd 日誌
cat ~/.openclaw/logs/rate-limit-proxy.launchd.log
cat ~/.openclaw/logs/rate-limit-proxy.launchd.err.log
```

---

## 🛡️ 阻擋邏輯說明

### 三個阻擋關卡

| 關卡 | 觸發條件 | 行為 |
|------|----------|------|
| **① Backoff 阻擋** | `state.status ∈ {backoff, emergency}` | 直接回 429，不送往 Google |
| **② RPM 阻擋** | 滑動窗口內呼叫數 ≥ 10 RPM | 直接回 429，不送往 Google |
| **③ Google 429 偵測** | Google API 返回 HTTP 429 | 自動寫入 state.json，進入 backoff |

### 狀態 flow

```
normal → (收到 Google 429) → backoff → (15s) → normal
                      ↓
               (短時間第2次) → emergency → (30s) → normal
```

---

## 🔧 常見問題

### Q: proxy 掛了怎麼辦？

```bash
# 方式一：launchd 自動重啟（已有 KeepAlive: true）
# 方式二：手動重啟
python3 ~/.openclaw/rate-limit-proxy/proxy.py &

# 方式三：確認 port 是否被佔用
lsof -i :18799
```

### Q: 如何完全移除 proxy？

```bash
# 停止
launchctl unload ~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist

# 刪除 plist（可選）
rm ~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist

# 將 openclaw.json 改回原本設定
# 將 "baseUrl": "http://127.0.0.1:18799/v1beta" 改回
# "baseUrl": "https://generativelanguage.googleapis.com/v1beta"
```

### Q: 是否適用於其他模型？

目前設計為 Google Gemma 系列專用。若要支援其他 provider，須修改 `transform_request/transform_response` 函式。

---

## 📊 測試報告（2026-04-11）

| 測試項目 | 預期行為 | 結果 |
|----------|----------|------|
| 健康檢查 | `/health` 回傳 `{"status":"ok"...}` | ✅ 通過 |
| 正常轉發 | 流量成功轉發到 Google → 回應正確轉換 | ✅ 通過 |
| Backoff 阻擋 | `status=backoff` 時直接回 429 | ✅ 通過 |
| 恢復放行 | `status=normal` 時正常轉發 | ✅ 通過 |
| RPM 追蹤 | 滑動窗口正確記錄每次呼叫 | ✅ 通過 |
| SSL Mac 修復 | Python 3.13 不報 SSL certificate 錯誤 | ✅ 通過 |
| Launchd 自動啟動 | 開機自動啟動 proxy | ✅ 設定完成 |
| openclaw.json 整合 | Gateway 流量確實經過 proxy | ✅ 驗證完成 |

---

## 🗂️ 相關檔案路徑速查

| 用途 | 路徑 |
|------|------|
| **Proxy 本體** | `~/.openclaw/rate-limit-proxy/proxy.py` |
| **自動啟動 plist** | `~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist` |
| **Guard State** | `~/.openclaw/hooks/google-model-guard/state.json` |
| **Proxy 日誌** | `~/.openclaw/logs/rate-limit-proxy.log` |
| **Launchd stdout** | `~/.openclaw/logs/rate-limit-proxy.launchd.log` |
| **Launchd stderr** | `~/.openclaw/logs/rate-limit-proxy.launchd.err.log` |
| **Proxy 健康檢查** | `http://127.0.0.1:18799/health` |
| **設定檔** | `~/.openclaw/openclaw.json`（`models.providers.google.baseUrl`） |

---

## ⚠️ 維護提醒

1. **更換 API Key**：`~/.openclaw/openclaw.json` 中的 `GEMINI_API_KEY` / `GOOGLE_API_KEY` 改了之後，proxy 會自動讀取（每個 request 重新解析）
2. **不要手動刪除 `state.json`**：RPM 追蹤依賴其中的 `callTimestamps`，刪除後 RPM 計算會歸零但仍正常運作
3. **Proxy 日誌若過大**：可定期 `truncate -s 0 ~/.openclaw/logs/rate-limit-proxy.log`