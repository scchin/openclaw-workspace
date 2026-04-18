---
name: swarm-governor
description: |
  多代理協同治理者。強制實施「暫存隔離 $\rightarrow$ 階層提煉 $\rightarrow$ 物理清理」的 Swarm 記憶協議。
  防止多代理並行寫入導致的上下文噪音污染，確保長期記憶的純度。
  用途：啟動多代理並行研究、分配隔離路徑、執行最終合成與資源回收。
---

# swarm-governor · 多代理協同治理者

> 「不要信任 AI 的自律，要信任物理路徑的隔離。」

## 核心理念

在多代理協同 (Parallel Swarm) 模式下，最危險的行為是所有 Agent 共同寫入同一個文件。這會導致信息熵激增，使主 Agent 在合成時陷入噪音。

`swarm-governor` 的核心邏輯是 **「隔離 $\rightarrow$ 提煉 $\rightarrow$ 摧毀」**：
1. **隔離 (Isolation)**：為每個任務創建唯一 ID，為每個 Agent 分配獨立的物理寫入路徑。
2. **提煉 (Synthesis)**：僅在所有子任務完工後，由主 Agent 讀取隔離區結果並進行高純度合成。
3. **摧毀 (Purge)**：合成完成後立即物理刪除所有臨時文件，防止系統臃腫。

## 使用方式

### 1. 初始化 Swarm 任務 (`init`)
在啟動多代理研究前，必須首先初始化一個任務空間。
- **指令**：`python3 scripts/governor.py init --name "任務名稱"`
- **輸出**：獲得 `TASK_ID` 與 `DIR`。

### 2. 分配隔離路徑 (`dispatch`)
在 `sessions_spawn` 啟動子代理時，調用此命令為其指定唯一的寫入路徑。
- **指令**：`python3 scripts/governor.py dispatch --id [TASK_ID] --agent [AGENT_ID] --role "[專家角色]"`
- **輸出**：獲得該 Agent 專屬的 `research_output.md` 物理路徑。
- **強制要求**：主 Agent 必須將此路徑作為唯一寫入目標告知子 Agent。

### 3. 執行合成與清理 (`finalize`)
當所有子代理完成任務後，觸發最終的合成與資源回收。
- **指令**：`python3 scripts/governor.py finalize --id [TASK_ID] --out "[最終結果路徑]"`
- **效果**：
    - 自動讀取所有隔離區文件。
    - 將結果合成至指定路徑。
    - **物理刪除** 整個 `TASK_ID` 臨時目錄。

## 強制執行協議 (Hard-Lock)

本技能與 `AGENTS.md` 中的最高指令連動：
- **禁止** 在多代理任務中直接使用共享文件。
- **禁止** 在未調用 `finalize` 前將臨時數據移入 `Sutra_Library`。
- **判定**：任何繞過 `swarm-governor` 的並行寫入行為均視為嚴重違規。

## 物理路徑定義
- **臨時根目錄**：`/Users/KS/.openclaw/workspace/sources/swarm_temp/`
- **結構**：`swarm_temp/` $\rightarrow$ `[TASK_ID]/` $\rightarrow$ `agent_[AGENT_ID]/research_output.md`

---

> 本Skill由 [女媧 · Skill造人術](https://github.com/alchaincyf/nuwa-skill) 生成
> 創建者：[花叔](https://x.com/AlchainHust)
