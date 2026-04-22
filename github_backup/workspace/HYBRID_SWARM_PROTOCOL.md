# 🛠️ 混合增強型 Swarm 強制執行協議 (HYBRID_SWARM_PROTOCOL)

本文件為 OpenClaw 系統之最高級別協同規範。凡啟動「多 Agent / Swarm」模式之任務，必須 100% 遵循本協議之物理路徑，禁止任何形式的隨機優化或簡化。

## 1. 物理基礎設施 (Physical Infrastructure)
所有任務必須在 `~/.openclaw/workspace/swarm_env/` 下運行。
- **隔離區 (Isolation)**：每個 Agent 必須擁有獨立的 `git worktree`。
- **信箱 (Mailbox)**：所有進度同步必須通過 `inboxes/{agent_id}/` 之 JSON 文件完成。
- **看板 (Ledger)**：所有狀態變更必須同步至 `tasks.json`。

## 2. 執行生命週期 (Execution Lifecycle)

### 第一階段：初始化 (Initialization)
- **觸發條件**：主代理判定為多 Agent 任務。
- **強制動作**：調用 `swarm_manager.py init <task_id>`。
- **結果**：建立 Worktree $\rightarrow$ 創建信箱 $\rightarrow$ 登記狀態 $\rightarrow$ 輸出物理路徑給子代理。

### 第二階段：執行與同步 (Execution & Sync)
- **子代理規範**：
  - 禁止直接修改主分支。
  - 每完成一個里程碑，必須寫入結構化 JSON 消息至 `inboxes/`。
  - 完結後，必須調用 `swarm_manager.py update <agent> COMPLETED`。
- **主代理規範**：
  - 僅通過 `peek` 結構化信箱監控進度 $\rightarrow$ 降低 Token 消耗。
  - 嚴禁在子代理未提交結論前進行全量文件讀取。

### 第三階段：結案與合成 (Closure & Synthesis)
- **觸發條件**：`tasks.json` 中所有參與 Agent 狀態均為 `COMPLETED`。
- **強制動作**：
  1. 讀取所有 `distilled_report.md`。
  2. 召開「技術審查委員會」進行跨領域會審。
  3. 調用 `swarm_manager.py finalize <task_id>` 執行 `git merge` 並清理 Worktree。

## 3. 禁令 (Prohibitions)
- ❌ 禁止在共享目錄中直接進行多 Agent 並行修改。
- ❌ 禁止使用純文本日誌替代結構化信箱進行進度上報。
- ❌ 禁止在未通過委員會審核前將子代理成果直接併入主線。
