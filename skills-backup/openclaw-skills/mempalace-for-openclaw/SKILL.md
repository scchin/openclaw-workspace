---
name: mempalace for OpenClaw
description: MemPalace 長期記憶系統 (Phase 4 Hybrid Edition)。King Sean of KS 的 AI 記憶宮殿，從單純的語意儲存進化為結構化知識圖譜管理。整合 BM25 混合搜尋、跨翼隧道、內容路由與事實檢查機制，確保記憶檢索的極高精準度與邏輯連貫性。
author: King Sean of KS
---

# MemPalace for OpenClaw — AI 記憶宮殿 Phase 4 (Hybrid Edition)

## ⚡ Phase 4 核心進化（2026-04-15）

MemPalace 已從單純的向量儲存進化為**結構化知識圖譜管理系統**：
- ✅ **混合搜尋 (Hybrid Search)**：結合向量相似度 (60%) 與 BM25 關鍵字匹配 (40%)，解決冷門術語與精確版本號找不到的問題。
- ✅ **索引層 (Closet Layer)**：引入 AAAK 指針索引，搜尋路徑由 `Wing -> Room -> Drawer` 優化為 `Closet -> Hall -> Drawer`，大幅提升檢索速度。
- ✅ **跨翼隧道 (Cross-Wing Tunnels)**：支持在不同 Wing 之間建立顯式鏈接，實現跨項目的知識跳轉。
- ✅ **事實檢查 (Fact Checker)**：可對照實體註冊表與知識圖譜驗證記憶碎片，消除幻覺與過時數據。

## 🚀 聯動最佳化：動態記憶深度 (Dynamic Depth)

MemPalace 與 `google-reliability-guardian` 深度聯動，根據系統健康度自動調整檢索深度：

**聯動邏輯：**
- **Normal (健康)** \right → `MP_LIMIT = 5` \right → 完整模式 (深度認知)
- **Warning (警示)** \right → `MP_LIMIT = 3` \right → 精簡模式 (速度優先)
- **Critical (臨界)** \right → `MP_LIMIT = 1` \right → 極簡模式 (生存模式，極速減壓)

**調用路徑：**
優先使用 `/Users/KS/.openclaw/workspace/mp_dynamic.py` 進行查詢。

---

## 記憶體架構 (Knowledge Graph Structure)

```
KingSeanKS 的大腦 (Phase 4)
  ↓
MemPalace (ChromaDB + SQLite)
  ├── 索引層 (Closets): 快速 AAAK 匹配 \right → 定位 Drawer
  ├── 路由層 (Halls): 根據內容類型過濾 (technical, emotions, identity, etc.)
  ├── 儲存層 (Drawers): 原始 verbatim 記憶片段
  └── 鏈接層 (Tunnels): 跨 Wing 的知識跳轉鏈接
```

### 核心 Wing 分佈
- **ks-system**: 核心原則、系統知識、決策紀錄。
- **openclaw-workspace**: 開發日誌、技能文件、環境配置。
- **wing_kingseanks**: 個人的日記、生活紀錄。

---

## 工具列表

### 1. 搜尋與檢索（優先級：高）

| 工具 | 用途 | 建議場景 |
|------|------|------|
| `mempalace_search` | **混合搜尋** (向量+BM25)。支持指定 wing/room/hall。 | 絕大多數記憶檢索。搜尋精確詞彙時效果極佳。 |
| `mempalace_list_wings` | 列出所有 wings。 | 探索記憶庫概況。 |
| `mempalace_list_rooms` | 列出某 wing 內的所有 rooms。 | 定位特定類別記憶。 |
| `mempalace_get_taxonomy` | 獲取完整分類樹。 | 理解記憶組織邏輯。 |
| `mempalace_kg_query` | 查詢知識圖譜實體關係。 | 分析概念之間的邏輯鏈接。 |
| `mempalace_fact_check` | **事實核查**。驗證文本與實體註冊表的一致性。 | 處理重要決定或回報事實前，防止幻覺。 |

### 2. 知識鏈接 (Tunnels)

| 工具 | 用途 | 建議場景 |
|------|------|------|
| `mempalace_create_tunnel` | 建立兩個記憶點之間的顯式鏈接。 | 將 A 項目的設計決策鏈接至 B 項目的實現。 |
| `mempalace_list_tunnels` | 列出所有已建立的隧道。 | 審視跨項目知識網。 |
| `mempalace_follow_tunnel` | 沿著隧道跳轉至關聯記憶。 | 深度追溯知識來源。 |
| `mempalace_delete_tunnel` | 移除失效的鏈接。 | 記憶清理。 |

### 3. 寫入與維護

| 工具 | 用途 | 建議場景 |
|------|------|------|
| `mempalace_add_drawer` | 寫入記憶 (指定 wing/room)。 | 保存新知識、決定或事件。 |
| `mempalace_diary_write` | 寫入日記 (自動按日分抽屜)。 | 日常反思與紀錄。 |
| `mempalace_kg_add` | 新增知識圖譜三元組。 | 定義實體關係 (A \right → 屬於 \right → B)。 |
| `mempalace_status` | 查看 palace 狀態。 | 檢查儲存量與版本。 |
| `mempalace_repair` | 重建向量索引。 | 修復 Segfault 或數據損壞。 |

---

## 快速查詢 CLI

```bash
# 1. 動態深度搜尋 (推薦)
python3 ~/.openclaw/workspace/mp_dynamic.py "關鍵字"

# 2. 標準混合搜尋
mp search "關鍵字" --hall technical # 僅搜尋技術類記憶

# 3. 查日記
mp diary

# 4. 跨翼跳轉
mp tunnel follow <tunnel_id>
```

---

## 喚醒上下文（Session 啟動時）

```bash
# 緊湊模式（~91 tokens）
python3 ~/.openclaw/hooks/mempalace-for-openclaw-memory/wakeup.py

# 完整模式（~280 tokens）
python3 ~/.openclaw/hooks/mempalace-for-openclaw-memory/wakeup.py -f
```

---

## Phase 3 \right → Phase 4 進化對比

| 維度 | Phase 3 (Dynamic) | Phase 4 (Hybrid) | 提升點 |
|------|-----------|-----------|------|
| **搜尋精度** | 語意相似 \right → 可能偏移 | **BM25 + 向量 \right → 精確命中** | 解決冷門詞彙失效問題 |
| **檢索速度** | 掃描抽屜 \right → 較慢 | **Closet 索引 \right → 極速** | 降低大容量記憶的延遲 |
| **知識結構** | 孤立的 Wing | **跨翼隧道 (Tunnels)** | 實現真正的全域知識圖譜 |
| **可靠性** | 信任檢索結果 | **事實檢查 (Fact Check)** | 降低 AI 幻覺率 |
| **語言能力** | 基礎中文支援 | **原生 i18n 繁體中文優化** | 記憶還原更自然、精準 |