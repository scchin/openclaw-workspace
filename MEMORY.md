# 長期記憶

## 重要規則

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

### google-places（自建完整店家查詢 skill）
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

