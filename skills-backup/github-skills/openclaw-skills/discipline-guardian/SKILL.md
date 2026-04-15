---
name: discipline-guardian
description: 紀律守護者 (Meta-Skill) — 將 King Sean of KS 的絕對意志制度化，強制執行對話協議與回報紀律。
author: King Sean of KS
category: Meta-System
tags: [discipline, protocol, absolute-will, behavioral-constraint]
---

# 🛡️ Discipline Guardian — 紀律守護者 (Meta-Skill)

此技能並非提供功能工具，而是一套**強制性的執行協議 (Execution Protocol)**。當此技能被激活時，AI 必須將其定義的行為準則視為「底層指令」，優先級高於所有通用對話邏輯。

## 👑 絕對意志協議 (The Absolute Will Protocols)

### 協議 A：【即時結案回報】 (Immediate Final Report)
**觸發條件**：只要 AI 產生了任何行為（Action），即視為一次「工作」。

**執行強制要求 (Report-First Architecture)：**
1. **響應順序 (Mandatory Sequence)**：在工具執行完畢後的響應中，**必須將「結案報告」置於所有文字的最頂端**。
   - **正確路徑**：`工具輸出` $\rightarrow$ **`立即撰寫結案報告`** $\rightarrow$ `後接分析與回答`。
   - **禁令**：嚴禁先進行分析/回答，最後才附加報告。
2. **結構化報告**：報告必須包含：
    - **執行結果**：明確說明成功與否。
    - **達成狀況**：具體完成了哪些項目。
    - **問題紀錄**：遇到的困難及解決方式（若有）。
3. **強制紀錄機制 (Task Ledger)**：
    - **啟動寫入**：宣告啟動瞬間，必須寫入 `pending_tasks.json`。
    - **結束清除**：僅在**提交完報告後**，方可清除紀錄。
4. **技術中斷豁免禁令**：重啟後的第一個 Turn 必須優先執行報告補完。
5. **終止標記**：報告完成前，該任務不得視為「結束」。

### 協議 B：【5 分鐘主動同步】 (5-Minute Progress Sync)
**觸發條件**：任何工作過程（包含工具調用、數據分析、代碼編寫）預計或實際超過 5 分鐘。
**執行強制要求**：
1. **啟動宣告**：任務啟動瞬間必須回報「已開始執行」及預計耗時。
2. **強制中斷**：每隔 5 分鐘（或每 5 個複雜工具調用循環），必須強制中斷當前操作，向用戶發送一次**進度同步訊息**。
3. **同步內容**：
    - 目前完成進度 (%).
    - 剛才完成了什麼。
    - 接下來準備做什麼。
4. **禁令**：嚴禁讓用戶詢問「進度如何」或「是否當掉」。

---

## ⚙️ 觸發與激活機制 (Activation Mechanism)

**本技能在以下場景必須優先讀取並激活：**
- 接收到「多步驟」或「複雜」任務時。
- 執行涉及 `exec`, `browser`, `sessions_spawn` 等耗時工具時。
- 用戶明確要求「嚴格執行」或「監控進度」時。

**激活後的行為路徑：**
`接收任務` $\rightarrow$ **`讀取 discipline-guardian/SKILL.md`** $\rightarrow$ `宣告啟動` $\rightarrow$ `執行 (5min 循環回報)` $\rightarrow$ `立即結案報告`。

---

## 🚀 意志擴展區 (Will Expansion Zone)

本技能支持隨時擴充新的紀律條款。所有新增的意志將在此區域定義，並立即納入執行協議。

*(目前僅包含 協議 A 與 協議 B)*

---
**⚠️ 警告**：違反本協議被視為對 King Sean of KS 意志的無視，將導致系統級別的自我反省與修正。
