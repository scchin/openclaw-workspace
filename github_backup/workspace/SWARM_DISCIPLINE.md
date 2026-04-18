# SWARM_DISCIPLINE.md — 多代理協同紀律 (Protocol D)

本文件定義了 OpenClaw 在執行多代理並行任務時的最高行為準則。本協議之優先級與 `discipline-guardian` 同級，屬於系統硬鎖定指令。

## 🛡️ 核心禁令：禁止共享寫入 (No Shared Writes)

在任何 Swarm 任務中，**絕對禁止**多個子代理 (Sub-agents) 同時寫入同一個文件。
- **原因**：共享寫入會導致上下文熵增、信息覆蓋以及合成時的認知噪音。
- **判定**：凡是未經 `swarm-governor` 分配之路徑的寫入行為，均視為嚴重違規。

## ⚙️ 強制執行路徑 (The Hard-Lock Path)

所有多代理任務必須遵循以下物理閉環路徑 $\rightarrow$ 否則禁止發送：

1. **初始化**：必須調用 `swarm-governor init` $\rightarrow$ 獲取 `TASK_ID`。
2. **分發**：必須調用 `swarm-governor dispatch` $\rightarrow$ 為每個 Agent 分配唯一路徑。
3. **寫入驗證 (Interception)**：
   - 在每次執行 `write` 操作前 $\rightarrow$ **必須調用 `swarm_integrity_checker.py`**。
   - 驗證指令：`python3 scripts/swarm_integrity_checker.py --id [TASK_ID] --path [TARGET_PATH]`。
   - **攔截機制**：若 Checker 返回 `CRITICAL VIOLATION` $\rightarrow$ **立即中止任務** $\rightarrow$ 刪除錯誤文件 $\rightarrow$ 重啟隔離流程。
4. **合成與摧毀**：
   - 必須調用 `swarm-governor finalize` $\rightarrow$ 執行高純度合成 $\rightarrow$ **物理刪除** 臨時目錄。

## 📋 違規處置
若偵測到繞過 `swarm-governor` 直接寫入共享文件的行為：
- **立即自省**：停止所有子代理執行。
- **物理清理**：強制刪除污染的共享文件。
- **重新部署**：強制重新執行 $\rightarrow$ 必須從 `init` 步驟重新開始。
