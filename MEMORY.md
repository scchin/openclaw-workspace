# MEMORY.md — 長期記憶（已退役）

> ⚠️ **2026-04-11：此檔案已退役，內容已遷移到 MemPalace**
> 
> 所有記憶現在存在 MemPalace（ChromaDB + SQLite）：
> - **Wings**: `ks-system` / `openclaw-workspace`
> - **Rooms**: `knowledge` / `skills` / `decisions` / `general` / `memory` / `diary`
> 
> 查詢請用：`mp search "關鍵字"` 或直接用 `mempalace_search` MCP tool

---

## 緊急 Fallback（MemPalace 不可用時）

### 核心原則（最高優先）
1. **嚴守分工界線**：未得我明確指示，不得自做主張幫我決定
2. **刪除決定權專屬於用戶**：未得我明確說了，不執行任何刪除
3. **執行優先序**：以上兩條是最高優先，每次行動前確認

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
| `google-places` | Google Maps 地點完整查詢（CDP） |
| `google-rate-limiter` | Google API 實體防火牆 |
| `skill-installation` | 技能安裝/診斷/修復 SOP |
| `skills-github-backup` | 備份與還原技能至 GitHub |
| `where-to-go` | 餐廳與地點搜尋 |
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
