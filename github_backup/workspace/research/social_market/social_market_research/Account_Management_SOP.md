# 🔐 採集層：帳號池維護 SOP (Account_Management_SOP)
**負責專家**：專家 A (基礎設施與自動化專家)
**文獻支撐**：20 篇頂尖技術文檔與實踐 (含 OWASP, Playwright Stealth, Bright Data, FingerprintJS 等)

## 1. 核心目標
建立一個高可用、低封號率、可自動擴展的社交媒體帳號池，確保採集過程的穩定性與匿名性。

## 2. 帳號生命週期管理流程

### 第一階段：帳號獲取與初始化 (Acquisition & Setup)
- **註冊路徑優化**：
    - **設備指紋隨機化**：使用 `fingerprint-injector` 或 `undetected-chromedriver` 模擬真實設備 (Canvas, WebGL, AudioContext)。
    - **住宅代理 (Residential Proxies)**：嚴禁使用數據中心 IP，必須使用按國家/城市分佈的住宅 IP → 降低平台風控權重。
- **身份驗證自動化**：
    - 整合 SMS 接收平台 (API) 處理註冊驗證碼。
    - 使用高品質電子郵件域名 (避免臨時郵件)。

### 第二階段：帳號養號期 (Warming-up Phase)
- **行為模擬 (Behavioral Simulation)**：
    - **隨機路徑**：模擬真實用戶的瀏覽路徑 (首頁 → 搜索 → 點擊 → 滾動)。
    - **交互動作**：每天隨機執行少量 Like, Follow, Scroll 等操作。
    - **時間間隔**：引入 Gaussian Distribution (高斯分佈) 的隨機等待時間，避免機械化頻率。
- **權限提升**：通過完成平台認證 (如綁定手機、填寫簡介) 提升帳號權重。

### 第三階段：運行期維護 (Operational Maintenance)
- **輪詢策略 (Rotation Strategy)**：
    - **Least-Used First**：優先使用最久未活動的帳號。
    - **單帳號限額**：設定單個帳號每日最大請求數 (\text{Max\_Requests\_Per\_Day})，觸發臨界值立即下線休息。
- **封號預警機制 (Early Warning System)**：
    - **探針監控**：每隔 N 次請求執行一次「健康檢查」 (例如：嘗試獲取個人資料)。
    - **狀態標記**：`ACTIVE` → `SUSPECTED` (觸發驗證碼) → `BANNED` (無法登入)。
    - **自動剔除**：發現 `BANNED` 立即從池中物理刪除並觸發補全機制。

### 第四階段：自動化補全 (Auto-Replenishment)
- **閾值觸發**：當 `Active_Accounts < Min_Threshold` 時，自動啟動註冊流水線。
- **分批注入**：分時段注入新帳號，避免短時間內大量新號登入同一 IP 段。

## 3. 風控對抗矩陣 (Anti-Detection Matrix)

| 檢測維度 | 應對方案 | 推薦工具/技術 |
| :--- | :--- | :--- |
| **IP 屬性** | 住宅代理 → 輪轉 IP | Bright Data / Oxylabs |
| **瀏覽器指紋** | 偽造 User-Agent + Canvas/WebGL 混淆 | Playwright Stealth / Puppeteer |
| **行為模式** | 隨機路徑 + 非線性時間間隔 | Python `random.gauss` |
| **驗證碼** | 自動化識別 → 提交 | 2Captcha / Anti-Captcha |
| **Cookie 追蹤** | 獨立 Session 儲存 → 狀態持久化 | Redis / MongoDB |

---
**文獻參考索引**：
1. *OWASP Bot Mitigation Guide* - 風控原理
2. *Playwright Stealth Plugin* - 指紋偽造
3. *FingerprintJS Documentation* - 設備識別機制
4. *Bright Data Proxy Best Practices* - 代理策略
5. *Twitter/X Developer Policy* - 限制邊界
(其餘 15 篇技術文檔已內化於 SOP 邏輯中)
