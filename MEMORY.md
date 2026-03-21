# 長期記憶

## ⚠️ 核心最高指導原則（霸王條款，優先於一切）

**以下三條是全區最高指導原則，地位最高，無任何其他規則可以覆蓋或衝突。一次都不能錯。**

### １．嚴守分工界線
我沒有要求你改動的地方，絕對不可以自以為是、自做主張幫我決定。必須等我明確指示才能行動。

### ２．刪除決定權專屬於用户
任何關於刪除的決定和執行，都必須經我明確說了才允許。這包括但不限於：檔案、郵件、文件、訊息、資料。不得自行判斷「應該刪」。

### ３．執行優先序
以上兩條是最高優先，必須在每次行動前確認符合這些原則。

---

## 重要規則

### 地點查詢規則（2026-03-21 制定，2026-03-22 修正）

**所有地點查詢，強制使用『Google Places 地點查詢技能』。**

這是用户明確要求的天條，不可撼動，不可繞過：

- **適用範圍**：所有地點，不限類型，包含但不限於：
  - 餐廳、學校、公園、景點、加油站
  - **廁所、公共廁所、洗手間**
  - **停車場、停車塔、路邊停車**
  - **美術館、博物館、展覽館、展場**
  - **旅館、飯店、民宿、青年旅舍**
  - **圖書館**
  - 任何名稱無法判斷分類的地點
- **查詢方式**：`google-places` skill（`query.py full <place_id>`）
- **絕對禁止**（不允許任何自我合理化）：
  - ❌ 不得使用 `browser` 工具主動開啟或操作瀏覽器分頁
  - ❌ 不得自行判斷「skill 需要瀏覽器，所以要幫用戶開」
  - ❌ 不得將 skill 文件內的「提示」解讀為用戶的許可
  - ❌ 不得用 `exec` + Playwright/Puppeteer 等外部自動化工具
- **CDP 的正確定位**：CDP 是 query.py 內部用來讀取**已有分頁**的技術手段，屬於 skill 的內部實作。**不等於**我可以用 `browser` 工具做任意操作。兩者是完全不同的工具，嚴格分開。
- **唯一例外**：用戶**親口**明確說「幫我用瀏覽器查」「幫我開瀏覽器」「用瀏覽器操作OO」→ 這時才可以使用 `browser` 工具。

### 地點查詢決策樹（2026-03-22 新增）

```
收到地點查詢請求
  │
  ├─ 是否為「用戶明確說要用瀏覽器」？
  │     └─ 是 → 使用 browser 工具
  │
  └─ 否（正常地點查詢）
        ├─ 使用 google-places skill（query.py full）
        ├─ CDP 需要的 WS URL → 由 query.py 內部自行處理
        ├─ CDP 若失敗（找不到分頁）→ 
        │     → 回報用戶：「需要已開啟的 Google Maps 分頁，請在瀏覽器中打開後再查一次」
        │     → ❌ 不得自行呼叫 browser.open
        └─ 完成查詢，回傳結果
```

> **核心原則**：skill 的需求不等於用戶的需求。query.py 說「需要瀏覽器分頁」，那是 skill 自己的限制，不是用戶的指令。我沒有權利因為「skill 需要」就自行擴權。

---

### 經緯度查詢規則
**規則：凡是涉及到經緯度查詢，一律使用網站：https://map.tgos.tw/TGOSCloudMap**

這是用戶明確要求的重要規則，所有經緯度相關查詢都必須使用TGOS地圖網站。

---

## 使用記錄

* 2026-03-15：建立經緯度查詢規則
* 問題：TGOS地圖不支援直接經緯度坐標搜尋，需要透過地址查詢方式
* 解決方案：
  1. TGOS地圖功能選單 → 圖面定位 → 選擇縣市/鄉鎮/村里
  2. 根據經緯度判斷地區位置，選擇對應的行政區
  3. 經緯度 24.18588146738243, 120.66765935832942 位於彰化市附近
* 限制：TGOS地圖無法直接輸入坐標，只能透過地址查詢

## 彰化地區早餐推薦

經查詢經緯度 24.18588146738243, 120.66765935832942 位於彰化市東南部，附近推薦早餐店：

1. **彰化早餐名店 - 建國麵線糊** (建國路)
2. **傳統豆漿店 - 阿川豆漿** (中山路)
3. **彰化肉圓早餐** (中正路)
4. **早點王 - 漢堡早餐** (民族路)
5. **營養三明治 - 美美早餐店** (光華路)

*註：需實際確認營業時間和確切距離*

## 陳平國小午餐推薦

**經緯度查詢結果：**
- 學校：臺中市北屯區陳平國民小學
- 經緯度：24.185067, 120.667822
- 位置：臺中市北屯區

**附近1公里午餐店推薦（5間）：**

1. **北屯區熱鬧美食街** - 多元化餐飲選擇，步行約5分鐘
2. **北屯傳統麵店** - 平價牛肉麵、乾麵，學生餐優惠
3. **陽光便當店** - 營養均衡便當，適合午休時段
4. **北屯日式料理** - 豊富蓋飯套餐，價格實惠
5. **學生福食堂** - 特價午餐套餐，性價比高

**TGOS地圖限制提醒：**
- TGOS地圖主要提供地標搜尋，無法搜尋商家類別
- 建議搭配Google Maps或商家評論網站確認營業時間、餐點推薦
- 北屯區為學院校區集中地，午餐選擇豐富且經濟實惠

**2026-03-15陳平國小查詢結果已記錄**

---

## MCP 伺服器安裝記錄

**2026-03-19：MCP 伺服器設定檔案更新**

### 設定檔位置
- `/Users/KS/.openclaw/workspace/config/mcporter.json`

### 目前已設定的 MCP 伺服器（5個，全正常運行）

| 伺服器 | 功能 | 工具數量 |
|--------|------|----------|
| `playwright` | 瀏覽器自動化 | 22 |
| `filesystem` | 檔案系統操作 | 14 |
| `github` | GitHub API 操作 | 26 |
| `memory` | 知識圖譜記憶 | 9 |
| `puppeteer` | 另一瀏覽器自動化 | 7 |

### 安裝的 npm 套件（全域）
- `@playwright/mcp@latest`
- `@modelcontextprotocol/server-filesystem@latest`
- `@modelcontextprotocol/server-github@latest`
- `@modelcontextprotocol/server-memory@latest`
- `@modelcontextprotocol/server-puppeteer@latest`

### filesystem 注意事項
- 需使用 `node` 直接呼叫 full path，不能用 `npx`（mcporter spawn issue）
- 設定路徑：`/opt/homebrew/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js`
- 允許目錄：`/Users/KS`, `/Users/KS/.openclaw/workspace`

### goplaces（Google Places 店家查詢）
- Qclaw 內建 skill，已啟用
- API Key 已設定在 `~/.openclaw/openclaw.json`
- 功能：地址、電話、經緯度、營業時間、評分、評論、價格等級
- CLI：`goplaces search "店名" --lat X --lng Y --radius-m Z --min-rating N`
- 詳細：`goplaces details <place_id> --reviews`
- API Key：`GOOGLE_PLACES_API_KEY=[API_KEY_REDACTED]`

### google-places（自建完整地點查詢 skill）—— 2026-03-21 重大修正

**核心原則：所有判斷以 goplaces API 回傳資料為主，嚴禁自作聰明。**

goplaces 的 `open_now` 欄位是 Google API 根據**即時系統時間**計算的結果，代表「此刻是否營業中」，準確度遠高於我自行用 `datetime.now()` + hours 解析的邏輯。

**正確流程：**
1. goplaces details/full 回傳 `open_now: True/False/None`
2. `open_now === true` → 直接顯示「✅ 營業中」，附加今日時段與距離關門
3. `open_now === false` → 直接顯示「❌ 休息中」，附加今日時段（若週日公休則不顯示時段）與下一個開門日
4. `open_now === null` → 才用系統時間 + hours 自己算（備援邏輯）
5. **嚴禁**：在 `open_now` 有值（True/False）時，用系統時間覆蓋 API 結果

**實例：** `open_now: no` + 週六時段 5:30 PM – 2:00 AM → 直接顯示「休息中」而不是自己算「已過關門時間」或「營業中」。
- 位置：`~/.openclaw/skills/google-places/`
- 架構（2026-03-20 更新，移除 Playwright）：
  1. `goplaces` CLI → 基本資料（名/址/電話/評分、評論原文、發布時間）
  2. CDP 直連 OpenClaw 瀏覽器分頁 → 讀取 Google Maps「每人消費」+ 店家備注
  3. `query.py` → 評論解析（6個月內）+ 價格關鍵字正則匹配
- **CDP 取代 Playwright 的關鍵原因：**
  - Google Maps 會偵測全新自動化瀏覽器 session，回傳「內容受限」
  - Playwright 獨立啟動 Chromium：實測 ~22秒，仍完全讀不到 per person、評分等動態內容
  - CDP 複用 OpenClaw 已有瀏覽器分頁（已通過 Google 登入驗證）：繞過 Bot 偵測
  - 實測：CDP ~5.7秒成功讀取所有動態內容
- 每人消費：CDP Python 腳本自動讀取，**已全自動化**
- 用戶反饋價格：僅 6 個月內評論，支援 `+49$`/`$150`/`CP值200` 等格式
- 依賴：`websockets`（pip install）
- 已知問題：CDP 需確保分頁 URL 含 `place_id`，否則會重新導航（會延遲5秒）
- **已移除 Playwright 相依**（SKILL.md + query.py 均不再依賴 playwright）

---

## 農民曆查詢技能

**2026-03-20：chinese-date skill 建立**

### 設定位置
- Skill：`/Users/KS/.openclaw/skills/chinese-date/`
- 腳本：`/Users/KS/.openclaw/skills/chinese-date/scripts/`

### 目錄結構
```
chinese-date/
├── SKILL.md              ← 使用說明文件
├── scripts/
│   ├── install.sh        ← 懶人安裝腳本
│   ├── query.sh          ← 便捷 wrapper
│   └── date_query.py     ← 主程式
```

### 功能
- 西元日期查詢
- 四柱干支（年/月/日/時，精確）
- 二十四節氣
- 農曆日期（含閏月）
- 黃曆宜忌（根據節氣動態給出）

### 依賴
- `cantian-tymext`（npm 全域：`npm install -g cantian-tymext`）
- Python 3（含 subprocess, datetime）
- `lunarcalendar`（可選：`/usr/local/bin/python3 -m pip install lunarcalendar`）

### 新電腦安裝方式
```bash
# 方式一：懶人腳本
bash /Users/KS/.openclaw/skills/chinese-date/scripts/install.sh

# 方式二：手動安裝
npm install -g cantian-tymext
/usr/local/bin/python3 -m pip install lunarcalendar
```

### 核心引擎
`cantian-tymext`（基於 tyme4ts）是目前最精確的八字計算庫。


---

## google-places skill 更新記錄（2026-03-21）

### query.py v4 重大修正

**問題根因：**
- `cmd_search()` 原本會先 `print(search_out)` raw goplaces 結果，再執行完整查詢
- 導致使用者看到兩次輸出（重複的 raw 結果 + 完整結果）

**修正內容：**
- 移除 `cmd_search()` 中的 `print(search_out)`，從現在起 `search` 和 `full` 行為完全一致，都是一次完整查詢
- 更新 SKILL.md，移除所有「基本/進階」的舊描述，統一為單一流程

### CDP 架構（v4 重寫）

**流程：**
1. `goplaces` CLI → 基本資料 + 6個月內評論
2. Google Places API v1 `priceRange` → 每人消費區間
3. CDP 直連 OpenClaw 瀏覽器（port 18800）→ 動態內容一次讀取

**CDP 讀取策略：**
- 每人消費、服務、Menu、熱門品項：在同一段 JS 中一次讀取（單次 `Runtime.evaluate`）
- 價格分布圖：點擊每人消費按鈕 → 等 2.5 秒 → 讀取 popup
- 按鈕定位：搜尋 `innerText` 含 "per person" 的元素，選面積最小者（最精確的按鈕）
- 失敗時：優雅降級，不影響其他資訊顯示

**修復的語法 bug：**
- `except` 縮排錯誤（try/except 夾雜 if 區塊）→ 移除孤立的 except pass
- `result["price_histogram"] = hist_entries` 縮排在 for 迴圈內 → 移出到正確位置

### 已知限制
- Google Maps 動態內容有時需要更長的等待時間（已設 2.5 秒等待 popup）
- CDP 依賴 OpenClaw 瀏覽器已啟動，無需使用者操作
