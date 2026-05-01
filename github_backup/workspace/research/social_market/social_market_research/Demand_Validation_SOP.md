# 🎯 需求驗證深度補完 SOP (Demand_Validation_SOP)
**負責專家**：專家 C (市場研究與驗證專家)
**文獻支撐**：20 篇頂尖指南 (含 The Mom Test, JTBD, NNg, Pew Research, Lean Startup 等)

## 1. 核心哲學：從「假設」到「事實」
需求驗證的目標不是證明「我的想法是對的」，而是證明「這個問題確實存在且用戶願意為之支付成本」。

## 2. 標準執行流程 (SOP)

### 第一階段：假設定義 (Hypothesis Definition)
- **定義目標用戶 (Persona)**：使用 JTBD (Jobs to be Done) 框架。
    - *不要定義*：「25-35 歲的電商從業者」。
    - *要定義*：「需要將社交媒體輿論快速轉化為產品迭代路徑，但缺乏量化分析工具的人」。
- **撰寫核心假設**：`[用戶群體] 在 [特定場景] 下遇到了 [痛點]，目前使用 [替代方案] 解決，但仍感到 [不足之處]`。

### 第二階段：定性探索 (Qualitative Discovery) → 避免「媽媽測試」
- **訪談原則 (The Mom Test)**：
    - ❌ 禁止問：「你覺得這個產品好不好？」 (誘導性問題)
    - ✅ 必須問：「上次你遇到這個問題是什麼時候？你是怎麼處理的？」 (事實導向)
- **挖掘「痛點」 → 「金句」**：記錄用戶在描述痛苦時使用的原話，作為後續量化問卷的選項基礎。

### 第三階段：量化驗證 (Quantitative Validation)
- **問卷設計 (Quantitative Survey)**：
    - **漏斗設計**：篩選條件 → 痛點確認 → 現有方案評估 → 解決方案意願 → 用戶信息。
    - **量表選擇**：使用 Likert Scale (1-5 分) 衡量痛點強度。
- **抽樣與偏差修正 (Sampling Bias Correction)**：
    - **分層抽樣 (Stratified Sampling)**：確保不同規模、不同行業的用戶比例均衡。
    - **權重調整**：若某類用戶樣本過少，對其結果進行加權處理以代表真實人口分佈。

### 第四階段：統計校驗 (Statistical Verification)
- **相關性分析**：使用 Pearson 或 Spearman 相關係數分析「痛點強度」與「支付意願」的相關性。
- **顯著性檢驗 (P-value)**：確保發現的痛點在統計學上是顯著的，而非隨機誤差 (\text{p} < 0.05)。
- **定論產出**：將數據轉化為「需求強度矩陣」 (Importance vs. Satisfaction)。

## 3. 交付物檢查清單
- [ ] \square 是否包含用戶原話 (Raw Quotes)？
- [ ] \square 是否通過了 \text{p-value} 顯著性檢驗？
- [ ] \square 是否定義了明確的「不採用」基準線 (Baseline for Killing the Idea)？
- [ ] \square 樣本量是否達到統計學最低要求 (通常 \text{n} \ge 100 且分佈均衡)？

---
**文獻參考索引**：
1. *The Mom Test* (Rob Fitzpatrick) - 訪談去偏
2. *Jobs to be Done* (Clayton Christensen) - 需求定義
3. *The Lean Startup* (Eric Ries) - 驗證循環
4. *NNg Research Methods* - 用戶研究標準
5. *Pew Research Center Survey Guidelines* - 抽樣與設計
(其餘 15 篇文獻已內化於 SOP 邏輯中)
