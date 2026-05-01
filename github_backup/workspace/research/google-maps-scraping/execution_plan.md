# Google Maps 評論抓取項目：最終執行提案 (Final Execution Proposal)

## 1. 總體架構圖 (Overall Architecture)

本系統採取「分佈式調度 $\rightarrow$ 混合抓取 $\rightarrow$ 多級存儲」之數據流設計。

| 階段 | 組件 | 核心功能 | 數據流向 |
| :--- | :--- | :--- | :--- |
| **任務分發** | Celery + Redis | 管理抓取隊列、分發地點 ID、監控任務狀態 | $\text{Task Queue} \rightarrow \text{Worker}$ |
| **抓取執行** | Hybrid Scraping Engine | 執行 $\text{Internal API} \rightarrow \text{Playwright}$ 降級路徑 | $\text{Worker} \rightarrow \text{Google Maps}$ |
| **數據清洗** | Cleaning Pipeline | 格式化時間戳、剔除重複項、驗證 Schema 完整性 | $\text{Raw Data} \rightarrow \text{Clean Data}$ |
| **數據存儲** | MongoDB + PostgreSQL | 評論正文存儲 (NoSQL) 與 地點索引管理 (Relational) | $\text{Clean Data} \rightarrow \text{Databases}$ |

---

## 2. 詳細配置清單 (Configuration Blueprint)

### 2.1 身分特徵 (Persona)
必須為每組抓取 Worker 分配獨立且穩定的 **Stateful Persona**。嚴禁對單一請求進行隨機化，必須保證 Session 的連續性。

- **必須配置項**：
    - **User-Agent**：必須與瀏覽器版本精確匹配。
    - **視窗解析度**：固定為 $\text{1920} \times \text{1080}$，僅允許 $\pm \text{5\%}$ 的輕微偏移。
    - **語言與時區**：必須與代理伺服器所在地理位置 $\text{100\%}$ 一致 (Locale/Timezone)。
    - **持久化路徑**：必須使用 Playwright 的 `userDataDir` 保存 Cookie 與 LocalStorage。

### 2.2 代理配置 (Proxy Configuration)
- **代理類型**：強制使用 **住宅代理 (Residential Proxies)**。
- **輪詢策略**：
    - **綁定關係**：$\text{1 Persona} = \text{1 Static Residential IP}$。
    - **輪詢頻率**：僅在 Persona 被封禁 (403) 時執行 IP 更換，禁止在每個請求間切換。

### 2.3 技術棧清單 (Tech Stack)
| 組件 | 推薦版本 | 角色 |
| :--- | :--- | :--- |
| **Python** | $\ge \text{3.11}$ | 核心開發語言 |
| **Playwright** | 最新穩定版 | 瀏覽器自動化引擎 |
| **playwright-stealth** | 最新穩定版 | 繞過 Bot 檢測插件 |
| **Redis** | $\ge \text{6.0}$ | 任務隊列與 Bloom Filter 去重 |
| **Celery** | $\ge \text{5.0}$ | 分佈式任務調度 |
| **MongoDB** | $\ge \text{5.0}$ | 評論數據非結構化存儲 |
| **PostgreSQL** | $\ge \text{14}$ | 地點索引與元數據管理 |

---

## 3. 核心算法流程 (Algorithm Flow)

### 3.1 混合抓取路徑 (Hybrid Scraping Path)
系統必須遵循以下判定邏輯，以最大化效能並保證穩定性：

1. **優先路徑 (Fast Path)**：執行 `Internal API (Protobuf)` 請求。
2. **判定條件**：
    - 若返回 $\text{HTTP 200}$ 且數據完整 $\rightarrow$ **繼續執行 API 抓取**。
    - 若觸發 $\text{HTTP 403}$、$\text{CAPTCHA}$ 或 $\text{Empty Response}$ $\rightarrow$ **立即觸發降級路徑**。
3. **降級路徑 (Stable Path)**：
    - 切換至 **Playwright Stealth 模式**。
    - 模擬人類行為（隨機鼠標軌跡 $\rightarrow$ 頁面滾動 $\rightarrow$ 觸發 DOM 渲染）。
    - 重新獲取 Session Token / Cookies。
    - 成功後，嘗試切回 `Internal API` 路徑。

### 3.2 滾動與提取邏輯 (Scroll-Wait-Verify)
針對 Playwright 抓取，必須執行以下循環：

```python
# 偽代碼流程
while (current_reviews < target_limit) and (not end_of_page):
    1. 執行容器級滾動: scroll_down(element=review_container, distance=800)
    2. 執行高斯分佈延遲: wait(random.gauss(2.0, 0.5))
    3. 驗證數據增量: 
       if (count_elements(review_selector) > previous_count):
           mark_as_success()
       else:
           retry_with_jitter()
    4. 提取當前視窗內所有新評論
    5. 更新 previous_count
```

---

## 4. 數據 Schema 定義

最終存儲格式必須符合以下 JSON Schema：

```json
{
  "review_id": { "type": "string", "description": "Google 唯一評論 ID, 強制唯一" },
  "location_id": { "type": "string", "description": "地點唯一 ID" },
  "user": {
    "user_id": { "type": "string" },
    "display_name": { "type": "string" },
    "profile_photo_url": { "type": "string" }
  },
  "content": {
    "rating": { "type": "integer", "minimum": 1, "maximum": 5 },
    "text": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "translation": { "type": "string", "nullable": true }
  },
  "metadata": {
    "scraping_date": { "type": "string", "format": "date-time" },
    "persona_id": { "type": "string" },
    "method": { "type": "string", "enum": ["internal_api", "playwright"] }
  }
}
```

---

## 5. 部署與運維計劃 (Deployment & Ops)

### 5.1 部署環境
- **基礎設施**：強制使用 **Docker** 容器化部署。
- **編排方案**：
    - **開發/小規模**：`docker-compose` (1 Worker $\text{+} 1 Redis $\text{+} 1 MongoDB)。
    - **生產/大規模**：**Kubernetes (K8s)**，根據隊列長度動態擴展 Worker Pods。

### 5.2 監控指標 (KPIs)
必須建立實時監控看板，追蹤以下指標：
- **CAPTCHA 觸發率**：$\text{CAPTCHA Count / Total Requests}$ (閾值 $\text{> 5\%}$ 時觸發 Persona 告警)。
- **抓取成功率**：$\text{Successful Reviews / Attempted Reviews}$。
- **Persona 健康度**：單個 IP 的連續成功請求數。
- **數據完整度**：Schema 缺失字段之百分比。

---

## 6. 風險緩解方案 (Risk Mitigation)

| 風險場景 | 應對 SOP (標準作業程序) |
| :--- | :--- |
| **觸發 $\text{HTTP 403}$ 封禁** | 1. 立即停止該 Persona 所有任務 $\rightarrow$ 2. 標記 Persona 為 `Cooldown` $\rightarrow$ 3. 觸發 Playwright Token 刷新 $\rightarrow$ 4. 輪換住宅 IP。 |
| **DOM 結構變動** | 1. 監控到提取率驟降 ( $\text{< 20\%}$ ) $\rightarrow$ 2. 自動切換至 **Multi-Candidate Selector Library** 中的候選方案 $\rightarrow$ 3. 發送 Slack/Email 告警通知工程師更新選擇器。 |
| **數據重複抓取** | 1. 在寫入前強制執行 **Redis Bloom Filter** 檢查 $\text{review\_id}$ $\rightarrow$ 2. 若存在則直接捨棄，不進入清洗流程。 |
| **記憶體洩漏 (Browser)** | 1. 強制執行 `page.close()` 與 `browser.close()` $\rightarrow$ 2. 設置 Worker 最大任務數 ( $\text{Max Tasks per Process}$ )，達到閾值後自動重啟容器。 |
