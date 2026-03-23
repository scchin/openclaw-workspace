# 長期記憶

## ⚠️ 核心最高指導原則（霸王條款，優先於一切）

### １．嚴守分工界線
未得我明確指示，不得自做主張幫我決定。

### ２．刪除決定權專屬於用戶
未得我明確說了，不執行任何刪除。

### ３．執行優先序
以上兩條是最高優先，每次行動前確認。

---

## 地點查詢規則

**所有地點查詢，強制使用 `google-places` skill。**

查詢方式：
```bash
cd ~/.openclaw/skills/google-places && .venv/bin/python scripts/query.py search "店名"
cd ~/.openclaw/skills/google-places && .venv/bin/python scripts/query.py full <place_id>
```

**絕對禁止：**
- ❌ 跳過 skill 直接用 `web_search`/`web_fetch`/`browser` 查地點
- ❌ 自己開瀏覽器分頁
- ❌ 用 `browser` 工具操作
- ❌ 用 `exec` + Playwright/Puppeteer

**CDP 定位**：CDP 是 query.py 內部技術，不等於我可使用 `browser` 工具。

**經緯度查詢**：一律用 https://map.tgos.tw/TGOSCloudMap

---

## MCP 設定

`~/.openclaw/workspace/config/mcporter.json`

| 伺服器 | 功能 |
|--------|------|
| `playwright` | 瀏覽器自動化（22工具）|
| `filesystem` | 檔案系統（14工具）|
| `github` | GitHub API（26工具）|
| `memory` | 知識圖譜（9工具）|
| `puppeteer` | 瀏覽器自動化（7工具）|

---

## google-places skill（自建 v9）

- `~/.openclaw/skills/google-places/`
- `open_now` 欄位為主（Google API 即時判斷）
- CDP 讀「每人消費」，已全自動化
- 用 `goplaces` CLI 做基本查詢
- 僅6個月內評論

---

## 我要去哪（where-to-go）技能

- `~/.openclaw/skills/where-to-go/`
- 觸發關鍵字：早餐、午餐、晚餐、宵夜、下午茶、點心、麵包、小吃、夜市、餐館、飯店、廁所、加油站、停車場、美術館、博物館、圖書館、公園、景點、學校、旅館、民宿、火鍋、壽司、合菜、快炒、素食、港式、飲茶、冰（2026-03-23 新增）等
- 預設圓心：我家（`24.18588146738243, 120.66765935832942`）
- 預設半徑：1km，評分 ≥ 4.5（食物類型自動降至 ≥ 3.5），現在有開，由近到遠
- 半徑自動擴張：1000 → 1500 → 2500 → 5000 → 10000 → 20000 → 50000 m
- 執行：`python3 ~/.openclaw/skills/where-to-go/scripts/run.py "<關鍵字>"`

---

## where-to-go 輸出模板（2026-03-23 v2 最終版，永久鎖定）

**輸出時直接貼上 run.py 的 raw 文字，不得濃縮、摘要或重新排版。**

格式實例（2026-03-23 實測驗證）：

```
+--------------------------------------------------------+
|                     🍽️  午餐 選 項  🍽️                     |
+--------------------------------------------------------+

  📍 條件  午餐
  📏 範圍  (24.1859, 120.6677) 半徑 1km
  📊 排序  評分 ≥ 4.5，由近到遠
  🔍 搜尋  共 20 家候選

  🥇 +--------------------------------------------------
    | 悠沐手作豆花 - 陳平店｜🍴 符合：午餐
    | ⭐ 4.8（210則）
    | ▓░░░░░░░░░
    | 🚗1分 🚶3分
    | ✅ 營業中
    | 📞 0905 669 695
    | 📌 外帶
    | 🍴 豆花：吃不錯，還可以調甜度很有彈性
    | 👤 Bill Kao：豆漿豆花吃不錯...
    | 🗺️ https://www.google.com/maps/place/?q=place_id:ChIJ...
    +--------------------------------------------------

  🥈 +--------------------------------------------------
    | 王爺王肉羹(總店)｜🍴 符合：午餐
    ...
    +--------------------------------------------------

  （下一家以此類推，店家間不加分隔線）
```

**抬頭（開場）：** `+---` 頂底、`|` 行首、`🍽️` 置中、寬度 58 字元
**店家卡片：** `  🥇 +---` 卡片頂、每行 `|    |` 縮排、末尾 `    +---` 卡片底
**固定欄位：** 店名/評分/進度條/交通/狀態/電話（可选）/服務/菜色/評論/地圖
**結尾：** 無需 `✅ 已找到...`（2026-03-23 已移除）

**嚴格規定：**
- Markdown code block（```）包裹全文，不得使用 HTML `<pre>`
- `|` 為純 ASCII pipe character
- 框線全用 `+` `-` `|` ASCII，不可摻 Unicode 繪文字字元（Emoji 除外）
- 日後新增項目，一律適用同一模板：一行一個資訊，不並排
- **技能執行鐵律**：拿到的 raw 輸出原封不動貼給用戶，不濃縮、不摘要、不重排

---

## 農民曆查詢

- `~/.openclaw/skills/chinese-date/`
- 引擎：`cantian-tymext`
- 安裝：`bash ~/.openclaw/skills/chinese-date/scripts/install.sh`

---

## 技能雲端備份

- 技能：`~/.openclaw/skills/skills-backup-github/`
- Repo：https://github.com/scchin/openclaw-workspace
- 備份：`skills-backup/all-skills/`
- 每日03:00自動執行（launchd）

```bash
# 備份
bash ~/.openclaw/skills/skills-backup-github/scripts/backup.sh
# 還原
bash ~/.openclaw/skills/skills-backup-github/scripts/restore.sh
```

---

## Token Optimizer

- `~/.openclaw/skills/token-optimizer/`
- 已套用全量優化（11/11通過）
- 模型：Haiku、Heartbeat：Ollama、快取：開啟
- 日預算：$5、月預算：$200
- 備份：`~/.openclaw/backups/openclaw_YYYYMMDD_HHMMSS.json`

---

## 舊記錄歸檔

`MEMORY-ARCHIVE.md`（包含2026-03-22前所有使用記錄、彰化早餐、陳平國小午餐、MCP安裝歷程、google-places v7修正歷程）

## 技能執行行為鐵律（2026-03-23 新增）

### 濃縮輸出 = 最高優先違規
**拿到的完整輸出，就是回覆的完整內容。**
不多一個字，不少一個字。

觸發時機：使用任何技能（where-to-go、或其他），該技能有完整原始輸出時，必須將那段文字原封不動貼進回覆。不得濃縮、摘要、或用自己的話重說。

**例外**：使用者明確說「幫我濃縮」、「只要3家」、「給我精選」。

**為何要明文規定**：AI 預設會「幫使用者想比較好讀的版本」，這不是使用者要求的，是自己決定的。每次都必須重新確認「我正在拿到的輸出是什麼，就貼什麼」。
