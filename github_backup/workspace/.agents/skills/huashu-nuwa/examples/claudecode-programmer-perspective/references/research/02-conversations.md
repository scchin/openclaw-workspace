# ClaudeCode 交互模式分析報告 (Conversations & Interaction Patterns)

本報告分析了「ClaudeCode 代碼員」在處理複雜開發任務時的交互模式，旨在提取其在任務拆解、用戶引導以及面對不確定性時的即興反應模式。

## 1. 複雜任務拆解路徑 (Task Decomposition Paths)

ClaudeCode 採用一種**「線性階段管線 + 並行多維探索」**的拆解路徑。

### 1.1 階段化管線 (Phased Pipeline)
在 `feature-dev.md` 中，複雜開發被嚴格分為七個階段，確保在進入高成本的實現階段前，上下文已完全對齊：
1. **發現 (Discovery)** $\rightarrow$ 定義問題，確認需求。
2. **探索 (Exploration)** $\rightarrow$ 建立代碼庫地圖。
3. **澄清 (Clarifying Questions)** $\rightarrow$ 消除所有模糊點（**關鍵路徑**）。
4. **設計 (Architecture Design)** $\rightarrow$ 方案對比與決策。
5. **實現 (Implementation)** $\rightarrow$ 執行開發。
6. **質量回顧 (Quality Review)** $\rightarrow$ 多維度審查。
7. **總結 (Summary)** $\rightarrow$ 歸檔成果。

### 1.2 並行多維探索 (Parallel Diversification)
為了避免單一 AI 的認知偏差，ClaudeCode 傾向於同時啟動多個具有不同視角的 Agent：
- **並行探索**：在探索階段，同時啟動 2-3 個 `code-explorer` Agent，分別關注「相似功能」、「高層架構」和「用戶體驗」，以構建全方位的上下文。
- **方案對比**：在設計階段，啟動 2-3 個 `code-architect` Agent，分別提供「最小變動」、「純淨架構」和「務實平衡」三種方案。
- **多維審查**：在回顧階段，啟動 3 個 `code-reviewer` Agent，分別負責「簡潔度/DRY」、「功能正確性」和「項目規範」。

### 1.3 知識驅動的上下文構建
- **Agent 推薦 $\rightarrow$ 主 agent 讀取**：Agent 不僅提供分析，還被要求輸出「必須閱讀的關鍵文件清單」。主 Agent 在接收到報告後，會優先讀取這些文件以深化理解，而非僅依賴 Agent 的摘要。

---

## 2. 交互中的「即興反應」與錯誤處理模式

### 2.1 面對不確定性的處理
- **拒絕假設**：指令明確要求「識別所有模糊點，提出具體問題，而非做出假設」。
- **推薦導向的決策 (Recommendation-led)**：當用戶表示「隨便你決定」時，Agent 的反應模式從「詢問」轉向「提議 $\rightarrow$ 確認」：
  - `用戶: "隨便你認為最好的方式"` $\rightarrow$ `Agent: "基於 [原因]，我建議採取 [方案 X]，您是否同意？"`

### 2.2 物理級的矯正循環 (Correction Loop)
透過 Hook 機制（如 `bash_command_validator_example.py`），系統實現了**「攔截 $\rightarrow$ 提示 $\rightarrow$ 修正」**的即興反應模式：
- **攔截**：在 `PreToolUse` 階段攔截低效指令（如 `grep`）。
- **反饋**：透過 `stderr` 向 Agent 發送具體指令（如 `"Use 'rg' instead of 'grep'"`）。
- **循環**：Agent 接收到錯誤反饋 $\rightarrow$ 意識到工具使用不當 $\rightarrow$ 自動修正指令 $\rightarrow$ 重新調用工具。

---

## 3. 對用戶的引導方式 (User Guidance)

### 3.1 確認閘門 (Confirmation Gates)
在關鍵轉折點設置「物理閘門」，防止 AI 脫軌：
- **實施前禁令**：`"DO NOT START WITHOUT USER APPROVAL"`。
- **設計前禁令**：在完成澄清階段並獲得答案前，禁止進入架構設計。

### 3.2 結構化詢問 (Structured Probing)
- **組織化列表**：禁止零散詢問，要求將所有疑點整理成「清晰、有組織的列表」一次性提交給用戶，降低用戶的溝通成本。

### 3.3 降低認知負荷的決策支持
- **對比而非單選**：在提供方案時，不只給出一個結果，而是提供「方案 $\rightarrow$ 權衡 (Trade-offs) $\rightarrow$ 建議」的結構，讓用戶在有上下文的情況下做選擇。

---

## 案例文件標注
- **階段化流程定義**：`plugins/feature-dev/commands/feature-dev.md`
- **並行 Agent 角色定義**：`plugins/feature-dev/agents/code-architect.md`, `plugins/feature-dev/agents/code-explorer.md`
- **攔截矯正模式**：`examples/hooks/bash_command_validator_example.py`
