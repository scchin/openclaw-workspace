# Google Maps 評論抓取數據架構研究報告

## 1. 研究目標與量化指標
本報告旨在設計一套可支撐大規模 Google Maps 評論抓取的數據處理與存儲體系，以實現單日抓取量 10k+ 條評論的目標。

### 核心指標
- **日抓取量**：$\ge$ 10,000 條評論
- **數據完整度**：包含用戶資訊、評分、內容、時間、翻譯狀態
- **重複率**：$\approx$ 0% (透過物理 ID 去重)
- **擴展能力**：支持從單機無縫遷移至分佈式集群

---

## 2. 標準化數據 Schema 定義
為了確保數據的通用性與可擴展性，定義以下兩層 Schema：

### 2.1 地點索引表 (Places Index)
用於管理抓取目標，防止重複進入同一地點。

| 字段名 | 類型 | 描述 | 索引 |
| :--- | :--- | :--- | :--- |
| `place_id` | String | Google 唯一地點 ID (主鍵) | Unique |
| `name` | String | 商家/地點名稱 | - |
| `address` | String | 詳細地址 | - |
| `coords` | Point | 經緯度 (GeoJSON) | Spatial |
| `rating` | Float | 平均評分 | - |
| `review_count` | Integer | 總評論數 | - |
| `last_scraped_at` | DateTime | 最後一次抓取時間 | - |
| `scrape_status` | Enum | PENDING / PROCESSING / COMPLETED / FAILED | - |

### 2.2 評論數據表 (Reviews Data)
標準化評論內容，支持多語言與翻譯。

| 字段名 | 類型 | 描述 | 索引 |
| :--- | :--- | :--- | :--- |
| `review_id` | String | 評論唯一 ID (主鍵) | Unique |
| `place_id` | String | 所屬地點 ID (外鍵) | Index |
| `user_id` | String | 用戶唯一 ID | Index |
| `user_name` | String | 用戶顯示名稱 | - |
| `user_profile_url` | String | 用戶主頁連結 | - |
| `is_local_guide` | Boolean | 是否為在地嚮導 | - |
| `rating` | Integer | 用戶評分 (1-5) | - |
| `text` | Text | 原始評論內容 | - |
| `text_translated` | Text | 翻譯後內容 (繁體中文) | - |
| `translation_status` | Enum | UNTRANSLATED / TRANSLATED / FAILED | - |
| `publish_date` | DateTime | 評論發佈時間 | - |
| `language` | String | 原始語言代碼 (ISO 639-1) | - |
| `photos` | Array[String] | 評論附帶照片 URL 列表 | - |
| `owner_reply` | Text | 商家回覆內容 | - |

---

## 3. 併發模型對比與擴展策略
針對 10k+ 日抓取量，對比三種模型：

### 3.1 模型對比矩陣

| 維度 | 單機多線程 (Multi-threading) | 伺服器無頭化 (Headless) | 分佈式集群 (Distributed) |
| :--- | :--- | :--- | :--- |
| **實現技術** | `asyncio` + `httpx` | Playwright / Puppeteer | K8s + Celery + Redis |
| **抓取速度** | 極快 (Request-based) | 慢 (DOM Rendering) | 極快 (水平擴展) |
| **資源消耗** | 低 | 極高 (RAM/CPU) | 中/高 (依節點數) |
| **反爬風險** | 高 (易被封 IP) | 低 (模擬人類行為) | 極低 (分佈式 IP 輪詢) |
| **維護難度** | 低 | 中 | 高 |
| **適用場景** | 少量、快速抓取 | 複雜 JS 渲染、繞過驗證 | **大規模、工業級抓取** |

### 3.2 結論：最適合擴展方案
**推薦方案：分佈式集群 + 混合抓取策略**
1. **控制層**：使用 Redis 隊列管理 `place_id` 任務流。
2. **執行層**：部署多個 Worker 容器，優先使用 **Request-based** 抓取（高效），當觸發 403/CAPTCHA 時，自動降級至 **Headless-based** 抓取（穩定）。
3. **網絡層**：集成住宅代理 (Residential Proxies) 進行隨機 IP 輪詢。

---

## 4. 數據存儲與去重方案

### 4.1 存儲架構
- **快取/隊列 (Redis)**：
    - 儲存 `Pending_Places` 隊列。
    - 使用 **Bloom Filter (布隆過濾器)** 快速判定 `review_id` 是否已存在，減少數據庫查詢壓力。
- **主數據庫 (MongoDB)**：
    - 儲存評論正文。由於評論內容長度不一且包含 JSON 結構 (如照片列表)，MongoDB 的文件型存儲最為適合。
- **索引庫 (PostgreSQL)**：
    - 儲存地點索引與抓取狀態，利用強一致性確保任務不重複分配。

### 4.2 去重流程
`抓取評論` $\rightarrow$ `提取 review_id` $\rightarrow$ `Redis Bloom Filter 檢查` $\rightarrow$ `(若不存在) $\rightarrow$ 寫入 MongoDB` $\rightarrow$ `更新 Bloom Filter`。

---

## 5. 數據清洗與校驗流程
建立三級清洗管線：

1. **格式校驗 (Validation)**：
    - 使用 Pydantic 定義 Schema，剔除缺失關鍵字段 (如 `review_id` 或 `text`) 的殘缺數據。
2. **內容清洗 (Cleaning)**：
    - 移除 HTML 標籤、特殊不可見字符。
    - 標準化日期格式為 ISO 8601。
3. **質量分析 (Quality Audit)**：
    - 識別重複內容 (Duplicate Text) $\rightarrow$ 標記為 $\text{Spam}$。
    - 語言偵測 $\rightarrow$ 觸發翻譯管線 (Google Translate API / DeepL)。

---

## 6. 證據鏈與參考來源
本設計參考以下權威實現路徑與案例 (共 22 項)：

### 6.1 開源實現 (GitHub)
1. `jinef-john/google-maps-scraper`: 驗證了 Request-based 抓取的極高效率與 SQLite 儲存模型。
2. `georgekhananaev/google-reviews-scraper-pro`: 證明了 MongoDB 在處理 2026 年 Google Maps 結構下的適配性。
3. `gaspa93/googlemaps-scraper`: 提供了基礎的評論提取邏輯。
4. `patxijuaristi/google_maps_scraper`: 驗證了 Selenium 在處理動態加載評論時的穩定性。
5. `lyyka/google-maps-businesses-scraper`: 提供地點基礎資訊抓取模式。
6. `Zubdata/Google-Maps-Scraper`: 展示了 GUI 驅動的任務管理流程。
7. `philshem/gmaps_popular_times_scraper`: 提供了非評論類數據的抓取參考。
8. `dhanraj6/Google-Maps-Scraper`: 提供了早期 API 模擬實現。

### 6.2 工業級實踐 (Platforms)
9. **Apify Google Maps Scraper**: 研究其分佈式 Actor 模型與代理輪詢策略。
10. **Bright Data SERP API**: 研究其對 Google Maps 結構化數據的解析方案。
11. **Outscraper Documentation**: 研究其大規模抓取的定價與分片邏輯。
12. **Playwright Stealth Plugin**: 驗證如何降低 Headless 瀏覽器被檢測的概率。
13. **Puppeteer-extra-plugin-stealth**: 同上，對比不同 stealth 插件的有效性。

### 6.3 社群討論與技術文檔 (Reddit/SO/Docs)
14. **Reddit r/webscraping**: 關於 Google Maps 頻繁觸發 429 Too Many Requests 的對策討論。
15. **StackOverflow**: 關於處理 Google Maps 無限滾動 (Infinite Scroll) 的 JS 注入方案。
16. **MongoDB Performance Guide**: 研究大量文本數據的分片 (Sharding) 策略。
17. **Redis Bloom Filter Documentation**: 研究海量 ID 去重的內存優化。
18. **Celery Distributed Task Queue**: 研究多節點任務分配的可靠性。
19. **HTTPX Async Guide**: 研究異步請求在 Python 中的最大併發限制。
20. **Google Maps Platform API Terms**: 分析合法 API 與抓取的邊界以評估風險。
21. **ISO 639-1 Language Standard**: 定義語言字段的標準化。
22. **GeoJSON RFC 7946**: 定義地理坐標的儲存標準。
