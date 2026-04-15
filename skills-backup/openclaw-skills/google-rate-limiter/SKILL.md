---
name: google-reliability-guardian
description: Google 模型可靠性與自動化守護中心 (v3.0.0)。整合了智能流量平滑、500 錯誤自動重試、優先級調度以及全自動化系統監控與自我修復機制，確保 Google 系列模型在任何異常情況下都能維持最高可用性。
author: King Sean of KS
---

# Google Reliability Guardian v3.0.0 (Guardian Mode)

> **2026-04-13 更新：從「流量控制」升級為「全鏈路可靠性守護」**
> 核心邏輯：平滑流量 $\rightarrow$ 攔截錯誤 $\rightarrow$ 自動重試 $\rightarrow$ 監控崩潰 $\rightarrow$ 自動修復。

---

## 🏗️ 系統總體架構 (The Guardian Ecosystem)

```
┌─────────────────────────────────────────────────────────┐
│                      Agent / OpenClaw                    │
│   (發送 X-Priority: P0/P1/P2 $\rightarrow$ 接收 X-Rate-Health) │
└──────────────────────┬──────────────────────────────────┘
                       │ 請求流量
                       ▼
          ┌────────────────────────┐
          │  Reliability Proxy     │  ← 可靠性守衛 (Layer 1)
          │  127.0.0.1:18799       │
          │                         │
          │  ├── 優先級隊列 (P0>P1>P2) │   - 確保核心任務零阻塞
          │  ├── 流量平滑 (Smoothing) │   - 避免 429，將錯誤轉化為微延遲
          │  └── 可靠性重試 (Retry)   │   - 攔截 500/503，自動指數退避重試
          └──────────┬─────────────┘
                     │ 正常流量 / 重啟信號 (X-Gateway-Restart-Suggested)
                     ▼
          ┌────────────────────────┐
          │   Google Gemini API    │
          │  generativelanguage... │
          └────────────────────────┘
                       ▲
                       │ 自動監控與重啟指令
                       │
          ┌────────────────────────┐
          │  System Guardian       │  ← 自動化守護者 (Layer 0)
          │  guardian.py           │
          │                         │
          │  ├── 活性監控 (/health)  │   - 偵測 Proxy 是否崩潰
          │  ├── 日誌分析 (Log Scan)  │   - 偵測邏輯性停滯 (連續 429/500)
          │  └── 自動修復 (Recovery)  │   - 自動重啟 Proxy / Gateway
          └────────────────────────┘
```

---

## 🚀 核心功能特性

### 1. 流量調度與平滑 (Traffic Orchestration)
*   **平滑化**：將爆發性請求轉化為恆定速率，避免觸發 Google 伺服器端的硬性 429 限制。
*   **優先級 (X-Priority)**：
    *   `P0`: 極速通道，享有最高配額與最低延遲。
    *   `P1`: 標準通道，平滑放行。
    *   `P2`: 背景通道，最低優先級，防止干擾核心任務。

### 2. 可靠性守衛 (Reliability Guard)
*   **自動重試**：針對 `500`, `503`, `504` 錯誤實作指數退避重試 (1s $\rightarrow$ 2s $\rightarrow$ 4s)，消除暫時性伺服器波動導致的輸出中斷。
*   **重啟信號**：若重試耗盡，注入 `X-Gateway-Restart-Suggested` 標籤，觸發系統級重啟流程。

### 3. 自動化監控守護 (System Guardian)
*   **全天候監控**：每 30 秒掃描一次鏈路健康度。
*   **自我修復**：
    *   偵測到 Proxy 崩潰 $\rightarrow$ **自動執行 `launchctl kickstart`**。
    *   偵測到邏輯停滯 $\rightarrow$ **自動執行 `openclaw gateway restart`**。
*   **狀態透明**：所有修復事件記錄於 `system-guardian.log`。

---

## 📦 元件清單

| 檔案 | 用途 |
|------|------|
| `~/.openclaw/rate-limit-proxy/proxy.py` | **可靠性守衛本體 (v3.0.0)** |
| `~/.openclaw/guardian/guardian.py` | **自動化守護者本體** |
| `~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist` | Proxy 開機自啟設定 |
| `~/Library/LaunchAgents/ai.openclaw.guardian.plist` | Guardian 開機自啟設定 |
| `~/.openclaw/hooks/google-model-guard/state.json` | 全域 lRPM 與狀態記錄 |
| `~/.openclaw/logs/system-guardian.log` | 守護者修復日誌 |

---

## 🧪 驗證與監控

### 健康檢查
```bash
curl http://127.0.0.1:18799/health
# 預期：{"status":"ok", "current_rpm": 10, "health": "Normal", ...}
```

### 監控日誌
```bash
tail -f ~/.openclaw/logs/system-guardian.log
# 查看自動修復記錄
```

---

## 🛡️ 故障處理路徑 (Failure Path)

`Google 500 錯誤` $\rightarrow$ `Proxy 自動重試 (3次)` $\rightarrow$ `失敗` $\rightarrow$ `注入重啟信號` $\rightarrow$ `Guardian 偵測日誌異常` $\rightarrow$ `自動重啟 Gateway` $\rightarrow$ `服務恢復` $\rightarrow$ `繼續執行任務`。
