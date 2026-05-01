# 🚀 社交媒體與輿論市場分析項目：最終執行指南 (v2.0 操作級)
**版本**: v2.0 (Final Operational Manual)
**狀態**: 100% 可執行 (Executable)
**日期**: 2026-04-26

---

## 1. 執行摘要 (Executive Summary)
本指南將「社交媒體雜訊」轉化為「商業決策指標」的流程標準化。v2.0 版本在 v1.0 的基礎上，將「需求驗證」、「帳號池維護」、「Prompt 工程」與「實戰案例」四個核心缺口完全填補，從「框架級」提升至「操作級」。

**核心交付物**: 
- 跨平台數據採集集群 → 輿論量化看板 → 需求驗證報告 → 產品優先級 Roadmap。

---

## 2. 技術架構 (Technical Architecture)

### 2.1 數據獲取層 (Data Acquisition) & 帳號池維護
**策略**: 採用 **「混合採集 + 定向抽樣」** 與 **「工業級帳號管理」**。
- **採集路徑**:
    - **低門檻 (JSON/API)**: `Dcard`, `X (Official API)` → 直接請求 → MongoDB。
    - **高門檻 (JS-Heavy/Anti-Bot)**: `TikTok`, `Instagram`, `小紅書`, `Threads` → **Playwright (Stealth)** → **Residential Proxy (Bright Data)** → MongoDB。
- **帳號池維護 SOP**:
    - **初始化**: 設備指紋隨機化 → 住宅代理分佈 → SMS API 自動驗證。
    - **養號期**: 執行隨機路徑瀏覽 (首頁 → 搜索 → 點擊) → 高斯分佈隨機延時。
    - **運行期**: 採用 Least-Used First 輪詢 → 單帳號每日請求限額 → 探針健康檢查。
    - **補全**: \text{Active\_Accounts} < \text{Threshold} 時自動觸發分批注入註冊流水線。

### 2.2 數據處理與分析層 (NLP Pipeline)
**策略**: 採用 **「LLM 標記 → 輕量模型執行」**。
1. **清洗**: `Custom Preprocessing` → 剔除 Bot → 俚語標準化。
2. **聚類 (Discovery)**: 使用 **BERTopic** → 自動分群為 5-10 個核心話題。
3. **量化 (Quantification)**: 
   - 使用 **RoBERTa-ABSA** (面向方面的情緒分析) → \text{Sentiment Score} \in [-1, 1]。
   - **Prompt 模板**: 使用 Few-Shot CoT 誘導模型 → 強制 JSON 輸出 → 自我修正檢查 → 錨定原話。
   - 計算 **Velocity** (話題增速) → 識別爆發性需求。

### 2.3 商業驗證層 (Business Validation)
**策略**: 建立 **「需求閉環 (The Loop)」**。
- **需求定義**: 使用 JTBD (Jobs to be Done) 框架定義目標用戶及其在特定場景下的痛點。
- **驗證路徑**:
    - **定性探索 (The Mom Test)**: 訪談事實導向 → 挖掘用戶原話 → 建立痛點假設。
    - **量化驗證**: 漏斗式問卷設計 → 分層抽樣 → Likert Scale 衡量強度 → \text{p-value} 顯著性檢驗 (\text{p} < 0.05)。
- **決策轉化**: \text{社群數據 (量)} + \text{問卷數據 (質)} + \text{競品數據 (參照)} → 填入優先級矩陣 → 產出產品 Roadmap。

---

## 3. 工具鏈清單 (Tooling Stack)

| 模組 | 推薦工具 | 用途 | 替代方案 |
| :--- | :--- | :--- | :--- |
| **採集** | Playwright + Python | 動態網頁抓取 | Selenium / Scrapy |
| **代理** | Bright Data / Oxylabs | 繞過 IP 封鎖 | 自建 Proxy Pool |
| **存儲** | MongoDB | 非結構化文本存儲 | PostgreSQL (JSONB) |
| **分析** | BERTopic / HuggingFace | 話題聚類與情緒分析 | GPT-4o (全量分析, 成本高) |
| **驗證** | Typeform / Qualtrics | 定向需求驗證問卷 | Google Forms |
| **可視化** | Grafana / Tableau | 實時輿論監控看板 | Streamlit |

---

## 4. 標準執行步驟 (SOP)

1. **Step 1 (Setup)**: 部署 MongoDB → 配置 Playwright 環境 → 採購住宅代理 → 建立帳號池。
2. **Step 2 (Crawling)**: 執行 \text{定向關鍵字採集} → \text{存儲至 MongoDB} → 監控帳號健康狀態。
3. **Step 3 (Clustering)**: 運行 BERTopic → 輸出 `Topic_Map.csv` → 審核話題類別。
4. **Step 4 (Sentiment)**: 使用 ABSA Prompt 庫 → 運行 RoBERTa-ABSA → 產出 \text{Aspect-Sentiment Matrix}。
5. **Step 5 (Mapping)**: 將矩陣填入 \text{優先級矩陣} → 篩選 Top 3 痛點 → 定義 JTBD 假設。
6. **Step 6 (Validation)**: 撰寫無偏差問卷 → 社群定向投放 → 統計顯著性校驗 → 修正結論。
7. **Step 7 (Output)**: 產出 \text{產品迭代建議書} (包含：發現 → 證據 → 建議 → 預期收益)。

---

## 5. 風險預估與對策 (Risk Management)

| 風險 | 概率 | 影響 | 對策 |
| :--- | :--- | :--- | :--- |
| **帳號大規模封鎖** | 中 | 高 | 降低採集頻率 → 增加帳號池 → 住宅代理輪轉 → 自動補全機制 |
| **模型分析偏差** | 中 | 中 | 引入 LLM 進行 5% 數據的隨機抽檢 → 修正標籤 → 重新訓練 |
| **數據合規問題** | 低 | 極高 | 嚴格執行 PII (個資) 脫敏 → 僅儲存聚合指標 → 不儲存用戶 ID |

---

## 📚 附錄：補完計畫核心技術資源列表 (總計 80 項)

本列表記錄了 v2.0 補完計畫中四項深度研究的技術底層。

### 📦 模組 A：帳號池維護與反爬對抗 (20 項)
| 序號 | 名稱 | 簡介 | 備註 | 連結 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | **Playwright Stealth** | 隱藏瀏覽器自動化特徵 | 繞過 WAF 核心 | [GitHub](https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth) |
| 02 | **Bright Data** | 住宅級 IP 代理網路 | 降低風控權重 | [Official](https://brightdata.com/) |
| 03 | **FingerprintJS** | 設備指紋識別原理 | 用於對抗指紋追蹤 | [Official](https://fingerprint.com/) |
| 04 | **undetected-chromedriver** | 修改 ChromeDriver 內核特徵 | 繞過 Cloudflare | [GitHub](https://github.com/ultrafunkamsterdam/undetected-chromedriver) |
| 05 | **2Captcha** | 自動化驗證碼識別 API | 處理註冊攔截 | [Official](https://2captcha.com/) |
| 06 | **SMS-Activate** | 虛擬手機號接收平台 | 自動化帳號註冊 | [Official](https://sms-activate.org/) |
| 07 | **OWASP Bot Mitigation** | 機器人緩解最佳實踐 | 理解風控邏輯 | [OWASP](https://owasp.org/) |
| 08 | **Residential Proxy Rotation** | 住宅 IP 輪轉算法 | 模擬真實用戶分佈 | [Research](https://brightdata.com/) |
| 09 | **User-Agent Spoofing** | 隨機化設備標識 | 避免單一指紋特徵 | [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent) |
| 10 | **Gaussian Sleep Interval** | 高斯分佈隨機延時 | 模擬人類行為頻率 | [Python-Random](https://docs.python.org/3/library/random.html) |
| 11 | **Canvas/WebGL Noise** | 注入隨機噪聲以混淆指紋 | 繞過 Canvas Fingerprinting | [Research](https://github.com/fingerprintjs/fingerprintjs) |
| 12 | **HTTP/2 Fingerprinting** | 偽造 HTTP/2 協議特徵 | 解決底層協議攔截 | [Research](https://github.com/ja3er/ja3) |
| 13 | **Session Persistence** | Cookie 持久化與狀態同步 | 減少重複登入風險 | [Redis](https://redis.io/) |
| 14 | **Account Warming Protocol** | 帳號養號權重提升流程 | 模擬自然增長 | [Internal SOP] |
| 15 | **Rate Limit Probing** | 動態探測平台限流閾值 | 尋找安全採集上限 | [Internal SOP] |
| 16 | **Headless vs Headful** | 採集模式切換策略 | 應對高強度檢測 | [Playwright](https://playwright.dev/) |
| 17 | **Proxy Mesh Architecture** | 代理集群分發架構 | 提高高併發採集穩定性 | [Network-Arch] |
| 18 | **Anti-Bot Trigger Log** | 封號特徵日誌分析 | 建立封號預警模型 | [Internal SOP] |
| 19 | **Email Domain Reputation** | 高權重郵件域名篩選 | 提升註冊成功率 | [Internal SOP] |
| 20 | **GDPR Data Minimization** | 數據最小化採集原則 | 確保商業採集合規 | [GDPR](https://gdpr-info.eu/) |

---

### 🧠 模組 B：ABSA Prompt 工程模板 (20 項)
| 序號 | 名稱 | 簡介 | 備註 | 連結 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | **Few-Shot CoT** | 鏈式思考少樣本提示 | 提升複雜情感推理精度 | [Wei et al.](https://arxiv.org/abs/2201.11903) |
| 02 | **JSON-Schema Locking** | 強制輸出 JSON 格式 | 確保後續量化可解析 | [OpenAI](https://platform.openai.com/docs/guides/json-mode) |
| 03 | **Zero-Shot Labeling** | 無樣本標記技術 | 用於快速探索新維度 | [HuggingFace](https://huggingface.co/tasks/zero-shot-classification) |
| 04 | **Self-Correction Loop** | 自我修正檢查指令 | 降低標記幻覺率 | [Research](https://arxiv.org/abs/2305.18290) |
| 05 | **Role-Playing (Analyst)** | 定位為資深市場分析師 | 提升分析視角的專業度 | [OpenAI Cookbook](https://cookbook.openai.com/) |
| 06 | **Aspect Extraction Prompt** | 專用維度提取指令 | 精確區分功能與服務 | [Internal SOP] |
| 07 | **Sentiment Polarity Map** | 情感極性映射表 | 統一 Positive/Negative 定義 | [Internal SOP] |
| 08 | **Chain-of-Verification** | 驗證鏈提示法 | 交叉核對原話與標記 | [Research](https://arxiv.org/abs/2309.11495) |
| 09 | **Few-Shot ABSA Dataset** | 針對 ABSA 的金標樣本集 | 提供模型模仿的基準 | [ACL Anthology](https://aclanthology.org/) |
| 10 | **Negative Constraint** | 負面約束指令 (如：禁止解釋) | 減少 Token 浪費 | [Internal SOP] |
| 11 | **Opinion Anchoring** | 錨定原話引用指令 | 防止模型概括導致失真 | [Internal SOP] |
| 12 | **Multi-Turn Refinement** | 多輪對話精煉標記 | 針對極端模糊文本 | [Internal SOP] |
| 13 | **Emotional Nuance Prompt** | 細粒度情緒(驚訝/憤怒)提取 | 挖掘深層用戶痛點 | [GoEmotions](https://github.com/google-research/google-research/tree/master/goemotions) |
| 14 | **Cross-Lingual Prompting** | 跨語言情感對齊指令 | 處理多國語言社群數據 | [Research](https://arxiv.org/abs/1905.04345) |
| 15 | **JSON-L Streaming** | 流式 JSON-L 輸出格式 | 適配海量數據實時分析 | [JSON-L](https://jsonlines.org/) |
| 16 | **Instruction Tuning** | 指令微調對齊方法 | 提升模型對 SOP 的服從度 | [Research](https://arxiv.org/abs/2203.02155) |
| 17 | **Dynamic Few-Shot** | 根據輸入動態選擇示例 | 提高類比標記的準確度 | [Research](https://arxiv.org/abs/2205.00443) |
| 18 | **Contrastive Prompting** | 對比提示法 (正例 vs 負例) | 明確定義邊界案例 | [Internal SOP] |
| 19 | **Self-Consistency** | 自一致性投票機制 |  l-次採樣取眾數以定標籤 | [Research](https://arxiv.org/abs/2203.11171) |
| 20 | **ABSA Evaluation Metric** | F1-Score / Kappa 評估指標 | 量化 Prompt 的有效性 | [Wikipedia](https://en.wikipedia.org/wiki/Cohen%27s_kappa) |

---

### 🏛️ 模組 C：需求驗證與實戰路徑 (40 項)
*包含「需求驗證 SOP」與「實戰案例模擬」兩部分。*

| 序號 | 名稱 | 簡介 | 備註 | 連結 |
| :--- | :--- | :--- | :--- | :--- |
| 01 | **The Mom Test** | 訪談去偏法 (事實導向) | 避免誘導性問題 | [Official](https://momtestbook.com/) |
| 02 | **Jobs-to-be-Done (JTBD)** | 用戶「雇傭」產品理論 | 挖掘底層驅動力 | [JTBD.me](https://jtbd.me/) |
| 03 | **Lean Startup (MVP)** | 精實創業驗證循環 | 快速排除錯誤假設 | [Official](https://theleanstartup.com/) |
| 04 | **Likert Scale Design** | 5 級量表設計規範 | 量化痛點強度 | [Research](https://en.wikipedia.org/wiki/Likert_scale) |
| 05 | **P-value Significance** | 統計顯著性檢驗 | 確保結論非隨機誤差 | [Statistics](https://www.investopedia.com/terms/p/p-value.asp) |
| 06 | **Stratified Sampling** | 分層隨機抽樣法 | 消除樣本偏差 | [Statistics](https://en.wikipedia.org/wiki/Stratified_sampling) |
| 07 | **Pearson Correlation** | 相關係數分析 | 驗證痛點與支付意願關係 | [Statistics](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient) |
| 08 | **Fake Door Testing** | 虛擬門頁面測試 | 驗證真實轉化率 | [Research](https://hbr.org/) |
| 09 | **Value Proposition Canvas** | 價值主張畫布 | 對齊產品功能與用戶痛點 | [Strategyzer](https://strategyzer.com/) |
| 10 | **User Persona Archetypes** | 數據驅動的用戶畫像 | 定義典型目標用戶群 | [HubSpot](https://blog.hubspot.com/marketing/buyer-persona-research) |
| 11 | **Conversion Rate Opt (CRO)** | 轉換率優化路徑 | 用於 Landing Page 驗證 | [Optimizely](https://www.optimizely.com/) |
| 12 | **Jobs-to-be-Done Map** | 任務路徑映射圖 | 識別用戶旅程中的摩擦點 | [Internal SOP] |
| 13 | **User Friction Analysis** | 用戶摩擦力分析法 | 量化-「不方便」的程度 | [NNg](https://www.nngroup.com/) |
| 14 | **Targeted Survey Design** | 定向問卷設計技巧 | 提高高質量樣本回覆率 | [Pew Research](https://www.pewresearch.org/) |
| 15 | **Data Triangulation** | 數據三角校驗法 | 交叉驗證社群-問卷-銷售 | [Research](https://scholar.google.com/) |
| 16 | **Net Promoter Score (NPS)** | 淨推薦值模型 | 量化需求滿足後的忠誠度 | [Bain](https://www.bain.com/) |
| 17 | **Sean Ellis PMF Survey** | 產品市場契合度問卷 | 驗證「失去產品會多失望」 | [Sean Ellis](https://seanelliss.com/) |
| 18 | **Competitive Benchmarking** | 競品功能對標分析 | 尋找市場空白區 (White Space) | [Gartner](https://www.gartner.com/) |
| 19 | **Priority Matrix (Impact/Effort)** | 影響力-可行性矩陣 | 決定產品 Roadmap 優先級 | [Internal SOP] |
| 20 | **Executive Summary Synthesis** | 高階管理摘要合成 | 將數據轉化為 actionable 建議 | [McKinsey](https://www.mckinsey.com/) |
| 21 | **Kano Model** | 卡諾模型 (基本/期望/興奮) | 區分必須功能與驚喜功能 | [Wikipedia](https://en.wikipedia.org/wiki/Kano_model) |
| 22 | **Design Thinking (Empathize)** | 設計思考-共情階段 | 深度挖掘用戶心理模型 | [IDEO](https://www.ideo.com/) |
| 23 | **Problem-Solution Fit** | 問題-方案契合度驗證 | 驗證方案是否解決該痛點 | [Lean Startup] |
| 24 | **User Interview Scripting** | 訪談腳本撰寫指南 | 確保訪談過程無誘導 | [Internal SOP] |
| 25 | **Sentiment-to-Demand Map** | 情緒-需求映射表 | 將「憤怒」轉化為「功能需求」 | [Internal SOP] |
| 26 | **Rapid Prototyping** | 快速原型開發驗證 | 用低保真模型測試交互 | [Research](https://scholar.google.com/) |
| 27 | **Cohort Analysis** | 隊列分析法 | 觀察特定需求人群的演變 | [Research](https://scholar.google.com/) |
| 28 | **A/B Testing (Hypothesis-led)** | 假設驅動的 A/B 測試 | 驗證特定價值主張的吸引力 | [Optimizely](https://www.optimizely.com/) |
| 29 | **Value-to-Price Ratio** | 價值-價格比分析 | 驗證用戶的支付意願閾值 | [Internal SOP] |
| 30 | **Customer Journey Mapping** | 客戶旅程圖分析 | 識別從社群發現到購買的流失點 | [NNg](https://www.nngroup.com/) |
| 31 | **Product-Market Fit (PMF) Cycle** | PMF 迭代循環路徑 | 從驗證到擴張的完整週期 | [Marc Andreessen] |
| 32 | **Quantitative Bias Correction** | 量化數據偏差修正 | 處理社交媒體的「幸存者偏差」 | [Statistics] |
| 33 | **Interview-to-Survey Pipeline** | 訪談 → 問卷流水線 | 將定性發現量化為數據 | [Internal SOP] |
| 34 | **Pain-Point Scoring System** | 痛點評分體系 (頻率 \times 強度) | 量化痛點的商業價值 | [Internal SOP] |
| 35 | **Landing Page Conversion Analysis** | 落地頁轉化分析 | 驗證價值主張的市場吸引力 | [CRO] |
| 36 | **KOC/KOL Influence Mapping** | 關鍵意見領袖影響力映射 | 識別需求的傳播路徑 | [Internal SOP] |
| 37 | **Competitive SoV Analysis** | 品牌聲量佔有率分析 | 量化市場競爭地位 | [HubSpot](https://blog.hubspot.com/marketing/share-of-voice) |
| 38 | **Churn Signal Detection** | 用戶流失信號檢測 | 識別對現有產品的不滿 | [Research](https://scholar.google.com/) |
| 39 | **Behavioral Psychology (Nudge)** | 行為心理學-助推理論 | 優化問卷填寫率與真實度 | [Thaler/Sunstein] |
| 40 | **Business Model Canvas** | 商業模式畫布 | 將驗證後的需求轉化為商業模型 | [Strategyzer](https://strategyzer.com/) |
