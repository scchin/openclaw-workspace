# 📘 [更新指南] MemPalace 多代理協同治理 (Swarm-Governor)

本指南旨在為系統管理員與開發者提供關於 `swarm-governor` 技能及其連動協議的詳細操作說明。

## 1. 定位與角色
- **技能名稱**：`swarm-governor`
- **定位**：多代理協同的「流量調度員」與「環境清理工」。
- **核心目標**：防止多代理並行任務對長期記憶或共享文件造成噪音污染。

## 2. 標準執行路徑 (The Only Legal Path)

凡涉及啟動 2 個或以上 Sub-agents 的研究任務，**必須**遵循以下步驟：

### Step 1: 空間初始化 (`init`)
- **目的**：在 `sources/swarm_temp/` 下創建唯一任務 ID 目錄。
- **執行**：`python3 scripts/governor.py init --name "任務名稱"`
- **輸出**：記錄 `TASK_ID`。

### Step 2: 路徑分發 (`dispatch`)
- **目的**：為每個 Agent 分配專屬的物理寫入路徑 $\rightarrow$ 杜絕共享寫入。
- **執行**：`python3 scripts/governor.py dispatch --id [TASK_ID] --agent [AGENT_ID] --role "[角色]"`
- **操作**：將獲取的 `.md` 路徑作為唯一寫入目標告知 Sub-agent。

### Step 3: 寫入驗證 (Interception)
- **目的**：物理級攔截違規寫入。
- **執行**：子代理在調用 `write` 前，必須執行 `python3 scripts/swarm_integrity_checker.py --id [TASK_ID] --path [TARGET_PATH]`。
- **結果**：若返回 `CRITICAL VIOLATION` $\rightarrow$ 立即中止 $\rightarrow$ 重新分配路徑。

### Step 4: 合成與摧毀 (`finalize`)
- **目的**：提取結論並徹底清理臨時痕跡。
- **執行**：`python3 scripts/governor.py finalize --id [TASK_ID] --out "[最終結果路徑]"`
- **效果**：合成結果 $\rightarrow$ 刪除臨時目錄 $\rightarrow$ 從 `system-task-manager` 清除紀錄。

## 3. 連動項目說明
- **`system-task-manager`**：負責追蹤 `TASK_ID` 的生命週期。若任務異常中斷，可通過 `list` 查看殘留的 Swarm 任務並手動執行 `finalize`。
- **`discipline-guardian`**：負責監控寫入行為。任何繞過 `swarm-governor` 的並行寫入將被視為嚴重違規 $\rightarrow$ 觸發自省流程。

## 4. 常見問題 (FAQ)
- **Q: 為什麼不能直接寫入一個共享文件？**
  - A: 共享寫入會導致 Token 消耗劇增且結論被噪音掩蓋，導致主 Agent 合成失敗或產生幻覺。
- **Q: 如果 `finalize` 失敗了怎麼辦？**
  - A: 臨時文件將殘留在 `sources/swarm_temp/`，可通過 `TaskID` 手動清理。

---
> 本指南與 `SWARM_DISCIPLINE.md` 共同構成 OpenClaw 的 Swarm 治理標準。
