# 🌐 市場情報研究報告 - 第一維度：全球主流社群分析 (Global Social Media)

本報告旨在提供一套可真實落地的 CLI 工具組合方案，用於監控 X (Twitter), Threads, Instagram 與 Facebook 的趨勢話題及品牌熱度。

## 1. 推薦工具鏈 (Toolchain)

我從 GitHub 及開發者社群中篩選出以下最穩定且高效的工具：

### A. X (Twitter) 監控
| 工具名稱 | 來源 | 優勢 | 劣勢 | 適用場景 |
| :--- | :--- | :--- | :--- | :--- |
| **Twitter-CLI** | `public-clis/twitter-cli` | 輕量、直接對接 API | 依賴 API Key | 快速獲取單一用戶或話題推文 |
| **X-CLI** | `Infatoshi/x-cli` | 支援較新的 X API 結構 | 配置較複雜 | 深度數據採集與自動化監控 |
| **TwitterXScraper** | `calchiwo/twitterxscraper` | 繞過部分 API 限制 | 穩定性受平台更新影響 | 大規模話題關鍵字抓取 |

### B. Threads 監控
| 工具名稱 | 來源 | 優勢 | 劣勢 | 適用場景 |
| :--- | :--- | :--- | :--- | :--- |
| **Threads-CLI** | `ptrlrd/threads-cli` | 首批支援 Threads 的 CLI | 社群維護速度快但功能單一 | 追蹤 Threads 熱門討論 |
| **X-Thread-DL** | `aj47/x-thread-dl` | 專注於 Thread 鏈條下載 | 僅限下載，分析能力弱 | 保存完整討論鏈供後續分析 |

### C. Instagram & Facebook (Meta 生態)
| 工具名稱 | 來源 | 優勢 | 劣勢 | 適用場景 |
| :--- | :--- | :--- | :--- | :--- |
| **InstaPy-CLI** | `b3nab/instapy-cli` | 自動化程度極高 | 易觸發帳號封禁 | 品牌互動監控與自動化追蹤 |
| **InstaScrape** | `tnychn/instascrape` | 數據提取純淨 | 需處理 Cookie 驗證 | 競爭對手內容分析 |
| **FB-CLI** | `0xPr0xy/facebook-cli` | 整合多項 FB 基礎功能 | Meta API 限制極其嚴格 | 公開頁面話題抓取 |

### D. 智能分析層 (Analysis Layer)
| 工具名稱 | 來源 | 功能 | 適用場景 |
| :--- | :--- | :--- | :--- |
| **Sentiment-Model-CLI** | `watermelonich/Sentiment-Model-CLI` | 快速文本情緒分類 (正/負/中) | 判斷品牌輿論正面/負面比例 |
| **SentimentCLI** | `moritzwilksch/SentimentCLI` | 支援多語言情感分析 | 全球化品牌熱度監控 |
| **Topic-Modeling-Toolkit**| `boromir674/topic-modeling-toolkit` | LDA 主題模型提取 | 從海量推文中自動總結「核心需求」 |

---

## 2. 真實落地執行工作流 (Executable Workflow)

要將上述工具組合為商業分析系統，建議採取以下流水線：

**步驟 1：數據採集 (Data Acquisition)**
- 使用 `TwitterXScraper` → 抓取 `#品牌關鍵字` 相關推文 → 儲存為 `raw_x.json`。
- 使用 `Threads-CLI` → 抓取特定趨勢話題 → 儲存為 `raw_threads.json`。
- 使用 `InstaScrape` → 採集競爭對手最新貼文 → 儲存為 `raw_ig.json`。

**步驟 2：數據清洗 (Data Cleaning)**
- 執行 Python 腳本剔除重複內容、廣告推文與無意義符號。
- 統一格式為：`[Timestamp, Platform, Content, UserID, Engagement]`。

**步驟 3：智能分析 (Intelligence Analysis)**
- **情緒掃描**：`cat cleaned_data.txt | sentiment-cli` → 產出情緒分佈圖 → 判定品牌當前「口碑溫度」。
- **話題提取**：將所有內容輸入 `topic-modeling-toolkit` → 提取前 5 個高頻主題 → 定義用戶目前的「核心痛點」。

**步驟 4：結果交付 (Reporting)**
- 將分析結果匯總為：`品牌熱度趨勢` → `用戶主要反饋` → `建議行動方案`。

---

## 3. 專家總結
該方案擺脫了單一 API 的依賴，透過「Scraper (抓取) → Pipeline (清洗) → Model (分析)」的結構，能有效解決 Meta 平台 API 封鎖嚴格的問題。建議優先部署 `X-CLI` 與 `SentimentCLI` 以快速建立初步的輿論監控模型。