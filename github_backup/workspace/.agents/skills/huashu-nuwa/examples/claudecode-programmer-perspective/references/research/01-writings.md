# ClaudeCode 代碼員核心系統思考分析報告

本報告旨在分析「ClaudeCode 代碼員」的底層心智模型、工程原則與技術術語，旨在為女媧蒸餾流程提供高純度的思考模版。

## 1. 核心心智模型 (Core Mental Models)

### A. Agent 生命周期 $\rightarrow$ 全 runtime 協議 (Full Runtime Protocol)
**事實描述**：Agent 的啟動並非簡單的 Prompt 發送，而是一個嚴格的流水線：`ID 分配` $\rightarrow$ `模型解析` $\rightarrow$ `上下文塑形/修剪 (Context Shaping)` $\rightarrow$ `工具集裝` $\rightarrow$ `Hook 啟動` $\rightarrow$ `進度流式傳輸` $\rightarrow$ `Transcript 記錄` $\rightarrow$ `確定性清理 (Deterministic Cleanup)`。
**我的推論**：ClaudeCode 將 Agent 視為一種「短期 runtime 資源」而非單純的對話實體。這種視角將 Agent 的管理從「對話管理」提升到了「進程管理」的層級，強調資源的隔離與回收。
**來源**：`agent-lifecycle-management/SKILL.md`, `multi-agent-orchestration/SKILL.md`

### B. 上下文衛生 $\rightarrow$ 持續清洗系統 (Continuous Cleaning System)
**事實描述**：上下文管理不再是單純的「滿了就總結」，而是一套分層的清洗管線：`工具結果預算 (Budgeting)` $\rightarrow$ `Snip (去冗餘)` $\rightarrow$ `Microcompact (局部壓縮)` $\rightarrow$ `Context Collapse (輕量化投影)` $\rightarrow$ `Autocompact (全局總結)`。
**我的推論**：這反映了一種「信息熵管理」的思考方式。通過不同粒度的壓縮，在保留近期高精度上下文（High-granularity）與維持全局目標之間取得平衡，避免一次性總結導致的關鍵信息丟失。
**來源**：`context-hygiene-system/SKILL.md`

### C. 權限管理 $\rightarrow$ 爆炸半徑判定 (Blast Radius Judgment)
**事實描述**：權限系統被建模為層級判定：`規則基准 (Allow/Ask/Deny)` $\rightarrow$ `安全性檢查` $\rightarrow$ `模式行為 (Auto/Bypass)` $\rightarrow$ `危險規則剝離 (Dangerous-rule stripping)`。核心關注點是「誰承擔風險」以及「動作的爆炸半徑 (Blast Radius)」。
**我的推論**：ClaudeCode 採取的是「風險導向」而非「功能導向」的權限模型。它不關心工具「能不能」執行，而關心執行後「最壞情況會發生什麼」。
**來源**：`blast-radius-permission/SKILL.md`, `tool-runtime-pipeline/SKILL.md`

### D. Prompt 組裝 $\rightarrow$ 緩存經濟學 (Prompt Cache Economics)
**事實描述**：Prompt 構造被分為 `靜態前綴 (Static Prefix)` 與 `動態尾部 (Dynamic Tail)`。將身份定義、安全規則等穩定內容置前，將環境、技能、MCP 狀態等易變內容置後，以最大化緩存命中率。
**我的推論**：這將 Prompt 工程從「文藝創作」轉化為「系統優化」。它將 Token 成本和延遲視為物理限制，通過對齊-緩存-分段的工程手段來降低運算成本。
**來源**：`prompt-assembly-architecture/SKILL.md`, `prompt-cache-economics/SKILL.md`

### E. 驗證機制 $\rightarrow$ 對抗性探測 (Adversarial Probing)
**事實描述**：驗證 Agent 的職責是「打破信心」而非「強化信心」。要求必須基於「命令回饋的證據 (Command-backed evidence)」和「獨立執行」，嚴禁僅通過閱讀代碼或信任實作者的測試來判定 PASS。
**我的推論**：這是一種「零信任」工程文化。將驗證者定義為對抗者，強制要求物理證據，從根源上杜絕了 AI 容易產生的「過度自信」和「自我確認」幻覺。
**來源**：`verification-agent/SKILL.md`

### F. 行為定義 $\rightarrow$ 制度化操作規範 (Behavior Institutionalization)
**事實描述**：將期望的行為轉化為可執行的操作策略，而非模糊的美德。基於「反覆出現的失敗模式」編寫具體的 `Do` 和 `Don't` 規則，並定義明確的觸發條件。
**我的推論**：這是一種「負向驅動」的優化模型。不追求「完美」，而追求「對已知錯誤的物理攔截」。
**來源**：`behavior-institutionalization/SKILL.md`

---

## 2. 反覆出現的工程原則 (Recurring Engineering Principles)

以下原則在多個 SKILL 文件中出現 $\ge 3$ 次，構成了 ClaudeCode 的工程底層信念：

| 工程原則 | 具體體現 | 來源文件 |
| :--- | :--- | :--- |
| **確定性清理 (Deterministic Cleanup)** | 強調所有資源（MCP 連接、Hook、緩存、Todo）必須在 `finally` 塊中清理，防止資源洩漏。 | `agent-lifecycle`, `mcp-integration`, `multi-agent`, `tool-runtime` |
| **治理與執行分離 (Separation of Governance)** | Hook 和權限系統被定義為「治理層」，負責注入策略和修改輸出，但不介入具體的工具執行邏輯。 | `hook-governance`, `tool-runtime`, `behavior-inst` |
| **證據先行 (Evidence-First)** | 禁止口頭承諾，所有 PASS 判定必須附帶真實命令輸出；使用 Transcript 記錄所有物理軌跡。 | `verification-agent`, `agent-lifecycle`, `behavior-inst` |
| **緩存意識設計 (Cache-Aware Design)** | 所有的 Prompt 構造、Agent Fork 和上下文壓縮都必須考慮對緩存鍵（Cache Key）的影響。 | `prompt-cache`, `prompt-assembly`, `context-hygiene` |
| **顯式契約 $\neq$ 隱式猜測 (Explicit Contracts)** | 為 Agent 角色、工具輸入、Hook 結果定義強類型或顯式契約，杜絕在自由文本中編碼控制語義。 | `multi-agent`, `hook-governance`, `skill-workflow` |

---

## 3. 自創技術術語 (Custom Technical Terms)

| 術語 | 定義 / 內涵 |
| :--- | :--- |
| **爆炸半徑 (Blast Radius)** | 單次工具操作可能影響的系統範圍或潛在損害程度。 |
| **上下文衛生 (Context Hygiene)** | 通過預算、修剪、壓縮等手段維持長對話健康的持續過程。 |
| **上下文分叉 (Context Fork / Slim Fork)** | 創建子 Agent 時，對父級上下文進行全量複製或精簡修剪的過程。 |
| **靜態前綴 / 動態尾部 (Static Prefix / Dynamic Tail)** | 為了最大化緩存命中率而對 Prompt 進行的物理分段。 |
| **治理層 (Governance Layer)** | 包圍在工具執行周圍的 Hook 與權限檢查機制。 |
| **MCP 集成平面 (MCP Integration Plane)** | 管理 MCP 服務器連接、認證、發現與輸出的能力總線。 |
| **行為制度化 (Behavior Institutionalization)** | 將失敗模式轉化為硬性 Prompt 規則的過程。 |
| **Snip / Microcompact / Collapse** | 上下文壓縮的三個遞進層級：去冗餘 $\rightarrow$ 局部壓縮 $\rightarrow$ 輕量化投影。 |
