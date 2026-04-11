---
name: google-places
description: 查詢 Google Maps 地點完整資訊（地址、電話、經緯度、營業時間、評分、用戶評論、用戶反饋價格、每人消費含分布圖、服務、Menu、熱門品項、特色菜色）。CDP 直連 OpenClaw 瀏覽器讀取 Google Maps 動態頁面，輪詢策略確保所有資訊完整載入。⚠️ 這是所有地點查詢的預設方式與天條：廁所、停車場、美術館、旅館、飯店、圖書館、博物館、公園、學校、景點、餐廳、加油站等全部適用。
author: King Sean of KS
---

# Google Places 地點查詢（query.py v10.5（2026-04-06：get_reviews() months 參數化，預設 None（無時間限制）；網友心得改用全量評論（all_reviews）；cmd_search/cmd_full/cmd_details 維持6個月限制用於價格回饋））

## 單一指令（自動完整查詢）

收到地點查詢請求時，執行以下三步，全部自動化，無需使用者操作瀏覽器：

1. **goplaces CLI** → 基本資料、6個月內評論
2. **Google Places API v1** → 每人消費區間（priceRange）
3. **CDP 直連 OpenClaw 瀏覽器**（輪詢策略）→ 每人消費分布圖、服務、Menu、熱門品項

所有資訊一次呈現，不分階段。

### 資料來源分工（重要）

| 欄位 | 資料來源 | 說明 |
|------|----------|------|
| 💵 每人消費 | **Google Places API v1** (`priceRange`) | API 即時回傳，如 `$1–$200`。**非爬蟲**，是 Google 官方欄位，部分店家無此資料 |
| 💬 用戶反饋價格 | **goplaces 6個月內評論**文字解析 | 正規表達式搜尋 `$數字` 格式，純文字比對，準確率高但依賴評論提及 |

```
query.py 內部邏輯：
get_price_range_api(place_id)          → 💵 每人消費（Google Places API）
get_reviews(place_id) + price parsing  → 💬 用戶反饋價格（評論文字）
```

**為何有兩個價格來源？**
- API `priceRange` 是 Google 官方彙總，懶人首選，但並非每間店都有
- 用戶反饋是網友親自留言的實際消費金額，更具體但需要湊齊足夠樣本

---

```bash
# 搜尋關鍵詞，自動執行完整查詢
cd ~/.openclaw/skills/google-places
.venv/bin/python scripts/query.py search "鰄老闆捲起來"

# 直接以 place_id 查詢（等同完整查詢）
python scripts/query.py full ChIJs9ZwdXQXaTQRa5LL3bcnLq4

# 搜尋時加地理限制
python scripts/query.py search "火鍋" --lat 24.16659 --lng 120.667087 --radius-m 1000 --min-rating 4
```

> **CDP 瀏覽器需求**：query.py 透過 port 18800 連線到 Edge CDP server，**不自己啟動 Edge**。
> 使用前需先啟動瀏覽器（兩種方式）：
> 1. **（推薦）用 `browser` 工具啟動 `openclaw` profile**：`browser(action="start", profile="openclaw")` → 再執行查詢
> 2. 若 Edge 已以 `--remote-debugging-port=18800` 運行，query.py 會自動複用
>
> CDP 會透過 `Target.createTarget` 建立 Maps 分頁，**不會多開新 Edge 視窗**。
> 若 CDP 完全失效，goplaces API 基本資料仍正常顯示，CDP 部分（每人消費分布圖、服務、Menu、熱門品項）會顯示「無法讀取」。

---

## 輸出格式

```
==================================================
🏪 店名：鰄老闆卷起來(漢口店宵夜場)–澎湖小卷、海鮮粥、蝦滷飯、脆皮燒肉

📍 地址：台中市北區漢口路3段32號（404）
📍 經緯度：24.16659, 120.667087
📞 電話：0965 462 948
⭐ 評分：4.8（177則）
🚦 狀態：❌ 休息中（今日 5:30 PM – 2:00 AM）

🌐 網站：https://www.facebook.com/mammymambo/
🔗 Google Maps：https://www.google.com/maps/place/?q=place_id:ChIJs9ZwdXQXaTQRa5LL3bcnLq4
🍽️ Menu：https://store.dudooeat.com/order/store/f7a3eee9f71f4c2cb24ba41cc1bc1178

💵 每人消費：$1–200（71人回報）
   ▓▓▓▓░░░░░░  $1–200  ～34人（48%）
   ▓▓▓▓░░░░░░  $200–400  ～30人（42%）
   ░░░░░░░░░░  $400–600  ～3人（4%）

📌 服務：內用、外帶、外送
🍜 熱門品項：空間（7則）｜調酒（7則）｜聚餐（4則）｜唱歌（3則）

🔥 特色菜色：蝦滷飯、脆皮燒肉、辣椒、海鮮炒麵、油蔥蝦仁飯

📝 網友心得：
王仁偉：辣椒很辣，喜歡吃辣務必試試
林小雨：環境乾淨，桌距大不擁擠
Yao Wang：蝦子有幫忙剝殼大加分

💬 用戶反饋價格（6個月內）：
· LISON（5⭐，44天前）提及：$85, $100
  「一切還好，海鮮粥，干貝嗎？有炙燒滿酷的！…」
==================================================
```

### 排版規則

- **每項資訊一行**：店名、地址、經緯度、電話、評分、狀態、網站、Google Maps、Menu、每人消費、服務、熱門品項，全部各自獨立一行
- **⚠️ Webchat 顯示規則（v2.14 強制執行）：** webchat 對純 `\n` 換行支援極差，所有內容會全部黏在同一行。**輸出時必須將原始輸出包在 Triple backticks（```）程式區塊中**，才能正確保留換行。

**固定格式（每次都這樣用，寫死，2026-03-24 修正）：**
```
```
{原始輸出本尊，完整一字不漏，保留所有換行}
```
```

**⚠️ 绝不可省略的執行步驟（2026-03-24 修正）：**
1. 拿到原始輸出後，「原封不動」放進 ``` ``` ``` 這個殼裡（直接用 Enter 換行，不使用 \n 字元）
2. 完全不做任何濃縮、刪減、重新組織
- **🏪 店名**：自動去除 pipe 標籤（`|` 後面的分類詞全部移除，只保留正式名稱）
- **`💵 每人消費`**：API `priceRange` 優先，CDP 分布圖附長條圖（展開在每人消費下方）
- **`📌 服務`**：從頁面「關於」區塊動態解析（內用/外帶/外送/寵物友善/預約等）
- **`🍜 熱門品項`**：從評論摘要區塊抓取（支援新舊兩種 DOM 格式）
- **`🔥 特色菜色`**：所有菜色併為一行
- **`📝 網友心得`**：標題一行 + 每則心得一行（作者：內容），超過 150 字自動截斷
- **`💬 用戶反饋價格`**：標題一行 + 每則一行（提及：價格），原文引用若超過 150 字做智慧摘要
- **`🚦 狀態`**：`✅ 營業中（今日 HH:MM – HH:MM，距離關門 X 小時 Y 分鐘）` 或 `❌ 休息中（今日 HH:MM – HH:MM）`

---

## CDP 原理（v10）

```
query.py full / search
  │
  ├─ goplaces details + get_reviews()
  │     → 基本資料、6個月內評論（含用戶價格反饋）
  │
  ├─ Google Places API v1 / priceRange
  │     → "$1–200"
  │
  └─ CDP 直連 OpenClaw 瀏覽器
       │
       ├─ Phase 1：取得 Maps 分頁 WS URL（健康檢查 ping）
       │         → 若無 Maps 分頁，建立新分頁
       │         → 導航到目標店家（嚴格載入驗證）
       │
       ├─ Phase 2：點擊「菜單」「評論」「總覽」標籤讀取各類資訊
       │         → 「菜單」：抓取 Menu URL（支援 Instagram / Dudooeat /
       │                      inline_menu / UberEats / Foodpanda / Chope 等）
       │         → 「評論」：抓取熱門品項（支援舊版 role=radio[aria-label*=mentioned]
       │                      以及新版 radiogroup > radio 格式）
       │         → 「總覽」：抓取每人消費、服務（從 DOM 關鍵字動態解析）
       │         → 最多 8 輪滾動輪詢，連續 3 輪內容不增加時提前結束
       │
       └─ Phase 3：點擊「平均每人」右側箭頭按鈕（而非整個文字區塊）
                  → 四種解析策略：table aria-label / aria-live /
                  →   people+%$ div / dialog histogram
                  → 等 popup 彈出（4.0 秒）
                  → 百分比 → 人數估算
```

---

## 新電腦安裝

```bash
# 1. 安裝 goplaces
brew install steipete/tap/goplaces

# 2. 設定 API Key
export GOOGLE_PLACES_API_KEY="你的金鑰"

# 3. CDP 依賴（僅 websockets）
uv venv ~/.openclaw/skills/google-places/.venv --python 3.12
uv pip install --python ~/.openclaw/skills/google-places/.venv/bin/python websockets

# 4. 執行查詢（完整，一次完成）
cd ~/.openclaw/skills/google-places
.venv/bin/python scripts/query.py search "鰄老闆卷起來"
```

> **查詢前**：需先啟動 Edge：`browser(action="start", profile="openclaw")`

---

## 已知限制

- 「每人消費」由 Google Maps 用戶回報，非店家提供，部分店家無此資料時顯示「店家未提供」
- CDP 依賴 OpenClaw 瀏覽器 CDP server（port 18800），瀏覽器未啟動時 CDP 部分顯示「無法讀取」
- 價格分布人數由百分比估算，與實際回報數可能略有差異
- 「用戶反饋價格」從評論文字解析，僅供參考
- 分布圖僅在回報人數足夠（通常 20+）時才會出現，11 人回報通常只有單一區間
