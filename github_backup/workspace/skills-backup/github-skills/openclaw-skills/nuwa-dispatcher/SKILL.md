# nuwa-dispatcher (Nuwa 專家調度員)

## 1. 定位與目標
`nuwa-dispatcher` 是 `huashu-nuwa` 技能的「前端入口」。它不負責具體的內容生成，而是負責**「認知分流」**。
當使用者需要專業深度分析時，`nuwa-dispatcher` 會根據 `EXPERT_REGISTRY.md` 匹配最合適的專家原型，並將其「認知 DNA」傳遞給 `huashu-nuwa` 執行。

## 2. 觸發機制
- **關鍵字觸發**：當輸入包含「專家的看法」、「意見為何」、「專家分析」或 DED 特定模式時。
- **優先級**：高於通用回答，優先進入專家派遣管線。

## 3. 執行流程 (The DED Pipeline)
`nuwa-dispatcher` $\rightarrow$ `huashu-nuwa` 的連動路徑：
1. **意圖偵測**：識別 DED 觸發詞。
2. **專家匹配**：執行 `scripts/dispatch.py` $\rightarrow$ 讀取 `EXPERT_REGISTRY.md` $\rightarrow$ 返回最合適的 `專家名稱` 與 `認知 DNA`。
3. **上下文注入**：將匹配到的專家原型注入 System Prompt 或 MemPalace 指定房間。
4. **引擎執行**：調用 `huashu-nuwa` 進行高純度輸出生成。

## 4. 使用方式
**內部調用指令**：
`python3 ~/.openclaw/skills/nuwa-dispatcher/scripts/dispatch.py "<使用者問題>"`

**輸出結果**：
返回建議的專家名稱及其對應的邏輯模式，供 `huashu-nuwa` 直接採納。

## 5. 制度依賴
- 依賴文件：`/Users/KS/.openclaw/workspace/DED_SPEC.md`
- 數據源：`/Users/KS/.openclaw/workspace/EXPERT_REGISTRY.md`
- 執行引擎：`huashu-nuwa`
