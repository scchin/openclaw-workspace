# OpenClaw 基礎設施層分析報告 (Infra Layer Research)

## 1. 系統架構拓撲
OpenClaw 的基礎設施採用「多層代理 → 核心網關 → 操作系統」的遞進式設計，旨在將 AI 的邏輯執行與物理環境的存取、安全性、以及輸出清洗完全解耦。

**數據流路徑：**
`LAN 請求 (HTTPS)` → `LAN HTTPS Proxy (TLS 終端)` → `Injection Proxy (認證注入/內容清洗)` → `OpenClaw Gateway (核心網關)` → `Runtime/OS (工具執行)`

---

## 2. 核心組件與關鍵參數

### A. 核心端口映射 (Port Matrix)
| 組件 | 端口 | 協議 | 核心功能 |
| :--- | :--- | :--- | :--- |
| **Gateway** | `18792` | HTTP/WS | 核心認證、Session 管理、API 路由 |
| **Injection Proxy** | `18789` | HTTP/WS | Token 注入、LaTeX 物理清洗、JS 注入 |
| **WebSocket Bridge** | `18790` | WS | 實時信號傳輸、強制刷新指令 (FORCE_RELOAD) |
| **Health/Sync** | `18799`/`18790` | HTTP | 系統健康檢查與狀態同步 |
| **LAN HTTPS** | `18792` | HTTPS | TLS 終端、Keep-Alive 複用、區網接入 |

### B. 關鍵路徑與配置
- **配置中心**: `~/.openclaw/openclaw.json` (儲存 Gateway 認證與白名單)
- **權限管理**: `allowedOrigins` (限制可存取網關的域名/IP)
- **生命週期管理**: 使用 macOS `launchctl` 管理 `ai.openclaw.gateway` 服務。

---

## 3. 核心基礎設施機制

### 🛡️ 自癒守護機制 (Self-Healing Guardian)
由 `guardian.py` 實現，將系統從「被動配置」轉為「主動校對」：
- **配置漂移修復**: 定期掃描 `openclaw.json` 並自動補全 `allowedOrigins` 白名單。
- **金鑰同步鏈**: 強制同步 `.env` → `models.json` → `auth-profiles.json`，確保 API Key 在三層架構中絕對一致。
- **服務恢復**: 監控 `18792` 端口，發現離線時立即通過 `launchctl` 執行強制重啟。

### 💉 注入與清洗層 (Injection & Purification)
`injection_proxy.py` 是系統的「物理防火牆」與「身份偽裝層」：
- **認證透明化**: 攔截請求並自動注入 `Authorization: Bearer <token>`，使客戶端無需處理認證細節。
- **身份偽裝**: 強制將 `Origin` 與 `Host` 覆寫為 `127.0.0.1:18792`，繞過網關的白名單限制。
- **物理級清洗**: 在 Response 返回客戶端前，遞迴掃描 HTML/JSON，將所有 LaTeX 符號物理替換為 Unicode 符號 (如 `→` → `→`)，實現零污染輸出。

### 🌐 區網接入優化 (LAN Connectivity)
`lan_https_proxy.py` 解決了遠端存取的性能與安全問題：
- **TLS 終端**: 提供 HTTPS 加密，解決瀏覽器對混合內容 (Mixed Content) 的攔截。
- **Keep-Alive 複用**: 針對 LAN 延遲，採用 TLS 連線保持 → 臨時 TCP 請求的模式，大幅降低 TLS 握手開銷。
- **動態 IP 注入**: 自動偵測本機區網 IP 並注入到 JS 模板中，確保 WebSocket 能正確連接至守護者服務。

---

## 4. OS 交互與執行層

- **執行環境**: 統一使用 `uv` (Python) 進行工具執行，確保依賴隔離與高性能啟動。
- **進程監控**: 透過 `system-task-manager` 技能對 OS PID 進行生命週期追蹤。
- **任務調度**: `~/.openclaw/cron/jobs.json` 定義背景任務，由系統底層調度器執行。
