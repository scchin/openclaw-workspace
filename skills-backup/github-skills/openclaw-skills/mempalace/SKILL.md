---
name: mempalace
description: MemPalace 長期記憶系統。King Sean of KS 的 AI 記憶宮殿，提供 RAW verbatim 語意搜尋、知識圖譜、日記功能。當需要查詢歷史決定、搜尋過去對話、找回技術細節、或需要跨 session 的長期記憶時使用。觸發關鍵字：搜尋記憶、查歷史、找到過去、MemPalace、記得我之前說過、之前的決定。
author: King Sean of KS
---

# MemPalace — AI 記憶宮殿 Phase 3

## ⚡ Phase 3 完全接管（2026-04-11）

MemPalace 已完全取代舊的記憶系統：
- ✅ MEMORY.md 已退役（內容遷移到 MemPalace）
- ✅ 每日日誌已遷移（7個檔案 → 7 drawers）
- ✅ 技能摘要已遷移（8個技能）
- ✅ Session 啟動 Token：~2500 → ~280（88% 節省）

---

## 架構

```
KingSeanKS 的大腦
    ↓ 每個重要事件
MemPalace (ChromaDB + SQLite)
    ├── Wing: ks-system
    │   ├── knowledge（核心原則、系統知識）
    │   ├── skills（自建技能、輸出模板）
    │   ├── decisions（重要決定）
    │   └── general（一般記憶、日記）
    ├── Wing: openclaw-workspace
    │   ├── memory（OpenClaw 日誌）
    │   └── skills（技能文件）
    └── Wing: wing_kingseanks
        └── diary（KingSeanKS 日記）
```

**總 drawers：20,561 筆（持續增加中）**

---

## 工具列表

### 搜尋工具（首選）

| 工具 | 用途 |
|------|------|
| `mempalace_search` | 語意搜尋，可指定 wing/room 過濾 |
| `mempalace_list_wings` | 列出所有 wings |
| `mempalace_list_rooms` | 列出某 wing 內的所有 rooms |
| `mempalace_get_taxonomy` | 完整分類樹 |
| `mempalace_kg_query` | 查詢知識圖譜中的實體關係 |

### 寫入工具

| 工具 | 用途 |
|------|------|
| `mempalace_add_drawer` | 寫入記憶內容（指定 wing/room） |
| `mempalace_diary_write` | 寫入日記 |
| `mempalace_kg_add` | 新增知識圖譜三元組 |

### 管理工具

| 工具 | 用途 |
|------|------|
| `mempalace_status` | 查看 palace 狀態 |
| `mempalace_kg_stats` | 知識圖譜統計 |
| `mempalace_check_duplicate` | 寫入前檢查是否已存在 |

---

## 快速查詢 CLI

```bash
# 搜尋記憶
mp search "關鍵字"

# 查日記
mp diary

# 查看分類
mp taxonomy
```

---

## 喚醒上下文（Session 啟動時）

```bash
# 緊湊模式（~91 tokens）
python3 ~/.openclaw/hooks/mempalace-memory/wakeup.py

# 完整模式（~280 tokens）
python3 ~/.openclaw/hooks/mempalace-memory/wakeup.py -f
```

---

## Phase 3 vs Phase 1-2 對比

| 維度 | Phase 1-2 | Phase 3 |
|------|-----------|---------|
| Session 啟動 Token | ~2500 | ~280 |
| 歷史搜尋 | 關鍵字找檔案 | 語意搜尋，精準命中 |
| 記憶保存 | 檔案系統 | ChromaDB 向量 + SQLite |
| 跨 session 理解 | 需重述背景 | 自動上下文補充 |
| 日記 | 手動寫入 | Hook 自動寫入 |

---

## 維護與疑難排解

### Palace 狀態
```bash
mp status
```

### 重建索引（Segfault 後修復）
```bash
mempalace repair
```

### 手動寫入
```python
from mempalace.mcp_server import tool_add_drawer
tool_add_drawer(
    content="你的內容",
    wing="ks-system",
    room="general",
    source_file="manual-2026-04-11"
)
```
