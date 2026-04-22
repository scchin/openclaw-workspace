# OpenClaw Gateway 深度技術指南 (2026.4.18 終極版)
## 四層金鑰鎖定、區網 HTTPS 鏈路修復與 WebSocket 穩定性 SOP

> **修訂說明**：本文件整合了 2026.4.18 修復過程中的核心發現，解決了 API 金鑰自動跳回、區網 1006 斷線以及埠口衝突等實戰問題。旨在提供一套「一鍵配置、長期穩定」的終極方案。

---

## 一、 四層金鑰鎖定：徹底解決「自動跳回舊金鑰」

OpenClaw 具備強大的環境恢復機制，僅修改 `.env` 會導致金鑰在服務重啟時被還原。必須執行「四層同步」。

### 1.1 第一層：系統啟動項 (根源修復)
**檔案路徑**：`~/Library/LaunchAgents/ai.openclaw.gateway.plist`
這是 macOS 啟動服務時的權威環境變數源頭。
- **修改點**：搜尋 `EnvironmentVariables` 區塊，替換 `GEMINI_API_KEY` 與 `GOOGLE_API_KEY`。

### 1.2 第二層：環境變數基底
**檔案路徑**：`~/.openclaw/.env`
- **修改點**：替換所有 `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `GOOGLE_AI_API_KEY`。

### 1.3 第三層：Agent 認證配置
**檔案路徑**：`~/.openclaw/agents/main/agent/auth-profiles.json`
- **修改點**：替換 `google:default` 與 `google-ai:default` 的 `key` 欄位。

### 1.4 第四層：LLM 模型定義檔
**檔案路徑**：`~/.openclaw/agents/main/agent/models.json`
- **修改點**：替換 `google-ai` 節點下的 `apiKey`。

### 1.5 物理鎖定 (不可略過)
完成上述四層修改後，必須執行物理鎖定（防止 Guardian 或 Sidecar 覆寫）：
```bash
chflags uchg ~/Library/LaunchAgents/ai.openclaw.gateway.plist
chflags uchg ~/.openclaw/.env
chflags uchg ~/.openclaw/agents/main/agent/*.json
```

---

## 二、 區網連線修復：從 1006 斷線到穩定訪問

當出現 `disconnected (1006): no reason` 時，代表 WebSocket 鏈路在握手階段被切斷。

### 2.1 埠口隔離架構 (Port Binding)
為避免 IP 衝突，必須強制隔離綁定地址：
- **Gateway (核心)**：綁定在 `127.0.0.1:18792` (不可佔用廣播地址)。
- **Injection Proxy (注入口)**：監聽在 `*:18789`。
- **LAN HTTPS Proxy (加密終端)**：監聽在 `LAN_IP:18792`。

**`openclaw.json` 修改**：
```json
"gateway": {
  "bind": "loopback", // 強制 loopback 或 127.0.0.1
  "port": 18792
}
```

### 2.2 WebSocket 握手標頭校準
`injection_proxy.py` 必須具備標頭自動修正能力，防止多層代理導致的通訊崩潰。
**核心修正邏輯**：
```python
if is_websocket:
    # 強制標頭唯一性，避免重複注入
    clean_headers.append("Connection: Upgrade")
    clean_headers.append("Upgrade: websocket")
```

---

## 三、 全自動服務召回與重啟腳本 (SOP)

為了確保修復生效，必須按照「徹底清場 -> 核心啟動 -> 代理層疊」的順序。

### 3.1 終極重啟腳本
將以下指令整合進您的管理工具：
```bash
# 1. 強力清場
pkill -9 -f openclaw
pkill -9 -f guardian
pkill -9 -f injection_proxy
pkill -9 -f lan_https_proxy

# 2. 核心召回
launchctl kickstart -kp gui/$(id -u)/ai.openclaw.gateway
sleep 3

# 3. 注入層召回
launchctl kickstart -kp gui/$(id -u)/com.openclaw.injection-proxy
sleep 2

# 4. 區網層召回 (最外層)
launchctl kickstart -kp gui/$(id -u)/com.openclaw.lan-https-proxy
```

---

## 四、 常見故障快速診斷

| 錯誤訊息 | 原因 | 解決方案 |
|---|---|---|
| `disconnected (1006)` | Proxy 標頭遺失或埠口衝突 | 檢查 `injection_proxy.py` 的 `Connection: Upgrade` 設定 |
| `Status 401: Unauthenticated` | 金鑰被 .plist 覆寫 | 檢查第一層啟動項並執行 `uchg` 鎖定 |
| `Address already in use` | Gateway 搶佔了區網 IP | 修改 `openclaw.json` 將 `bind` 設為 `loopback` |
| `LLM Error 500 / 404` | 模型 ID 錯誤或 Google API 故障 | 在 `models.json` 中更換為 `gemini-1.5-pro` 交叉驗證 |

---

## 五、 長期維護建議
1. **更新金鑰前**：先執行 `chflags nouchg` 解鎖所有檔案。
2. **區網變動後**：檢查 `lan_https_proxy.py` 內的 `LAN_BINDINGS` 是否包含新的 IP 位址。
3. **穩定性核心**：始終保持 `ai.openclaw.gateway` 的順位最先啟動。

*本指南為 OpenClaw 系統可靠性工程的核心文件。*
