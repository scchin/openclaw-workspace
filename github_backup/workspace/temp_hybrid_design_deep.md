# 🛠️ 多代理混合協同系統 (S-Swarm) 深度程式設計指南

## 1. 系統核心設計哲學：從「概率」轉向「確定性」
本系統的最高指導原則是：**將 AI 的創造力限制在「內容生成」階段，將系統的穩定性錨定在「流程控制」階段。** 
我們不依賴 LLM 的「自覺」來遵循規範，而是通過物理級的程式攔截（Hooks）與環境隔離，強制 LLM 在定義好的軌道上運行。

---

## 2. 分層架構詳細設計

### 2.1 物理隔離層 (Physical Isolation Layer)
**目標**：杜絕上下文污染與資源競爭。
- **Git Worktree 實作**：
  - 每個啟動的 Agent 不再共享同一個工作目錄，而是通過 `git worktree add` 創建獨立的物理路徑。
  - **優勢**：Agent A 的文件修改不會影響 Agent B，且所有變更都被記錄在獨立的分支中，可隨時回滾或審核。
- **Ledger 狀態機 (`tasks.json`)**：
  - 系統維護一個全局狀態賬本，記錄每個任務的 `TaskID` $\rightarrow$ `AgentID` $\rightarrow$ `Status` (RUNNING/COMPLETED/FAILED) $\rightarrow$ `Branch`。
  - 所有的調度指令必須先經過 Ledger 驗證，確保任務狀態的原子性。
- **物理信箱 (Inbox/Outbox)**：
  - Agent 之間禁止直接通過記憶體傳遞大段文本，而是通過寫入特定的 `/inboxes/[AgentID]/` 目錄。
  - 這將通訊過程「文件化」，使得所有專家協作的過程都具備 100% 的可追溯性（Audit Trail）。

### 2.2 認知調度層 (Cognitive Dispatching Layer)
**目標**：實現高純度的身份注入。
- **認知 DNA 註冊 (`EXPERT_REGISTRY.md`)**：
  - 專家不再是簡單的提示詞，而是一套包含「核心專長」、「認知原型」、「邏輯模式」的結構化數據。
- **動態注入流程 (DED Flow)**：
  1. **特徵匹配**：`nuwa-dispatcher` 分析用戶需求 $\rightarrow$ 匹配 Registry 中的專家條目。
  2. **DNA 提取**：提取該專家的邏輯路徑（例如：第一原理 $\rightarrow$ 物理拆解 $\rightarrow$ 瓶頸定位）。
  3. **權重注入**：將提取的 DNA 作為高權重系統指令注入執行引擎 $\rightarrow$ 強制 AI 切換思考模式。
  4. **身份固化**：通過 `SKILL.md` 限制專家的誠實邊界，防止身份漂移。

### 2.3 攔截與 Hook 系統 (Interception & Hook System)
**目標**：實施物理級的輸出過濾與行為約束。
- **輸出攔截 Hook (`output_sanitizer.py`)**：
  - **位置**：位於 LLM 生成文本與用戶接收文本之間的最後一哩路。
  - **機制**：對所有輸出文本進行正則掃描 $\rightarrow$ 發現任何 `$` 包圍的 $\text{LaTeX}$ 符號 $\rightarrow$ 物理映射為對應的 Unicode 符號（例如 $\rightarrow$ 轉為 `→`）。
  - **特性**：這是確定性的字符串替換，不經過 LLM，因此不存在失效概率。
- **協議攔截 Hook (`purify_output.py`)**：
  - **位置**：專用於「報告」、「證明」、「分析」類的高等級任務。
  - **機制**：強制執行 `草稿` $\rightarrow$ `物理清洗` $\rightarrow$ `證據(Log)輸出` $\rightarrow$ `正文輸出` 的序列。
  - **目的**：防止 AI 進行「口頭承諾」，強制要求提供工具執行的物理證據。
- **狀態同步 Hook (`system-task-manager`)**：
  - **位置**：連接 OS 進程與 AI 認知層。
  - **機制**：定期掃描系統 PID $\rightarrow$ 將物理狀態轉譯為人類語言報告 $\rightarrow$ 注入上下文。

---

## 3. 確定性執行循環 (Deterministic Execution Loop)

一個完整的混合系統任務執行路徑如下：

1. **Dispatch (調度)**：`nuwa-dispatcher` $\rightarrow$ 查詢 `EXPERT_REGISTRY.md` $\rightarrow$ 確定專家陣容。
2. **Isolation (隔離)**：`swarm_manager.py` $\rightarrow$ 創建 Git Worktree $\rightarrow$ 分發任務至 Inbox。
3. **Execution (執行)**：Sub-agents 在隔離區運行 $\rightarrow$ 產出中間結果 $\rightarrow$ 寫入 Outbox。
4. **Audit (審核)**：主代理讀取所有 Outbox $\rightarrow$ 進行交叉比對 $\rightarrow$ 剔除幻覺 $\rightarrow$ 形成草稿。
5. **Interception (攔截)**：`output_sanitizer` $\rightarrow$ 物理清除 $\text{LaTeX}$ $\rightarrow$ 格式校準。
6. **Delivery (交付)**：輸出最終結果 $\rightarrow$ 根據 `pending_tasks.json` 結案 $\rightarrow$ 清理 Worktree。

## 4. 總結：為什麼這能 100% 執行？
本設計將 LLM 視為**「不穩定但高效的計算單元」**，而將 `swarm_manager`、`DED` 與 `Sanitizer` 視為**「穩定的控制電路」**。
- **不依賴 AI 記憶** $\rightarrow$ 依賴物理文件 (Ledger/Inbox)。
- **不依賴 AI 誠實** $\rightarrow$ 依賴物理過濾 (Hooks)。
- **不依賴 AI 穩定** $\rightarrow$ 依賴環境隔離 (Worktrees)。

透過這套設計，我們將 AI 的隨機性徹底封裝，實現了工程級的確定性執行。
