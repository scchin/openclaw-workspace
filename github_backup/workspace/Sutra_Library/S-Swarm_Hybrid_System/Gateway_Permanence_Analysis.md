# 🛡️ Gateway 物理攔截失效分析與永久化實作方案 (Expert Interpretation)

## 1. 失效根源分析：資產覆蓋 (Asset Overwrite)
**專家診斷**：本次失效並非邏輯錯誤，而是典型的**「衍生資產與原始碼脫節」**問題。

- **機制分析**：之前的攔截機制是直接修改編譯後的 Bundle 檔案 (`server.impl-*.js`)。在 Node.js 的現代開發流程中，這些檔案屬於「衍生資產 (Derived Assets)」。
- **觸發原因**：每當 OpenClaw 進行版本更新、依賴庫更新或執行 `npm install` 等操作時，系統會重新從原始碼編譯或下載最新的 Bundle 檔案 → **原本注入的 `_purify` 函數被物理覆蓋** → 攔截層瞬間消失。
- **結論**：直接修改編譯後的 JS 屬於「手術式修補」，雖然快速，但缺乏**持久性 (Persistence)**。

---

## 2. 永久化實作方案：從「靜態修補」轉向「動態注入」
要實現真正的永久化，必須將攔截邏輯從「檔案本身」移至「啟動流程」。

### 2.1 核心思路：啟動時注入 (Boot-time Injection)
不再試圖維護一個「永遠不變的檔案」，而是建立一個**「永遠存在的注入機制」**。

**方案：實作 `Gateway-Guardian` (網關守護者) 腳本**
- **邏輯**：創建一個輕量級的 Python/Shell 腳本，將其掛載至系統啟動鏈 (例如 `launchd` 或 `S-Swarm` 的啟動序號中)。
- **執行路徑**：
  `啟動 Gateway` → `觸發 Guardian 腳本` → `掃描 server.impl-*.js` → `檢查是否包含 _purify 簽名` → `若缺失 → 立即物理注入` → `啟動服務`。
- **效果**：即使 Bundle 檔案被覆蓋 100 次，Guardian 也能在每次啟動前將攔截邏輯「強行補回」。

---

## 3. Hook 系統能否取代此機制？ (深度解讀)
**專家解答**：**可以取代，但必須區分「認知 Hook」與「傳輸 Hook」。**

目前我們在 `S-Swarm` 中使用的 `output_sanitizer.py` 屬於 **「認知 Hook (Cognitive Hook)」**：
- **運作層級**：在 LLM 產生答案後 → 交付給 Gateway 之前。
- **缺陷**：它依賴於 Agent 的「自覺」去調用。如果 Agent 在某次對話中跳過了 Hook，LaTeX 就會洩漏。

而 `Gateway 攔截` 屬於 **「傳輸 Hook (Transport Hook)」**：
- **運作層級**：在數據離開伺服器 → 進入網路傳輸之前的最後一環。
- **優勢**：它是**最後一道防線**。無論 Agent 是否調用 Hook，所有數據在傳輸前都會被強制純化。

### 🚀 最終建議：建立「雙層鎖定」架構 (Double-Lock Architecture)
為了達到 100% 的確定性，不應選擇其一，而應將兩者結合：

1. **第一層：強制認知 Hook (Agent-side)**
   - 將 `output_sanitizer.py` 定義為所有 Agent 的**強制輸出插件** → 確保大部分內容在生成階段即純淨。
2. **第二層：永久傳輸 Hook (Gateway-side)**
   - 實作上述的 `Gateway-Guardian` 啟動注入機制 → 確保任何意外洩漏的 LaTeX 在傳輸前被物理抹除。

**總結**：透過 **「Agent 端的自律 → Gateway 端的強權」**，我們能將攔截機制從「依賴外部方式」轉化為系統內生的物理特性。
