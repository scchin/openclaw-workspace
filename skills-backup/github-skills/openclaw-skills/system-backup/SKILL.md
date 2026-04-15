---
name: system-backup
description: 系統全量備份與版本紀錄工具。整合了變更日誌自動化與 GitHub 同步，確保所有技能、設定及意志制度化內容被完整保存。觸發關鍵字：系統備份, 全量同步, system backup, sync all.
author: King Sean of KS
category: System
tags: [backup, sync, version-control, changelog]
---

# 📦 system-backup — 系統全量備份工具

本技能將系統同步流程從單純的「腳本執行」升級為「版本管理工作流」。它確保在每次同步前，所有的變更都被記錄在案，並在同步後提供結構化的回報。

## 🚀 執行工作流 (Execution Workflow)

當觸發本技能時，將依序執行以下原子操作：

1. **變更提取 (Change Extraction)**：
  - 掃描 `workspace` 與 `skills` 目錄的最近變動。
  - 自動生成/更新當日的 `CHANGELOG_YYYY-MM-DD.md`。
2. **設定 Sentry 喚醒 (Sentry Scheduling)**：
  - **禁止手動計算時間**。必須先執行 `python3 ~/.openclaw/workspace/sentry_scheduler.py 300` (或適當延遲)。
  - 將腳本輸出之 UTC 時間戳填入 `cron` 工具的 `schedule.at` 欄位。
3. **全量同步 (Full Sync)**：
  - 調用 `system-full-sync.sh` 執行同步 \right → 網關重啟 \right → UI 刷新。
4. **結案報告 (Final Report)**：
  - 根據 `discipline-guardian` 協議，輸出包含同步狀態、提交雜湊與變更摘要的報告。
  - **原子順序**：報告 \right → 清除 `pending_tasks.json` \right → 結束。

## 🛠️ 使用方式

### 1. 基礎同步
直接輸入 `系統備份` 或 `全量同步`。AI 將自動執行上述完整工作流。

### 2. 指定變更備註
如果您想為本次備份添加特定註記，可以使用：
`系統備份：[在此輸入變更摘要]`

## ⚙️ 內部實現
- **主控腳本**：`~/.openclaw/skills/system-backup/sync_manager.py`
- **底層依賴**：`/Users/KS/.openclaw/workspace/system-full-sync.sh`

---
**⚠️ 注意**：本技能涉及網關重啟，執行後 UI 將短暫中斷並自動刷新。