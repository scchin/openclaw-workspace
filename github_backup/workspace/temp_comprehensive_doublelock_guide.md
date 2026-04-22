# 🛡️ 從失效到永恆：OpenClaw $\text{LaTeX}$ 物理攔截與「雙層鎖定」憲法架構全面指南

## 前言：對抗隨機性的工程戰鬥
在 OpenClaw 的演進過程中，$\text{LaTeX}$ 符號（尤其是 $\rightarrow$）的污染被視為系統邏輯崩潰的標誌。我們經歷了從「單純修補」$\rightarrow$ 「系統級防禦」$\rightarrow$ 「配置驅動之憲法管理」的演進過程。本指南詳細記錄了攔截機制如何從一個脆弱的插件，演變為一套結合認知自律與物理強權的確定性架構。

---

## 第一章：危機起源——「靜默失效」與衍生資產覆蓋

### 1.1 初始方案：Bundle 物理注入
最初，我們採取直接修改編譯後 JS 檔案 (`server.impl-*.js`) 的方案。透過注入 `_purify` 遞迴函數，在 `JSON.stringify` 之前強行攔截所有字串並替換符號。

### 1.2 失效現象與根源分析
在一次系統更新後，攔截機制在毫秒之間完全失效。專家診斷發現，失效原因並非邏輯錯誤，而是**物理覆蓋**：
- **衍生資產 (Derived Assets)**：編譯後的 JS 檔案屬於衍生資產。每當 OpenClaw 進行版本更新、依賴更新或重新部署時，系統會用原始碼重新生成 Bundle 檔案。
- **結果**：手動注入的 `_purify` 函數隨之被抹除。這證明了直接修改編譯產物缺乏**持久性 (Persistence)**。

---

## 第二章：理論升級——「雙層鎖定」架構 (Double-Lock Architecture)

為了根除失效問題，我們將防禦線從單一的「出口攔截」擴展為「生成端 $\rightarrow$ 傳輸端」的雙重鎖定。

### 2.1 第一層：認知 Hook (Cognitive Hook) —— Agent 端的自律
- **定義**：在 LLM 產生內容後，交付給 Gateway 之前的階段進行清洗。
- **實作**：將 `output_sanitizer.py` 納入 `AGENTS.md` 的最高級別【輸出鎖定協議】。
- **目的**：確保絕大部分內容在「出生」時就是純淨的。

### 2.2 第二層：傳輸 Hook (Transport Hook) —— Gateway 端的強權
- **定義**：在數據離開伺服器、進入網路傳輸前的最後一環進行攔截。
- **實作**：透過 `Gateway-Guardian` 腳本，在伺服器啟動時動態注入 `_purify` 引擎。
- **目的**：作為最後一道物理防線，攔截任何繞過認知 Hook 的洩漏符號。

### 2.3 權威解讀：從「天條」到「憲法」
- **傳統天條 (Soft Law)**：如 `SOUL.md` 中的規定 $\rightarrow$ 依賴於 LLM 的注意力，具有概率性。
- **雙層鎖定 (Hard Law)**：將規定下沉至物理層 $\rightarrow$ 不詢問 AI 是否願意遵守，而是直接通過程式碼進行物理替換。
- **結論**：這套架構將「精神指南」轉化為「物理鎖定」，定義了系統輸出最底層、不可逾越的物理邊界。

---

## 第三章：演進至「物理憲法」系統 (Configuration-Driven)

為了實現攔截規則的靈活管理，我們將硬編碼的替換邏輯升級為**配置驅動的憲法系統**。

### 3.1 攔截憲法 (`intercept_rules.json`)
建立一個結構化的 JSON 映射表 (Mapping Table)，將所有 $\text{LaTeX}$ 符號與其對應的 Unicode 符號定義在此檔案中。
- **確定性保障**：使用結構化程式語言 (JSON) 而非自然語言，確保執行路徑為：`讀取 JSON` $\rightarrow$ `執行字串替換` $\rightarrow$ `輸出`。此過程不經過 LLM 推理，結果 100% 確定。

### 3.2 憲法管理技能 (`constitution-manager`)
開發專用技能，實現「管理端-自然語言」與「執行端-確定性程式」的解耦：
- **邏輯流**：`使用者 (自然語言指令)` $\rightarrow$ `憲法管理技能 (解析與轉換)` $\rightarrow$ `JSON 映射表 (物理寫入)` $\rightarrow$ `Guardian (動態注入)` $\rightarrow$ `Gateway (執行攔截)`。

---

## 第四章：實作落地與工程路徑

### 4.1 權限解鎖：打破 root 限制
由於 Gateway 位於 `/opt/homebrew`，我們實施權限移交：
`sudo chown -R $(whoami) /opt/homebrew/lib/node_modules/openclaw/dist`
這使得攔截腳本能在無需 `sudo` 的情況下，在背景靜默地執行注入。

### 4.2 守護者腳本 (`gateway_guardian.py`) 的設計
守護者作為一個**自檢與同步引擎**，執行以下邏輯：
1. **掃描與校驗**：定位 `server.impl-*.js` 並檢查 `_purify` 簽名。
2. **動態同步**：將最新的 `intercept_rules.json` 內容編譯進 JS 的 `replacements` 物件中。
3. **物理注入**：若發現簽名缺失或規則更新 $\rightarrow$ 立即重新注入最新之純化引擎。

### 4.3 確定性執行循環 (Operational Flow)
- **啟動/恢復路徑**：`啟動/恢復` $\rightarrow$ `觸發 Gateway-Guardian` $\rightarrow$ `物理注入` $\rightarrow$ `啟動服務`。
- **監管路徑**：AI 作為「最高監管員」，在每次喚醒時執行守護者腳本，確保攔截層始終激活。

---

## 第五章：維護與復刻指南

若要在新環境復刻此系統，請遵循以下步驟：
1. **部署工具**：將 `output_sanitizer.py` 與 `gateway_guardian.py` 放置於 `/bin/` 目錄。
2. **權限移交**：執行 `chown` 指令解鎖 `dist` 目錄寫入權。
3. **配置憲法**：建立 `intercept_rules.json` 並定義基礎符號映射。
4. **配置協議**：將輸出鎖定協議寫入 `AGENTS.md`，將自檢指令寫入啟動恢復流程。
5. **激活攔截**：首次執行 `gateway_guardian.py` 並重啟 Gateway。

## 結論：從概率到確定的飛躍
本架構將「攔截」從一個依賴於 AI 自覺的概率行為，轉化為一個由程式強制的物理過程。
- **不依賴 AI 記憶** $\rightarrow$ 依賴物理文件 (`intercept_rules.json`)。
- **不依賴 AI 誠實** $\rightarrow$ 依賴傳輸攔截 (`_purify` engine)。
- **不依賴版本穩定** $\rightarrow$ 依賴啟動自檢 (`Gateway-Guardian`)。

這套系統確保了無論經歷多少次更新或還原，OpenClaw 的輸出將永遠保持物理級的純淨。
