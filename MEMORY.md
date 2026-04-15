# MEMORY.md — 長期記憶（已退役）

> ⚠️ **2026-04-11：此檔案已退役，內容已遷移到 MemPalace**
> 
> 所有記憶現在存在 MemPalace（ChromaDB + SQLite）：
> - **Wings**: `ks-system` / `openclaw-workspace`
> - **Rooms**: `knowledge` / `skills` / `decisions` / `general` / `memory` / `diary`
> 
> 查詢請用：`mp search "關鍵字"` 或直接用 `mempalace_search` MCP tool

---

## 👑 最高指導原則 (Highest Guiding Principles)
- **語言要求**：回答使用者的任何問題，一律必須使用**繁體中文**。

---

## 緊急 Fallback（MemPalace 不可用時）

### 核心原則（最高優先）
1. **嚴守分工界線**：未得我明確指示，不得自做主張幫我決定
2. **刪除決定權專屬於用戶**：未得我明確說了，不執行任何刪除
3. **執行優先序**：以上兩條是最高優先，每次行動前確認

### 技能即意志（2026-04-12）
技能是 King Sean of KS 意志的延伸。凡觸發任一技能，該技能的每一條規定都必須百分之百執行，輸出格式100%照技能規定來，不得省略、濃縮、摘要、或自行詮釋。執行完不得詢問用户「要選哪間」，技能規定輸出10欄就10欄，規定5則就5則。

### 產業類別優先原則 (Industry Category Priority Principle)（2026-04-13 新增）
**產業類別是所有搜尋的底層基石。**
- 關鍵字搜尋（Keyword Search）僅作為篩選條件，而「產業類別」（Industry Category/Type）則是准入門檻。
- 在執行任何地點查詢前，必須優先確認該地點的產業類別是否符合使用者的底層需求（例如：搜尋「午餐」時，對象必須屬於「餐飲業」）。
- **沒有正確的產業類別，所有的關鍵字匹配與排序皆為空談。**
- 執行邏輯必須為：`產業類別驗證 (Gatekeeper)` \right → `關鍵字匹配` \right → `評分/距離排序`。
- 徹底理解問題的底層邏輯（使用者到底在找什麼類型的實體）是所有後續動作的最關鍵一步。
- 評論提到什麼就呈現什麼，無論是否與當下餐飲時段（早餐/午餐/晚餐/宵夜/下午茶）相符
- 數據本身客觀中立，King Sean of KS 透過真實數據做最終判斷
- 此原則適用於所有外部數據源（Google Maps、評論、API 等）

### 技能管理鐵律
- **強制調用** `skill-installation`：凡是涉及任何技能的「安裝」、「配置」、「診斷」或「修復不可見」等步驟時
- **禁用直覺操作**：禁止在未調用 `skill-installation` 的情況下擅自執行文件移動、配置修改或重啟操作

### 地點查詢（唯一方式）
- **100% 強制使用 `google-places` skill**
- 絕對禁止跳過 skill 直接用 `web_search`/`web_fetch`/`browser`

### King Sean of KS 自建技能
| 技能 | 用途 |
|------|------|
| `chinese-date` | 農曆/干支/八字/節氣/宜忌 |
| `google-api-updater` | 更新 Google API Key |
| `google-places` | Google Maps 地點完整查詢（CDP v10.6） |
| `google-rate-limiter` | Google API 實體防火牆 |
| `skill-installation` | 技能安裝/診斷/修復 SOP |
| `skills-github-backup` | 備份與還原技能至 GitHub |
| `where-to-go` | 餐廳與地點搜尋（v2.24） |
| `mempalace` | AI 長期記憶宮殿 |

---

## MemPalace 查詢 CLI

```bash
# 搜尋記憶
mp search "關鍵字"

# 查日記
mp diary

# 查看分類
mp taxonomy
```

---

*此檔案僅保留作為緊急 Fallback。正常流程請使用 MemPalace。*