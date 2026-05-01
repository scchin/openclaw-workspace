# 📦 跨平台數據採集路徑落地報告 (Collection Report)
**負責專家**: `social_collector_expert`
**日期**: 2026-04-25

## 1. 核心目標
建立一套可擴展、低成本且能繞過反爬蟲機制的社群數據獲取流水線，支持主流社交平台 (X, TikTok, IG, FB, 小紅書, Dcard, Threads)。

## 2. 採集技術矩陣 (Tech Matrix)

| 平台 | 推薦工具/路徑 | 採集難度 | 關鍵技術點 | 建議方案 |
| :--- | :--- | :--- | :--- | :--- |
| **X (Twitter)** | Official API v2 / `snscrape` | 中 | OAuth 2.0 / DOM 解析 | 優先 API → 補充 Scraper |
| **TikTok** | `TikTok-Api` (Python) / `yt-dlp` | 高 | Signature (msToken, X-Bogus) | 模擬移動端 Header / 第三方 API |
| **Instagram** | `instaloader` / Apify | 高 | Session Cookie / Rate Limit | 使用多帳號池 (Account Pool) |
| **Facebook** | `facebook-scraper` / Browser Automation | 極高 | 嚴格封號機制 | 僅採集公開 Page /  headless browser |
| **小紅書** | Mobile API Reverse / Playwright | 高 | 簽名驗證 (x-s, x-t) | 攔截 HTTPS 流量 → 模擬請求 |
| **Dcard** | Public JSON API | 低 | 直接請求 / 簡單分頁 | 直接使用 `requests` 抓取 JSON |
| **Threads** | Web Scraping (Playwright) | 中 | 動態加載 / React-based DOM |  headless browser 定時快照 |

## 3. 實作路徑 (Implementation Path)

### A. 基礎設施層 (Infrastructure)
- **代理池 (Proxy Pool)**: 必須部署住宅代理 (Residential Proxies) 以防止 IP 被封鎖 (推薦 Bright Data 或 Oxylabs)。
- **指紋偽裝 (Fingerprinting)**: 使用 `undetected-chromedriver` 或 Playwright 的 `stealth` 插件，繞過 Cloudflare 及其他 WAF。
- **帳號管理**: 建立帳號輪詢機制 (Rotation)，避免單一帳號觸發安全機制。

### B. 採集流程 (Workflow)
`目標 URL` → `代理分配` → `指紋模擬` → `數據抓取` → `HTML/JSON 清洗` → `存入數據湖 (MongoDB)`。

## 4. 潛在風險與對策
- **反爬升級**: 實施「隨機延時」與「行為模擬」(Random Sleep, Mouse Movement)。
- **法律合規**: 僅採集公開數據，剔除個資 (PII) 脫敏處理。
- **API 成本**: 優先使用開源工具 → 核心需求轉向付費 API → 自建爬蟲集群。

## 5. 結論
目前最可行的路徑是 **「混合模式」**：針對低門檻平台 (Dcard) 使用直接 API，針對高門檻平台 (TikTok, IG) 使用 Playwright + 住宅代理。
