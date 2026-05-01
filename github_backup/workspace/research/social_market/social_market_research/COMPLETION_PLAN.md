# 🛠️ 社交媒體分析項目：內容補完計畫 (v2.0)

## 1. 項目目標
將 v1.0 提案從「框架級」提升至「操作級」，填補執行細節缺口，確保每一項技術路徑都有 20 篇頂尖文獻/案例支撐。

## 2. 補完任務清單 (總計 80 篇研究)

### A. 需求驗證深度補完 (Expert C) - 20 篇
- **目標**：建立 \text{Demand\_Validation\_SOP}。
- **研究重點**：量化問卷設計、抽樣偏差修正、定性分析轉化、統計相關性校驗。
- **產出**：從「痛點」→ 「問卷」→ 「定論」的標準執行流程。

### B. 採集層：帳號池維護 SOP (Expert A) - 20 篇
- **目標**：解決大規模採集中的「帳號生命週期管理」。
- **研究重點**：高效註冊路徑、帳號權限維護、封號預警機制、自動化輪詢替換流程。
- **產出**：\text{Account\_Management\_SOP}。

### C. 分析層：Prompt 工程模板 (Expert B) - 20 篇
- **目標**：提供可直接複製的 LLM 標記指令。
- **研究重點**：Few-shot prompting for ABSA, 金標籤 (Gold Label) 生成邏輯, 減少 LLM 幻覺的約束指令。
- **產出**：\text{Prompt\_Library\_for\_ABSA}。

### D. 驗證層：實戰案例模擬 (Expert C) - 20 篇
- **目標**：提供從 0 到 1 的完整演示路徑。
- **研究重點**：分析真實產品案例 → 模擬痛點提取 → 模擬問卷投放 → 模擬決策轉化。
- **產出**：\text{Case\_Study\_Simulation.md}。

## 3. 執行里程碑
- [ ] **T+1**: 啟動四項研究任務 → 進入數據挖掘階段。
- [ ] **T+2**: 完成 80 篇文獻研讀 → 產出四份詳細補完報告。
- [ ] **T+3**: 總主持人進行整合 → 更新 \text{FINAL\_PROPOSAL.md} 至 v2.0。
- [ ] **T+4**: 交付最終完整版指南。

---

## 📚 整合資源庫與歷史提案 (Integrated Resource Library & Historical Proposals)

本章節整合了項目早期的核心提案、專家深度報告及技術資源庫，作為 v2.0 補完計畫的基礎參考。

### 第一部分：🚀 最終執行指南 (FINAL PROPOSAL - Historical Version)

#### 1. 執行摘要 (Executive Summary)
本方案旨在建立一套從「社交媒體雜訊」到「商業決策指標」的自動化流水線。通過整合 OSINT 採集、NLP 面向方面的情緒分析 (ABSA) 以及商業需求驗證模型，將輿論趨勢轉化為可量化的產品迭代路徑。

**核心交付物**:
跨平台數據採集集群 → 輿論量化看板 → 需求驗證報告 → 產品優先級 Roadmap。

#### 2. 技術架構 (Technical Architecture)
- **數據獲取層 (Data Acquisition)**:
    - 低門檻 (JSON/API): Dcard, X (Official API) → 直接請求 → MongoDB。
    - 高門檻 (JS-Heavy/Anti-Bot): TikTok, Instagram, 小紅書, Threads → Playwright (Stealth) → Residential Proxy (Bright Data) → MongoDB。
    - 關鍵配置: User-Agent 隨機化 + TLS Fingerprinting 偽裝；建立帳號池 (Account Pool) 進行輪詢，單帳號請求間隔 60s。
- **數據處理與分析層 (NLP Pipeline)**:
    - 清洗: Custom Preprocessing → 剔除 Bot → 俚語標準化。
    - 聚類 (Discovery): 使用 BERTopic → 將海量文本自動分群為 5-10 個核心話題。
    - 量化 (Quantification): 使用 RoBERTa-ABSA 提取每個話題下「產品維度」的 Sentiment Score [-1, 1]；計算 Velocity (話題增速) → 識別爆發性需求。
- **商業驗證層 (Business Validation)**:
    - 映射: 高頻率 + 低滿意度 (Negative Sentiment) → 定義為「核心痛點」。
    - 驗證: 從相關話題中提取關鍵詞 → 生成定向問卷 → 投放至同一社群 → 比較社群自發情緒與問卷受控回答的一致性 → 確定需求真實度。

#### 3. 工具鏈清單 (Tooling Stack)
| 模組 | 推薦工具 | 用途 | 替代方案 |
| :--- | :--- | :--- | :--- |
| 採集 | Playwright + Python | 動態網頁抓取 | Selenium / Scrapy |
| 代理 | Bright Data / Oxylabs | 繞過 IP 封鎖 | 自建 Proxy Pool |
| 存儲 | MongoDB | 非結構化文本存儲 | PostgreSQL (JSONB) |
| 分析 | BERTopic / HuggingFace | 話題聚類與情緒分析 | GPT-4o |
| 驗證 | Typeform / Qualtrics | 定向需求驗證問卷 | Google Forms |
| 可視化 | Grafana / Tableau | 實時輿論監控看板 | Streamlit |

#### 4. 標準執行步驟 (SOP)
- **Step 1 (Setup)**: 部署 MongoDB → 配置 Playwright 環境 → 採購住宅代理。
- **Step 2 (Crawling)**: 執行定向關鍵字採集 → 存儲至 MongoDB。
- **Step 3 (Clustering)**: 運行 BERTopic → 輸出 `Topic_Map.csv` → 審核話題類別。
- **Step 4 (Sentiment)**: 運行 ABSA 模型 → 產出 \text{Aspect-Sentiment Matrix}。
- **Step 5 (Mapping)**: 將矩陣填入優先級矩陣 → 篩選 Top 3 痛點。
- **Step 6 (Validation)**: 撰寫問卷 → 社群投放 → 收集結果 → 修正結論。
- **Step 7 (Output)**: 產出最終產品迭代建議書。

#### 5. 風險預估與對策 (Risk Management)
- **帳號大規模封鎖**: 降低採集頻率 → 增加帳號池 → 切換至第三方 API。
- **模型分析偏差**: 引入 LLM 進行 5% 數據的隨機抽檢 → 修正標籤 → 重新訓練。
- **數據合規問題**: 嚴格執行 PII (個資) 脫敏 → 僅儲存聚合指標 → 不儲存用戶 ID。

---

### 第二部分：🔬 詳細專家報告 (Detailed Reports)

#### 1. 跨平台數據採集路徑報告 (by OSINT Expert)
- **核心目標**: 建立一套可擴展、低成本且能繞過反爬蟲機制的社群數據獲取流水線。
- **採集技術矩陣**:
    - X (Twitter): 優先 Official API → 補充 snscrape。
    - TikTok: 模擬移動端 Header → 使用 TikTok-Api / yt-dlp。
    - Instagram: 使用多帳號池 (Account Pool) → instaloader / Apify。
    - Facebook: 僅採集公開 Page → Headless Browser。
    - 小紅書: 攔截 HTTPS 流量 → 模擬請求 → Playwright。
    - Dcard: 直接使用 requests 抓取 Public JSON API。
    - Threads: Headless Browser 定時快照 → Playwright。
- **實作關鍵**: 必須部署住宅代理 (Residential Proxies) 與指紋偽裝 (undetected-chromedriver)。

#### 2. 輿論分析與 NLP 框架報告 (by NLP Expert)
- **核心目標**: 將碎片化、非結構化的社交媒體文本轉化為可量化的商業指標。
- **分析流水線 (Pipeline)**:
    - 預處理: 雜訊過濾 → 俚語標準化 → SpaCy 命名實體識別 (NER)。
    - 量化提取: 情感量化 (VADER → RoBERTa-ABSA)；話題聚類 (BERTopic)；趨勢預測 (Velocity = Volume/Time)。
- **商業指標轉化**:
    - 正負面比 → 品牌健康度；話題熱度 → 市場關注點；情緒極值 → 用戶痛點。

#### 3. 市場調查落地報告 (by Market Architect)
- **核心目標**: 建立從發現需求 → 驗證需求 → 產出產品建議的閉環體系。
- **商業分析模型**:
    - 需求發現: 識別高增速話題 → 定義「潛在市場機會」。
    - 需求驗證: 定向問卷 → 深度訪談 (Jobs-to-be-Done) → 交叉驗證 (量 + 質 + 參照)。
    - 商業轉化: 構建競爭定位圖 與 優先級矩陣 → 決定產品 Roadmap。

---

### 第三部分：🤝 技術審查與整合紀錄 (Integration Notes)

- **整合路徑圖**: 數據採集 (Expert A) → 量化分析 (Expert B) → 商業驗證 (Expert C) → 執行提案 (Final)。
- **關鍵衝突解決方案**:
    - **規模 vs. 限制**: 引入「兩段式採集法」。先小規模抽樣驗證模型，再針對核心維度進行精準大規模採集。
    - **噪聲 vs. 精度**: 在 NLP 流水線中增加 「LLM 金標校準」 步驟，利用 GPT-4o 對小部分數據進行高品質標記，以此指導輕量化模型的訓練與推論。
- **最終交付標準**: 方案必須包含：物理可行性清單、需求驗證模板、風險緩衝方案。

---

### 📚 附錄：核心技術資源與工具清單 (綜合版)

本清單整合了三位專家研讀的 60+ 項核心工具與連結，分為三個專業模組。

#### 📦 模組一：OSINT 與社群採集專家 (數據獲取層)
| 序號 | 名稱 | 簡介 | 備註 | 連結 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | snscrape | 強大的社交媒體爬蟲 | 繞過 API 限制 | [GitHub](https://github.com/snoozing-snscrape/snscrape) |
| 02 | TikTok-Api | Python 封裝的 TikTok 非官方 API | 需處理 msToken | [GitHub](https://github.com/davidteather/TikTok-Api) |
| 03 | instaloader | Instagram 數據下載與分析工具 | 建議搭配帳號池 | [GitHub](https://github.com/instaloader/instaloader) |
| 04 | facebook-scraper | 專門針對 FB 公開頁面抓取 | 控制請求頻率 | [GitHub](https://github.com/facebook-scraper/facebook-scraper) |
| 05 | Playwright | 現代化端到端自動化瀏覽器 | JS 動態加載核心 | [Official](https://playwright.dev/) |
| 06 | Apify | 商業級 Web Scraping 平台 | 穩定社群爬蟲 | [Official](https://apify.com/) |
| 07 | Bright Data | 全球最大住宅代理網路 | 解決 IP 封鎖 | [Official](https://brightdata.com/) |
| 08 | Social Analyzer | 全網社交帳號搜尋分析工具 | 定位用戶分佈 | [GitHub](https://github.com/qeeqbox/social-analyzer) |
| 09 | Sherlock | 跨平台用戶名搜尋工具 | 核實帳號存在性 | [GitHub](https://github.com/sherlock-project/sherlock) |
| 10 | Maigret | 進階版個人識別 OSINT 工具 | 生成個體關係圖 | [GitHub](https://github.com/soxsane/maigret) |
| 11 | Scrapy | 業界標準大規模爬蟲框架 | 構建複雜系統 | [Official](https://scrapy.org/) |
| 12 | BeautifulSoup | Python HTML/XML 解析庫 | 清洗原始數據 | [Official](https://www.beautifulsoup.com/) |
| 13 | Selenium | 傳統瀏覽器自動化工具 | 複雜人類交互 | [Official](https://www.selenium.dev/) |
| 14 | undetected-chromedriver | 繞過 Cloudflare/WAF 的 Driver | 解決 Bot 偵測 | [GitHub](https://github.com/ultrafunkamsterdam/undetected-chromedriver) |
| 15 | cloudscraper | 繞過 Cloudflare 的 Python 庫 | 處理 HTTPS 攔截 | [GitHub](https://github.com/cloak-it/cloudscraper) |
| 16 | yt-dlp | 視頻元數據與內容下載工具 | TikTok/YouTube 採集 | [GitHub](https://github.com/yt-dlp/yt-dlp) |
| 17 | Dcard API | Dcard 內部公開 JSON 接口 | 低門檻高效路徑 | [Dcard Dev](https://dcard.tw/) |
| 18 | MongoDB | 靈活的 NoSQL 數據庫 | 存儲非結構文本 | [Official](https://www.mongodb.com/) |
| 19 | TLS Fingerprinting | 研究 HTTPS 握手特徵 | 解決協議級攔截 | [Research](https://github.com/ja3er/ja3) |
| 20 | GDPR Compliance | 歐盟通用數據保護條例 | 確保法律安全性 | [Official](https://gdpr-info.eu/) |

#### 🧠 模組二：NLP 分析專家 (量化分析層)
| 序號 | 名稱 | 簡介 | 備註 | 連結 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | BERT | Transformer 基礎模型 | 現代分析基石 | [Google](https://github.com/google-research/bert) |
| 02 | BERTopic | SOTA 話題聚類工具 | 提取熱門話題 | [Official](https://maartengr.github.io/BERTopic/) |
| 03 | VADER | 社交媒體專用情緒分析 | 處理 Emoji/俚語 | [GitHub](https://github.com/cjhutto/vaderSentiment) |
| 04 | RoBERTa | 優化版 BERT | ABSA 情感量化 | [Facebook AI](https://github.com/facebookresearch/fairseq) |
| 05 | Hugging Face | 全球最大預訓練模型庫 | 部署 SOTA 模型 | [Official](https://huggingface.co/) |
| 06 | GPT-4o | LLM 零樣本標記 | 建立金標數據集 | [OpenAI](https://openai.com/) |
| 07 | LDA | 隱含狄利克雷分佈模型 | 建立分析基準線 | [Research] |
| 08 | SpaCy | 高效 NLP 處理庫 | 命名實體識別 (NER) | [Official](https://spacy.io/) |
| 09 | UMAP | 維度縮減算法 | 視覺化話題分佈 | [GitHub](https://github.com/lmcinnes/umap) |
| 10 | HDBSCAN | 密度 l-基聚類算法 | 自動識別群集數量 | [GitHub](https://github.com/lesuyuan/hdbscan) |
| 11 | c-TF-IDF | 類別-TF-IDF | 提取話題代表詞 | [BERTopic](https://maartengr.github.io/BERTopic/) |
| 12 | Sentence-BERT | 句子級別向量化 | 計算語義相似度 | [SBERT](https://www.sbert.net/) |
| 13 | ABSA Framework | 面向方面的情緒分析框架 | 產品維度量化 | [Research] |
| 14 | VADER Sentiment | 快速情緒極性判定 | 實時數據流分析 | [GitHub] |
| 15 | NLTK | 自然語言工具包 | 基礎文本分詞與清洗 | [Official](https://www.nltk.org/) |
| 16 | TextBlob | 簡易 NLP 庫 | 快速原型開發 | [Official](https://textblob.readthedocs.io/) |
| 17 | GenSim | 主題建模與向量空間模型 | 處理大規模文本集 | [Official](https://radimrehurek.com/gensim/) |
| 18 | Transformers | 統一模型接口庫 | 快速切換不同 LLM | [HuggingFace](https://huggingface.co/docs/transformers) |
| 19 | Tokenizers | 高性能分詞器 | 處理多語言編碼 | [HuggingFace](https://github.com/huggingface/tokenizers) |
| 20 | PyTorch | 深度學習框架 | 模型訓練與微調 | [Official](https://pytorch.org/) |

#### 🏛️ 模組三：市場調查與驗證專家 (商業落地層)
| 序號 | 名稱 | 簡介 | 備註 | 連結 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | The Mom Test | 訪談去偏法 | 避免誘導性問題 | [Official](https://momtestbook.com/) |
| 02 | JTBD Theory | 用戶「雇傭」產品理論 | 挖掘底層驅動力 | [JTBD.me](https://jtbd.me/) |
| 03 | Lean Startup | 精實創業驗證循環 | 快速排除錯誤假設 | [Official](https://theleanstartup.com/) |
| 04 | Likert Scale | 5 級量表設計規範 | 量化痛點強度 | [Wikipedia](https://en.wikipedia.org/wiki/Likert_scale) |
| 05 | P-value Analysis | 統計顯著性檢驗 | 確保結論非隨機誤差 | [Statistics] |
| 06 | Stratified Sampling | 分層隨機抽樣法 | 消除樣本偏差 | [Wikipedia](https://en.wikipedia.org/wiki/Stratified_sampling) |
| 07 | Pearson Correlation | 相關係數分析 | 驗證痛點與支付意願 | [Statistics] |
| 08 | Fake Door Testing | 虛擬門頁面測試 | 驗證真實轉化率 | [Research] |
| 09 | Value Proposition Canvas | 價值主張畫布 | 對齊功能與痛點 | [Strategyzer](https://strategyzer.com/) |
| 10 | User Personas | 數據驅動的用戶畫像 | 定義目標用戶群 | [HubSpot](https://blog.hubspot.com/) |
| 11 | CRO Framework | 轉換率優化路徑 | 驗證價值主張 | [Optimizely](https://www.optimizely.com/) |
| 12 | JTBD Mapping | 任務路徑映射圖 | 識別旅程摩擦點 | [Internal SOP] |
| 13 | User Friction Analysis | 用戶摩擦力分析法 | 量化不方便程度 | [NNg](https://www.nngroup.com/) |
| 14 | Targeted Survey Design | 定向問卷設計技巧 | 提高高質樣本率 | [Pew Research](https://www.pewresearch.org/) |
| 15 | Data Triangulation | 數據三角校驗法 | 交叉驗證量-質-參 | [Research] |
| 16 | Net Promoter Score | 淨推薦值模型 | 量化滿意度忠誠度 | [Bain](https://www.bain.com/) |
| 17 | Sean Ellis PMF Survey | PMF 契合度問卷 | 驗證失去產品失望度 | [Sean Ellis](https://seanelliss.com/) |
| 18 | Competitive Benchmarking | 競品功能對標分析 | 尋找市場空白區 | [Gartner](https://www.gartner.com/) |
| 19 | Priority Matrix | 影響力-可行性矩陣 | 決定 Roadmap 優先級 | [Internal SOP] |
| 20 | Executive Synthesis | 高階管理摘要合成 | 轉化為 actionable 建議 | [McKinsey](https://www.mckinsey.com/) |
| 21 | Kano Model | 卡諾模型 (基本/期望/興奮) | 區分功能層級 | [Wikipedia](https://en.wikipedia.org/wiki/Kano_model) |
| 22 | Design Thinking | 設計思考-共情階段 | 挖掘用戶心理模型 | [IDEO](https://www.ideo.com/) |
| 23 | Problem-Solution Fit | 問題-方案契合度驗證 | 驗證方案是否對症 | [Lean Startup] |
| 24 | Interview Scripting | 訪談腳本撰寫指南 | 確保過程無誘導 | [Internal SOP] |
| 25 | Sentiment-to-Demand Map | 情緒-需求映射表 | 將憤怒轉化為功能需求 | [Internal SOP] |
| 26 | Rapid Prototyping | 快速原型開發驗證 | 低保真模型測試 | [Research] |
| 27 | Cohort Analysis | 隊列分析法 | 觀察需求人群演變 | [Research] |
| 28 | A/B Testing | 假設驅動的 A/B 測試 | 驗證價值主張吸引力 | [Optimizely](https://www.optimizely.com/) |
| 29 | Value-to-Price Ratio | 價值-價格比分析 | 驗證支付意願閾值 | [Internal SOP] |
| 30 | Customer Journey Map | 客戶旅程圖分析 | 識別轉化流失點 | [NNg](https://www.nngroup.com/) |
| 31 | PMF Cycle | PMF 迭代循環路徑 | 從驗證到擴張的週期 | [Marc Andreessen] |
| 32 | Quantitative Bias Correction | 量化數據偏差修正 | 處理幸存者偏差 | [Statistics] |
| 33 | Interview-to-Survey Pipeline | 訪談 → 問卷流水線 | 將定性發現量化 | [Internal SOP] |
| 34 | Pain-Point Scoring | 痛點評分體系 | 量化商業價值 | [Internal SOP] |
| 35 | Landing Page Analysis | 落地頁轉化分析 | 驗證市場吸引力 | [CRO] |
| 36 | KOC/KOL Influence Map | 關鍵意見領袖映射 | 識別需求傳播路徑 | [Internal SOP] |
| 37 | Share of Voice (SoV) | 品牌聲量佔有率分析 | 量化市場競爭地位 | [HubSpot](https://blog.hubspot.com/) |
| 38 | Churn Signal Detection | 用戶流失信號檢測 | 識別對現有產品不滿 | [Research] |
| 39 | Behavioral Nudge | 行為心理學-助推理論 | 優化問卷填寫真實度 | [Thaler/Sunstein] |
| 40 | Business Model Canvas | 商業模式畫布 | 轉化為商業模型 | [Strategyzer](https://strategyzer.com/) |
