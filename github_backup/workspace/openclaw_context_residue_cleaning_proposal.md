# 【OpenClaw 上下文殘留清理與優化綜合執行提案】 (v1.0)

## 0. 執行摘要 (Executive Summary)
本提案旨在解決 OpenClaw 系統中因「對話殘留紀錄」與「系統殘留錯誤」導致的上下文膨脹、響應遲緩及邏輯崩潰問題。透過整合【上下文衛生】、【會話生命週期】與【錯誤恢復】三大維度研究，我們將上下文管理從簡單的「文本拼接」升級為**「主動式狀態記憶體管理系統」**。

**核心目標**：
- **極小化 Token 消耗**：透過語義剪枝與分層儲存，減少 40% 以上的冗餘上下文。
- **消除狀態污染**：實作原子級重置，杜絕錯誤狀態在 Session 間洩漏。
- **提升響應速度**：減少 LLM 處理噪聲的時間，提升首字延遲 (TTFT) 與邏輯正確率。

---

## 1. 核心物理管線：偵測 $\rightarrow$ 清理 $\rightarrow$ 重置 $\rightarrow$ 對齊 (DCRA Pipeline)

我們將三個維度的研究融合成一套自動化的物理執行鏈條，確保系統在任何時刻都處於「純淨狀態」。

### Step 1: 偵測 (Detect) $\rightarrow$ 噪聲識別
- **物理實現**：部署 `NoiseRegistry` 偵測器。
- **邏輯**：
    - **模式匹配**：實時掃描 `Traceback`, `SyntaxError`, 及 LaTeX 污染符號 $\$$。
    - **熵值監控**：偵測輸出中出現大量重複符號或亂碼的「熵突變」片段。
    - **冗餘判定**：若同一-狀態卡-在 3 輪內重複出現 $\ge 5$ 次 $\rightarrow$ 標記為冗餘垃圾。

### Step 2: 清理 (Clean) $\rightarrow$ 物理剔除
- **物理實現**：實作 `ContextSieve` (上下文篩子)。
- **邏輯**：
    - **靜默替換**：將標記為 `ERROR` 的長文本塊替換為短標記 `[System Error Recovered: <Summary>]`。
    - **結構化壓縮**：將重複的 JSON Key 或模板轉換為列式儲存 (Columnar Form)，僅保留變量。
    - **分層回收**：根據注意力權重 (SAGE) 剔除對當前 Query 貢獻度低於閾值的 Token 區塊。

### Step 3: 重置 (Reset) $\rightarrow$ 狀態回溯
- **物理實現**：實作 `Session-Wall` 與 `Checkpoint Manager`。
- **邏輯**：
    - **原子級重置**：偵測到「邏輯崩潰」時，物理刪除所有 Current Session Token $\rightarrow$ 從最近一個有效的 `Checkpoint` 恢復。
    - **邊界截斷**：切換任務標籤時，強制截斷對話流，僅注入結構化摘要 (`summary.md`)。
    - **需求分頁**：將大文件/長 Log 移至 `/workspace/sessions/<id>/pages/` $\rightarrow$ 視窗內僅保留 Page ID。

### Step 4: 對齊 (Align) $\rightarrow$ 記憶校準
- **物理實現**：執行 `Re-alignment Trigger`。
- **邏輯**：
    - **記憶橋接**：清理後插入隱藏指令：`"Note: Noise cleaned. Current focus: [Target]."` $\rightarrow$ 消除記憶斷層。
    - **狀態快照更新**：強制更新一次 `AGENT_STATUS` $\rightarrow$ 確保模型知道目前處於哪個正確步驟。

---

## 2. 系統模組定義 (System Modules)

| 模組名稱 | 負責功能 | 物理實作路徑 |
| :--- | :--- | :--- |
| **Context-Sieve** | 實時 Token 級過濾與結構化壓縮 | `src/context/sieve.py` |
| **Session-Wall** | 邊界定義、快照管理與原子重置 | `src/session/wall.py` |
| **CGC-Engine** | 定期全量掃描、分層記憶轉移 | `src/gc/engine.py` |
| **NoiseRegistry** | 錯誤特徵庫與熵值分析 | `config/noise_registry.json` |

---

## 3. 實作路線圖 (Implementation Roadmap)

### ⚡ 第一階段：快速突破 (Quick-Win) $\rightarrow$ [ 1-2 週 ]
- **目標**：立即消除 LaTeX 與 Traceback 污染，降低基礎 Token 消耗。
- **動作**：
    1. 部署 `NoiseRegistry` $\rightarrow$ 實作基於 Regex 的物理替換算子。
    2. 實作 `ContextCompressor` $\rightarrow$ 對結構化 JSON 數據進行列式壓縮。
    3. 引入「技能按需掛載」 $\rightarrow$ 解決技能注入導致的上下文膨脹。

### 🛠️ 第二階段：結構升級 (Structural) $\rightarrow$ [ 3-5 週 ]
- **目標**：實現狀態可控，杜絕跨 Session 錯誤洩漏。
- **動作**：
    1. 構建 `session_state_manager` $\rightarrow$ 實現任務單元後的 State Snapshot。
    2. 實作 `Atomic Reset` 接口 $\rightarrow$ 支持從 Checkpoint 精準恢復。
    3. 建立 `Session-Wall` $\rightarrow$ 實施強制截斷與結構化摘要同步。

### 🚀 第三階段：性能飛躍 (Evolution) $\rightarrow$ [ 6 週+ ]
- **目標**：實現工業級的「虛擬內存」上下文管理。
- **動作**：
    1. 實作 `Context-Paging` $\rightarrow$ 將長輸出物理分頁儲存於磁碟。
    2. 部署 `CGC-Engine` $\rightarrow$ 實施基於 DAG 關係的自動垃圾回收。
    3. 引入 `SAGE` 注意力權重過濾 $\rightarrow$ 實現真正的主動衛生系統。

---

## 4. 驗證指標 (Verification Metrics)

| 指標 | 衡量方式 | 目標值 |
| :--- | :--- | :--- |
| **上下文壓縮率** | $\frac{\text{清理後 Token}}{\text{原始 Token}}$ | $\le 60\%$ (針對長任務) |
| **恢復成功率** | $\frac{\text{原子重置後恢復正確}}{\text{總崩潰次數}}$ | $\ge 95\%$ |
| **噪聲殘留率** | 輸出中 LaTeX/Traceback 殘留次數 | $0$ |
| **響應速度提升** | 首字延遲 (TTFT) 比較 | $\downarrow 30\% \sim 50\%$ |

## 5. 結案聲明
本提案已整合【上下文衛生】、【會話生命週期】與【錯誤恢復】三方專家之研究成果，通過總主持人之物理可行性核對。該方案將 OpenClaw 的上下文管理從「被動堆疊」轉化為「主動治理」，是提升系統穩定性與效率的必經之路。

**提案狀態：[ READY FOR EXECUTION ]**
