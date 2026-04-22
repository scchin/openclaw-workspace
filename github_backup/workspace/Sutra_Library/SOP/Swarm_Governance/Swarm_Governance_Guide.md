# 📘 [更新指南] MemPalace 多代理協同治理 (Swarm-Governor)

本指南旨在為系統管理員與開發者提供關於 `swarm-governor` 技能及其連動協議的詳細操作說明。

## 1. 定位與角色
- **技能名稱**：`swarm-governor`
- **定位**：多代理協同的「流量調度員」與「環境清理工」。
- **核心目標**：防止多代理並行任務對長期記憶或共享文件造成噪音污染。

## 2. 絕對執行標準：多代理混合協同系統 (S-Swarm Hybrid System)
凡涉及啟動 2 個或以上 Sub-agents 的研究任務，**必須 100% 強制採用「多代理混合協同系統 (S-Swarm Hybrid System)」**。任何其他形式的協同被視為過時且具風險的舊版路徑。

### 2.1 標準執行路徑 (The Only Legal Path)
1. **空間初始化 (`init`)**：
   - **目的**：在 `sources/swarm_temp/` 下創建唯一任務 ID 目錄。
   - **執行**：`python3 scripts/governor.py init --name "任務名稱"`
2. **路徑分發 (`dispatch`)**：
   - **目的**：為每個 Agent 分配專屬的物理寫入路徑 $\rightarrow$ 杜絕共享寫入。
   - **執行**：`python3 scripts/governor.py dispatch --id [TASK_ID] --agent [AGENT_ID] --role "[角色]"`
3. **寫入驗證 (Interception)**：
   - **目的**：物理級攔截違規寫入。
   - **執行**：子代理在調用 `write` 前，必須執行 `python3 scripts/swarm_integrity_checker.py --id [TASK_ID] --path [TARGET_PATH]`。
4. **合成與摧毀 (`finalize`)**：
   - **目的**：提取結論並徹底清理臨時痕跡。
   - **執行**：`python3 scripts/governor.py finalize --id [TASK_ID] --out "[最終結果路徑]"`

## 3. 連動項目說明
- **`system-task-manager`**：負責追蹤 `TASK_ID` 的生命週期。
- **`discipline-guardian`**：負責監控寫入行為。任何繞過 `swarm-governor` 的並行寫入將被視為嚴重違規 $\rightarrow$ 觸發自省流程。

---
> 本指南與 `SWARM_DISCIPLINE.md` 共同構成 OpenClaw 的 Swarm 治理標準。所有協同作業必須遵循 S-Swarm Hybrid System 之規範。
