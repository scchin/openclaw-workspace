# 📘 [開發指南] 系統恢復機制：大統一治理框架 (The Grand Unified Recovery Framework - GURF)

**文件版本**：v1.1.0-Final-Proposal
**狀態**：最終審核版 $\rightarrow$ 等候指令實作
**審核專家**：首席系統架構師 / 穩定性工程專家 / UX 診斷專家 / 系統審計員

---

## 0. 執行前言：從「恐慌修正」到「工程治理」

本框架旨在將系統從 4 月 18 日事故後產生的「恐慌式阻塞恢復」轉化為一套**配置驅動 (Configuration-Driven)** 的智能治理系統。我們不再追求單純的「絕對阻塞」，而是在確保「物理安全」的前提下，極大化「響應效率」。

本指南將原有的「分級響應」、「工具鏈聚合」、「意志整合」三項提案全面融合，確保在不損害任何藏經閣項目意志的前提下，消除系統啟動之沉默期與延遲。

---

## 1. 核心診斷與背景 (The Diagnosis)

### 1.1 效能崩潰分析 (Performance Gap)
- **現象**：簡單查詢 (如：藏經閣列表) 導致 $\approx 60\text{s}$ 的沉默期。
- **物理原因**：執行了 $\approx 13$ 次獨立工具調用 (Round-trip) $\rightarrow$ 導致上下文膨脹 $\rightarrow$ 增加 Token 消耗 $\rightarrow$ 延遲 TTFT。
- **邏輯衝突**：`絕對恢復協議` (要求阻塞) $\text{VS}$ `通訊紀律` (要求回報) $\rightarrow$ 導致 AI 陷入「不能說話但必須執行」的死循環。

### 1.2 治理缺陷分析 (Governance Flaw)
- **過度修正 (Over-correction)**：將「底層網關崩潰」這一極端特例，定義為所有啟動場景的常態路徑。
- **線性包袱 (Linear Burden)**：恢復路徑被寫死在 `AGENTS.md` 的步驟中 $\rightarrow$ 每增加一項安全要求 $\rightarrow$ 增加一個 Step $\rightarrow$ 延遲線性增加。

---

## 2. 統一治理架構 (The Unified Architecture)

本框架將「恢復」定義為一個 ** $\text{Intensity (強度)}$** 可調的動態過程。

### 2.1 智能分流門戶 (Intelligent Gateway)
系統不再採取單一的啟動路徑，而是根據 ** $\text{意圖} + \text{狀態}$** 分流：
- ** $\text{Light-Mode (日常)}$** $\rightarrow$ 觸發：簡單查詢、問候 $\rightarrow$ **目標：極速響應**。
- ** $\text{Standard-Mode (續接)}$** $\rightarrow$ 觸發：恢復 Session、有 `pending_tasks` $\rightarrow$ **目標：任務連續性**。
- ** $\text{Strict-Mode (恢復)}$** $\rightarrow$ 觸發：災難還原、高危操作 $\rightarrow$ **目標：物理絕對安全**。

### 2.2 系統健康註冊表 (System Health Registry, SHR)
將所有「意志結晶」從 SOP 文本轉化為 JSON 配置 (`system_health_registry.json`)。這不僅是配置，更是**統一的治理接口**：
- **模組化**：每個檢查項目 (Task, Gateway, Soul) 成為一個獨立模組。
- **優先級化**：定義 $\text{Priority}$ (1: 核心 $\rightarrow$ 10: 次要)。
- **意志插件化 (Will Plugin)**：定義標準接口，未來新項目只需註冊模組 $\rightarrow$ **無需修改 $\text{AGENTS.md}$ $\rightarrow$ 無需重新定義 SOP**。

### 2.3 聚合執行引擎 (Aggregated Execution Engine)
實作 **「工具鏈聚合 (Tool Aggregation)」** $\rightarrow$ 開發 `system_health_check.py` $\rightarrow$ **一次調用 $\rightarrow$ 全量執行 $\rightarrow$ 單一回報**。
- **物理路徑**：`AGENTS.md` $\rightarrow$ `system_health_check.py` $\rightarrow$ `SHR.json` $\rightarrow$ `執行模組` $\rightarrow$ `返回狀態卡`。
- **效益**：將 $N$ 次工具輪詢 (Round-trip) 降低為 $1$ 次 $\rightarrow$ 預計減少 $\approx 80\%$ 的恢復延遲。

### 2.4 動態反饋環 (Dynamic Feedback Loop)
- **心跳同步**：針對 $\text{Standard/Strict-Mode}$，在聚合執行過程中輸出「半同步狀態卡」 $\rightarrow$ 消除沉默感。
- **直接交付**：針對 $\text{Light-Mode}$，跳過非核心檢查 $\rightarrow$ 直接交付結果。

---

## 3. 實作路徑 (Implementation Roadmap)

### 第一階段：基礎設施建設 (Infrastructure)
1. **定義 $\text{SHR.json}$**：將 $\text{S-0}$ (任務)、$\text{S-1}$ (狀態)、$\text{S-2}$ (人格) 及 $\text{Gateway Guardian}$ 全部模組化。
2. **開發 `system_health_check.py`**：
   - 實作 $\text{Priority}$ 過濾邏輯。
   - 實作單次 Python 進程內的所有 $\text{read/exec}$ 聚合 (Tool Aggregation)。
   - 輸出格式定義為：`{"status": "READY/WARNING/CRITICAL", "details": {...}, "latency": "..."}`。

### 第二階段：觸發邏輯重構 (Logic Refactoring)
1. **修改 `AGENTS.md`【Every Session】**：
   - 刪除原有的 Step 1, 2, 3 阻塞描述。
   - 替換為：`調用 system_health_check.py (強度由意圖分流決定) $\rightarrow$ 根據返回狀態決定是否阻塞 $\rightarrow$ 交付`。
2. **實作意圖分流器**：在啟動的第一時間對 Prompt 進行 $\text{Risk-Level}$ 判定。

### 第三階段：心跳與反饋集成 (Feedback Integration)
1. **集成狀態卡輸出**：在 $\text{Standard/Strict-Mode}$ 時，將聚合器進度實時轉譯為人類語言回報。

---

## 4. 驗證與審計矩陣 (Verification & Audit Matrix)

實作完成後，將由專家小組進行以下對比測試 (Baseline: 2026-04-21 舊版協議)：

| 測試維度 | 測試場景 | 衡量指標 (Metric) | 預期目標 (Target) |
| :--- | :--- | :--- | :--- |
| **響應速度** | 日常查詢 (Sutra List) | TTFT (首字延遲) | $\text{Baseline} \rightarrow \text{Reduction } 90\%$ |
| **運算成本** | 全量恢復 (Strict Mode) | Input Tokens / Tool Calls | $\text{Tool Calls: } 13 \rightarrow 2$ |
| **複雜度** | 新增安全模組 (New Skill) | 修改行數 / 影響範圍 | $\text{SOP 修改} \rightarrow \text{JSON 增加一行}$ |
| **準確率** | 任務續接 (Warm Start) | 任務遺漏率 / 報告完整度 | $\text{Maintain } 100\% \text{ Accuracy}$ |
| **可擴展性** | 增加 5 個自檢項 | 延遲增量 (Latency Delta) | $\text{Near-Zero (due to aggregation)}$ |
| **統一性** | 治理接口驗證 | SHR $\rightarrow$ 聚合 $\rightarrow$ 插件 聯動率 | $\text{100\% 的檢查項均通過 SHR 驅動}$ |
| **資產影響** | 藏經閣項目核對 | 功能可用性 $\text{+}$ 意志繼承度 | $\text{0 損毀, 100\% 意志繼承}$ |

---

## 5. 專家小組分工 (Expert Assignment)

- **首席架構師**：負責 $\text{SHR.json}$ 結構定義與 `AGENTS.md` 邏輯重構。
- **穩定性工程專家**：負責 `system_health_check.py` 的魯棒性開發與物理攔截驗證。
- **UX 診斷專家**：負責「意圖分流」閾值設定與「心跳狀態卡」文案設計。
- **審計員**：負責執行上述驗證矩陣 $\rightarrow$ 產出最終綜合評估報告書。
