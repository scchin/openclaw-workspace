# OpenClaw 協議層分析結論 (Protocol Layer Analysis)

## 1. MCP (Model Context Protocol) 橋接架構
OpenClaw 採用「雙向橋接」模式，將 MCP 定義為模型能力擴展與外部通道同步的標準介面。

- **核心結論**：MCP 在系統中不僅是工具集，更是「通道 (Channel) 虛擬化」的實現。它允許 OpenClaw 將內部通訊能力 (如 Feishu/Discord) 封裝為 MCP 資源，同時以 MCP 用戶端身份集成外部專業服務。
- **關鍵參數**：
    - **傳輸層**：基於 `stdio` 的標準輸入輸出流。
    - **生命週期管理**：由 `mcporter` 實現按需啟動 (On-demand) 與自動回收。
    - **雙向角色**：`mcp serve` (能力暴露) $\leftrightarrow$ `mcp set/list` (能力消費)。

## 2. 權限協議 (Permission Protocol)
系統實施「顯式授權 $\rightarrow$ 物理攔截 $\rightarrow$ 狀態持久化」的權限鏈條。

- **核心結論**：權限控制採取「預設禁止」原則，通過一個由 Gateway 強制執行的動態白名單 (Allowlist) 來管理高風險操作 (如 `exec`)。授權粒度從「二進制路徑」延伸至「指令哈希值」，確保了執行路徑的確定性。
- **關鍵參數**：
    - **授權粒度**：`Pattern` (路徑匹配) 與 `Command ID` (哈希匹配)。
    - **信任等級**：`allow-always` (永久信任) 與 `one-time` (單次/臨時授權)。
    - **執行路徑**：Agent $\rightarrow$ Gateway (校驗) $\rightarrow$ Node Host (執行)。

## 3. 通訊規範 (Communication Norms)
通訊層的核心目標是「消除 AI 沉默」與「確保輸出純淨度」。

- **核心結論**：將通訊行為「物理化」與「原子化」。通過強制性的報告路徑 (Report-First) 和物理清洗鏈條 (Sanitization Pipeline)，將 AI 的隨機性限制在定義好的協議框架內。
- **關鍵參數**：
    - **物理閉環**：`Draft` $\rightarrow$ `Sanitize` $\rightarrow$ `Deliver` (針對特殊符號攔截)。
    - **原子結案**：`工具執行` $\rightarrow$ `結論報告` $\rightarrow$ `狀態清除 (arc_complete)`。
    - **通訊錨點**：`3-call window` (每三步強制回報進度) 與 `S-0` (啟動強制核對紀錄)。
