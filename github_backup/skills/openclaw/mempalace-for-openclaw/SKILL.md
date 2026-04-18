---
name: mempalace for OpenClaw
description: MemPalace 長期記憶系統 (Hybrid v5 Develop)。King Sean of KS 的 AI 記憶宮殿，從單純的語意儲存進化為時序實體關係圖管理。整合 29 個 MCP 工具、動態分流路由與關聯喚醒機制，確保記憶檢索的極高精準度與邏輯連貫性。
author: King Sean of KS
---

# MemPalace for OpenClaw — AI 記憶宮殿 Hybrid v5 (Develop)

## ⚡ v5 核心進化（2026-04-17 邏輯對齊）

MemPalace 已全面升級為**時序實體關係圖管理系統**，並將能力對齊至 OpenClaw 的自動化行為中：
- ✅ **關聯喚醒 (Relational Wake-up)**：Session 啟動時，不再僅讀取最近日記，而是根據「目前核心實體」自動提取關聯狀態。
- ✅ **智能分流 (Routed Search)**：強制執行「意圖 $\rightarrow$ 房間」路由。技術查詢導向 `skills`，事實/情緒查詢導向 `memory`，實現 0 噪音檢索。
- ✅ **時序有效性 (Temporal Validity)**：支持狀態回溯，可精確查詢「在特定時間點，實體的狀態是什麼」。
- ✅ **異構索引隔離**：通過虛擬房隔離，根除技術術語與個人記憶之間的信號干擾。

## 🚀 聯動最佳化：動態記憶深度 (Dynamic Depth)

MemPalace 與 `google-reliability-guardian` 深度聯動，根據系統健康度自動調整檢索深度：

**聯動邏輯：**
- **Normal (健康)** $\rightarrow$ `MP_LIMIT = 5` $\rightarrow$ 完整模式 (深度認知)
- **Warning (警示)** $\rightarrow$ `MP_LIMIT = 3` $\rightarrow$ 精簡模式 (速度優先)
- **Critical (臨界)** $\rightarrow$ `MP_LIMIT = 1` $\rightarrow$ 極簡模式 (生存模式，極速減壓)

**調用路徑：**
優先使用 `/Users/KS/.openclaw/workspace/mp_dynamic.py` 進行查詢。

---

## 記憶體架構 (Knowledge Graph Structure)

```
KingSeanKS 的大腦 (Hybrid v5)
    ↓
MemPalace (ChromaDB + SQLite Temporal KG)
    ├── 路由層 (Routed Halls): 根據意圖分流 (Technical, Memory, Identity, etc.)
    ├── 實體層 (Entities): 追蹤核心對象及其狀態變遷 (State-over-Time)
    ├── 儲存層 (Drawers): 原始 verbatim 記憶片段
    └── 鏈接層 (Tunnels): 跨項目知識跳轉鏈接
```

### 核心 Wing 分佈
- **ks-system**: 核心原則、系統知識、決策紀錄。
- **openclaw-workspace**: 開發日誌、技能文件、環境配置。
- **wing_kingseanks**: 個人的日記、生活紀錄。

---

## 工具列表

### 1. 搜尋與檢索（優先級：高）

| 工具 | 用途 | 建議場景 | v5 路由要求 |
|------|------|------|------|
| `mempalace_search` | **混合搜尋** (向量+BM25)。 | 絕大多數記憶檢索。 | **必須指定 `--room`** 以獲取最高純度。 |
| `mempalace_list_wings` | 列出所有 wings。 | 探索記憶庫概況。 | N/A |
| `mempalace_list_rooms` | 列出某 wing 內的所有 rooms。 | 定位特定類別記憶。 | N/A |
| `mempalace_get_taxonomy` | 獲取完整分類樹。 | 理解記憶組織邏輯。 | N/A |
| `mempalace_kg_query` | 查詢知識圖譜實體關係。 | 分析概念之間的邏輯鏈接。 | 建議指定實體名稱。 |
| `mempalace_fact_check` | **事實核查**。驗證文本與實體註冊表的一致性。 | 處理重要決定或回報事實前，防止幻覺。 | N/A |

### 2. 知識鏈接 (Tunnels)

| 工具 | 用途 | 建議場景 |
|------|------|------|
| `mempalace_create_tunnel` | 建立兩個記憶點之間的顯式鏈接。 | 將 A 項目的設計決策鏈接至 B 項目的實現。 |
| `mempalace_list_tunnels` | 列出所有已建立的鏈接。 | 審視跨項目知識網。 |
| `mempalace_follow_tunnel` | 沿著隧道跳轉至關聯記憶。 | 深度追溯知識來源。 |
| `mempalace_delete_tunnel` | 移除失效的鏈接。 | 記憶清理。 |

### 3. 寫入與維護

| 工具 | 用途 | 建議場景 |
|------|------|------|
| `mempalace_add_drawer` | 寫入記憶 (指定 wing/room)。 | 保存新知識、決定或事件。 |
| `mempalace_diary_write` | 寫入日記 (自動按日分抽屜)。 | 日常反思與紀錄。 |
| `mempalace_kg_add` | 新增知識圖譜三元組。 | 定義實體關係 (A $\rightarrow$ 屬於 $\rightarrow$ B)。 |
| `mempalace_status` | 查看 palace 狀態。 | 檢查儲存量與版本。 |
| `mempalace_repair` | 重建向量索引。 | 修復 Segfault 或數據損壞。 |

---

## 快速查詢 CLI

```bash
# 1. 動態深度搜尋 (推薦)
python3 ~/.openclaw/workspace/mp_dynamic.py "關鍵字"

# 2. 標準混合搜尋 (v5 強制路由模式)
mp search "關鍵字" --room skills  # 僅搜尋技術類記憶
mp search "關鍵字" --room memory  # 僅搜尋個人事實類記憶

# 3. 查日記
mp diary

# 4. 跨翼跳轉
mp tunnel follow <tunnel_id>
```

---

## 喚醒上下文（Session 啟動時）

```bash
# 緊湊模式（包含關聯喚醒 $\rightarrow$ ~150 tokens）
python3 ~/.openclaw/hooks/mempalace-for-openclaw-memory/wakeup.py

# 完整模式（深度回溯 $\rightarrow$ ~350 tokens）
python3 ~/.openclaw/hooks/mempalace-for-openclaw-memory/wakeup.py -f
```

---

## Phase 4 $\rightarrow$ Hybrid v5 進化對比

| 維度 | Phase 4 (Hybrid) | Hybrid v5 (Develop) | 實質提升 |
|------|-----------|-----------|------|
| **喚醒邏輯** | 線性時間軸 (最近紀錄) | **關聯圖譜 (核心實體狀態)** | 解決「重要事實被時間掩蓋」問題 |
| **搜尋路徑** | 語意搜尋 $\rightarrow$ 碎片結果 | **意圖路由 $\rightarrow$ 房間隔離** | 實現 0 噪音檢索 $\rightarrow$ 降低 Token 損耗 |
| **狀態管理** | 靜態事實儲存 | **時序有效窗 (Validity Window)** | 實現精確的狀態回溯與變遷追蹤 |
| **認知深度** | 點對點檢索 | **多跳關聯 (Multi-hop)** | 能夠處理複雜的邏輯推理鏈接 |
