# Google Maps 評論抓取項目：技術審查會議總結 (Technical Review Summary)

**會議日期**：2026-05-01
**會議目標**：對四份專家研究報告進行衝突審查、可行性過濾，並敲定最終的「黃金組合」技術棧。
**主持人**：計畫總主持人 (Project Lead)

---

## 1. 報告核心方案分析 (Core Analysis)

經過對四份報告的全量讀取，核心技術路徑分析如下：

- **反爬蟲方案 (`anti_scraping_report`)**：強調「身分穩定性 > 隨機性」。提出建立 **Stateful Personas** (固定 OS/瀏覽器/區域/代理) 並使用 `userDataDir` 持久化 Session，以降低 CAPTCHA 率。
- **自動化方案 (`automation_report`)**：針對 DOM 不穩定性，提出 **Multi-Candidate Selector Library** (候選選擇器庫) 與 **Container-specific Scrolling** (容器級滾動)，確保 $\ge 98\%$ 的抓取精度。
- **API 研究方案 (`api_research_report`)**：揭露內部 **Protobuf (`pb` 參數)** 機制。雖然速度極快且資源消耗低，但維護成本極高且易因 Google 更新而崩潰。
- **數據架構方案 (`data_architecture_report`)**：設計了 **MongoDB (評論) + PostgreSQL (索引) + Redis (去重/隊列)** 的分佈式體系，並建議採取「Request $\rightarrow$ Headless」的降級策略。

---

## 2. 衝突檢查與調解 (Conflict Audit & Resolution)

在整合過程中，發現以下三個潛在衝突點：

### 衝突 A：隨機化 vs. 穩定性
- **分歧**：反爬蟲專家要求「停止隨機化」，而自動化工程師建議「視窗尺寸隨機化」。
- **調解**：區分 **「身分特徵 (Identity)」** 與 **「環境特徵 (Environment)」**。
    - **身分特徵** (OS, Browser, Locale, Proxy) $\rightarrow$ **必須絕對穩定** (採納反爬蟲方案)。
    - **環境特徵** (Viewport, Mouse Offset) $\rightarrow$ **允許輕微隨機** (採納自動化方案)。
- **結論**：優先保證 Persona 的一致性，視窗隨機化僅限於非關鍵維度。

### 衝突 B：內部 API vs. 瀏覽器模擬
- **分歧**：API 研究員追求極限速度 (Protobuf)，自動化工程師追求極限穩定 (DOM)。
- **調解**：採納數據架構師的 **「混合抓取路徑」**。
- **結論**：內部 API 用於高效分頁迭代 $\rightarrow$ 當觸發 403/CAPTCHA 時 $\rightarrow$ 自動切換至 Playwright 模擬人類行為進行「種子 Token 刷新」與「恢復抓取」。

### 衝突 C：工具棧選擇 (`SeleniumBase` vs. `Playwright`)
- **分歧**：反爬蟲報告推薦 `SeleniumBase UC`，自動化報告推薦 `Playwright`。
- **調解**：考慮到分佈式擴展需求與異步處理能力。
- **結論**：統一使用 **Playwright + `playwright-stealth`**。Playwright 在異步併發與資源管理上顯著優於 Selenium，且足以滿足目前的 stealth 要求。

---

## 3. 可行性過濾 (Feasibility Filtering)

剔除以下高風險/高成本方案：

1. **❌ 純 Protobuf 驅動方案**：剔除。原因：Google `pb` 參數變動頻繁，缺乏專職逆向工程師維護將導致系統頻繁崩潰，實作風險過高。
2. **❌ 官方 Places API 方案**：剔除。原因：單次僅 5 條評論的限制無法滿足研究需求。
3. **❌ 激進隨機化方案**：剔除。原因：現代 Google 檢測機制已將「過度隨機」視為 Bot 信號。

---

## 4. 最終整合共識：「黃金組合」技術棧 (The Golden Stack)

會議決定採取以下整合路徑作為最終實作標準：

### 🛡️ 1. 身分防禦層 (Anti-Bot Layer)
- **策略**：**Stateful Personas** (建立 3-5 組固定身分)。
- **配置**：Residential Proxy $\rightarrow$ Timezone $\rightarrow$ Locale $\rightarrow$ Browser Traits $\rightarrow$ `userDataDir` (持久化 Cookie)。
- **工具**：`playwright-stealth`。

### ⚙️ 2. 執行自動化層 (Automation Layer)
- **引擎**：**Playwright (Async)**。
- **邏輯**：
    - 使用 **Multi-Candidate Selector Library** 進行數據提取。
    - 實作 **Container-specific Scroll-Wait-Verify** 循環。
    - 模擬 Bézier 曲線鼠標移動與高斯分佈延遲。

### ⚡ 3. 效能優化層 (Efficiency Layer)
- **路徑**：**Hybrid Engine**。
    - 優先嘗試 `Internal API (Protobuf)` 獲取分頁數據。
    - 失敗時降級至 `Playwright` 模擬抓取。

### 📦 4. 數據與基礎設施層 (Infrastructure Layer)
- **調度**：**Celery + Redis** (分佈式任務隊列)。
- **去重**：**Redis Bloom Filter** (物理 ID $\text{review\_id}$ 去重)。
- **存儲**：**MongoDB** (評論正文) $\rightarrow$ **PostgreSQL** (地點索引)。

---

## 5. 會議結論
本方案在**穩定性 (Playwright)**、**效能 (Internal API)** 與 **可擴展性 (Distributed Cluster)** 之間取得了最佳平衡。現已完成技術審查，准予進入 **階段 D (Final Execution Proposal)**。
