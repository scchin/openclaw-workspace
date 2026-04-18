# 🛡️ Google Reliability Guardian v3.0.0 終極使用指南
## —— 從「流量控制」進化為「全鏈路自我修復系統」

本文件詳細記錄了 `google-reliability-guardian` 技能的運作原理、系統集成狀態、極限性能表現以及完整的使用指南。本系統旨在徹底解決 Google Gemini API 的 `429 (Rate Limit)` 與 `500 (Internal Error)` 問題，並實現系統級的自動化監控與自我修復。

---

## 📖 1. 技能概述與設計哲學

### 1.1 進化路徑
*   **v1.x (Firewall)**：簡單的 429 攔截 然後 報錯 然後 手動介入。
*   **v2.0.0 (Orchestrator)**：流量平滑化 然後 優先級調度 然後 減少 429 發生。
*   **v3.0.0 (Guardian)**：自動重試 然後 狀態監控 然後 自動重啟 然後 **零手動介入**。

### 1.2 核心定位
*   **定位**：Google API 的可靠性守護者與自動化運維系統。
*   **目標**：實現「輸出不中斷」，將所有 API 異常轉化為自動化修復流程。

---

## ⚙️ 2. 運作原理深度解析

### 2.1 可靠性守衛 (Reliability Guard)
針對伺服器端錯誤 (500, 503, 504) 實作**指數退避重試機制**：
*   **邏輯**：偵測到 500 類錯誤 然後 自動等待 (1s 然後 2s 然後 4s) 然後 重新嘗試。
*   **效果**：消除暫時性伺服器波動導致的系統停滯。
*   **最終指令**：若 3 次重試皆失敗 然後 注入 `X-Gateway-Restart-Suggested: true` 然後 觸發系統級重啟。

### 2.2 流量調度員 (Traffic Orchestrator)
*   **平滑化 (Smoothing)**：將爆發性請求轉化為恆定速率，避免觸發硬性 429 限制。
*   **優先級體系 (Priority)**：
    *   `P0 (Critical)`：最高優先級 然後 快速通道 然後 確保核心對話零阻塞。
    *   `P1 (Standard)`：標準優先級 然後 平滑排隊 然後 正常執行任務。
    *   `P2 (Background)`：最低優先級 然後 限速放行 然後 避免干擾核心流量。
*   **自適應 RPM**：根據 API 回應延遲自動調整 RPM (5 到 15)，主動避開臨界點。

### 2.3 自動化監控守護者 (System Guardian)
獨立於 Proxy 之外的監控進程，負責執行「最後一公里的自我修復」：
*   **活性監控**：每 30 秒檢查一次 `/health` 端點 然後 崩潰時自動執行 `launchctl kickstart` 恢復 Proxy。
*   **日誌分析**：掃描 `rate-limit-proxy.log` 然後 偵測到邏輯性停滯（如連續大量 429/500 異常） 然後 自動執行 `openclaw gateway restart`。
*   **自我恢復**：將「發現停滯 然後 手動提醒 然後 重啟」的流程完全自動化。

---

## 🛠️ 3. 系統元件清單 (Components Map)

| 檔案路徑 | 用途 | 關鍵角色 |
| :--- | :--- | :--- |
| `~/.openclaw/rate-limit-proxy/proxy.py` | **可靠性守衛本體 (v3.0.0)** | 流量平滑、優先級調度、自動重試 |
| `~/.openclaw/guardian/guardian.py` | **自動化守護者本體** | 活性監控、日誌掃描、自動修復 |
| `~/Library/LaunchAgents/ai.openclaw.rate-limit-proxy.plist` | Proxy 開機自啟設定 | 確保守衛始終運行 |
| `~/Library/LaunchAgents/ai.openclaw.guardian.plist` | Guardian 開機自啟設定 | 確保監控始終運行 |
| `~/.openclaw/hooks/google-model-guard/state.json` | 全域 lRPM 與狀態記錄 | 狀態持久化 |
| `~/.openclaw/logs/system-guardian.log` | 守護者修復日誌 | 所有修復事件的審計追蹤 |

---

## 🌐 4. 系統接管與集成狀態

### 4.1 全鏈路路徑
`OpenClaw Gateway` 然後 `Reliability Proxy (18799)` 然後 `Google Gemini API`
$\quad \uparrow$ (監控與重啟) $\leftarrow$ `System Guardian (Background)`

### 4.2 部署細節
*   **設定集成**：`openclaw.json` 指向 `http://127.0.0.1:18799/v1beta`。
*   **自動化啟動**：透過兩個 `launchd` plist 實現開機自啟與崩潰自愈。
*   **多線程處理**：使用 `ThreadingMixIn` 確保緩衝等待期間不會阻塞其他併發請求。

---

## 🛡️ 5. 故障處理路徑 (Failure Path)

本系統將所有故障路徑標準化為自動化流程：

`Google 500 錯誤` 然後 `Proxy 自動重試 (1s 然後 2s 然後 4s)` 然後 `重試耗盡 (失敗)` 然後 `注入 X-Gateway-Restart-Suggested 信號` 然後 `Guardian 偵測日誌異常` 然後 `自動執行 openclaw gateway restart` 然後 `服務恢復` 然後 `繼續執行任務`。

---

## 📈 6. 極限運行效果測試報告

### 6.1 混合爆發測試 (P0/P1/P2)
*   **P0 通道**：**100% 成功率**，展現了絕對優先權。
*   **P1 通道**：**約 80% 成功率**，大部分請求在平滑延遲後成功完成。
*   **P2 通道**：**約 30% 成功率**，成功實現對背景流量的壓制。

### 6.2 崩潰恢復測試
*   **Proxy 崩潰** 然後 守護者偵測 然後 自動重啟 然後 **恢復時間 低於 40s**。
*   **邏輯性停滯** (模擬大量 429) 然後 守護者掃描日誌 然後 自動重啟 Gateway 然後 **恢復時間 低於 60s**。

---

## 🛠️ 7. 使用與維護指南

### 7.1 監控指令
*   **健康狀態檢查**：
    ```bash
    curl http://127.0.0.1:18799/health
    # 預期輸出: {"status":"ok", "current_rpm": X, "health": "Normal", ...}
    ```
*   **監控守護者日誌**：
    ```bash
    tail -f ~/.openclaw/logs/system-guardian.log
    ```

### 7.2 故障排查 FAQ
**Q: 為什麼我的請求突然變慢了？**
A: 這說明系統正在執行「平滑化」或「自動重試」。請檢查 `X-Rate-Health` Header，若為 `Warning` 或 `Critical`，表示系統正在保護 API 額度以防止崩潰。

**Q: 守護者自動重啟了我的網關，我該怎麼辦？**
A: 這代表系統偵測到了嚴重停滯。您無需任何操作，守護者已完成重啟，您可以直接繼續之前的對話，系統會嘗試恢復上下文。

**Q: 如何調整 RPM 上限？**
A: 系統目前採自適應模式。若需強制修改基準值，請修改 `proxy.py` 中的 `baseline_latency`。

---

**文件版本**：v3.0.0 (Reliability Guardian Edition)
**最後更新日期**：2026-04-14
**授權/作者**：King Sean of KS