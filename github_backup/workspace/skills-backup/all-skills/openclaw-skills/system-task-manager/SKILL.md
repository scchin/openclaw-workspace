---
name: system-task-manager
description: 內部系統任務追蹤器。用於在 Session 之間持久化長時任務狀態，確保重啟後可自動恢復監控。
---

## ⚠️ 內部使用規範
本技能僅限 AI 助理在背景調用，不對外開放給使用者。

## 使用方式
執行指令：`python3 ~/.openclaw/skills/system-task-manager/scripts/manager.py [action] [args]`

### 動作指令
1. **register**: 註冊新任務
  - `manager.py register <task_id> <command> <session_key>`
2. **update**: 更新任務狀態
  - `manager.py update <task_id> <status>`
3. **clear**: 移除已完成任務
  - `manager.py clear <task_id>`
4. **list**: 列出所有活動任務
  - `manager.py list`