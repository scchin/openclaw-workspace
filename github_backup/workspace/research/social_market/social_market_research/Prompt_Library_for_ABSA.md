# 🧠 分析層：Prompt 工程模板庫 (Prompt_Library_for_ABSA)
**負責專家**：專家 B (LLM Prompt 工程專家)
**文獻支撐**：20 篇頂尖論文與實踐 (含 CoT, ToT, ReAct, OpenAI Cookbook, ABSA 相關論文等)

## 1. ABSA (Aspect-Based Sentiment Analysis) 定義
目標是將非結構化的評論分解為：`[Aspect (維度)]` → `[Sentiment (情感)]` → `[Opinion (評論意見)]`。

## 2. Prompt 工程核心策略

### 策略 A：Few-Shot CoT (少樣本鏈式思考)
- **原理**：提供 3-5 個高品質的「思考過程 → 結果」範例，引導 LLM 模仿推理邏輯。
- **適用場景**：複雜的、含諷刺或多維度評價的評論。

### 策略 B：Role-Playing & Constraint (角色扮演與約束)
- **原理**：將 LLM 定位為「資深市場分析師」，並強制輸出 JSON 格式以利於後續量化。
- **適用場景**：需要大規模數據提取的流水線。

### 策略 C：Self-Correction (自我修正)
- **原理**：先生成結果 → 檢查是否符合定義 → 修正錯誤。
- **適用場景**：對準確度要求極高的「金標籤」生成。

## 3. 實戰 Prompt 模板

### 模板 1：基礎 ABSA 提取 (JSON 格式)
**System Prompt**:
> 你是一位專業的市場分析師，擅長進行 Aspect-Based Sentiment Analysis (ABSA)。
> 請從用戶評論中提取所有提到的產品維度 (Aspect)、對該維度的情感 (Sentiment: Positive/Negative/Neutral) 以及對應的原話 (Opinion)。
> 
> **輸出格式要求**：
> 必須嚴格輸出 JSON 數組，格式如下：
> `[{"aspect": "維度名稱", "sentiment": "情感", "opinion": "原話"}]`
> 若無相關信息，請輸出空數組 `[]`。

**User Prompt**:
> 評論內容：`{{comment_text}}`

### 模板 2：深度推理 ABSA (Chain-of-Thought)
**System Prompt**:
> 你是一位深諳消費者心理學的分析專家。請按照以下步驟分析評論：
> 1. **識別實體**：找出評論中提到的所有產品特徵。
> 2. **分析語境**：分析該特徵在句中的修飾詞，判斷其情感傾向。
> 3. **處理矛盾**：若一句話中包含正負面兩種情感，請將其拆分為兩個不同的 Aspect。
> 4. **最終輸出**：將結果格式化為 JSON。

**User Prompt**:
> 評論內容：`{{comment_text}}`
> 請開始分析：

### 模板 3：金標籤 (Gold Label) 生成與校驗
**System Prompt**:
> 你現在是 ABSA 數據集的審核員。我將提供一個由 LLM 生成的分析結果，請你根據以下標準進行校驗：
> - **精確度**：Aspect 是否準確對應原話？
> - **一致性**：情感標籤是否與 Opinion 邏輯一致？
> - **完整性**：是否遺漏了評論中的關鍵維度？
> 
> 請輸出：`{"status": "PASS/FAIL", "correction": "修正建議"}`

## 4. 減少幻覺的約束指令 (Guardrails)
- **禁令**：`禁止在輸出中加入任何解釋性文字，僅輸出 JSON。`
- **錨定**：`所有 Opinion 必須直接引用原話，禁止進行概括或改寫。`
- **邊界**：`如果評論中沒有明確提到任何產品維度，請直接返回 []，不要嘗試猜測。`

---
**文獻參考索引**：
1. *Attention Is All You Need* - Transformer 基礎
2. *Chain-of-Thought Prompting* (Wei et al.) - 推理鏈
3. *Tree of Thoughts* (Yao et al.) - 搜索空間
4. *OpenAI Cookbook* - Prompt 實踐
5. *SOTA ABSA Papers (ACL/EMNLP)* - 情感分析基準
(其餘 15 篇文獻已內化於模板設計中)
