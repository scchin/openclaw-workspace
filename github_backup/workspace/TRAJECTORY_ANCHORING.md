# Physical Trajectory Anchoring System (PTAS) Specification

## 核心哲學
- **信任軌跡，而非模型**：模型可能會撒謊，但工具的標準輸出 (stdout) 和物理文件不會。
- **意圖鎖定**：所有執行必須先定義「預期證據」，禁止在執行後才定義「成功標準」。
- **分級驗證**：根據風險等級動態調整驗證深度，平衡延遲與真實性。

## 物理層級定義與觸發矩陣

| 層級 | 名稱 | 觸發條件 (Trigger) | 驗證機制 | 物理路徑 | 延遲 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **L1** | **快速通道** | 低複雜度 \text{AND} 高信心 (\text{Entropy} < 0.2) | \text{Confidence Check} | \text{Input} → \text{Output} | 極低 |
| **L2** | **標準軌跡** | 常規任務 \text{OR} 中信心 (\text{Entropy } 0.2\text{-}0.5) | \text{原子拆解} → \text{RAG 物理核對} | \text{Draft} → \text{Verifier.py} → \text{Output} | 中 |
| **L3** | **深度審計** | 高風險領域 \text{OR} 低信心 (\text{Entropy} > 0.5) | \text{跨模型共識} → \text{DED 簽核} | \text{Draft} → \text{Auditor.py} → \text{Output} | 高 |

### 風險領域定義 (High-Risk Domains)
- 涉及代碼執行 (Code Execution)
- 涉及金錢/權限修改 (Permission/Money)
- 涉及醫療/法律/專業事實 (Professional Facts)
- 涉及系統配置更改 (System Config)


## Pydantic 意圖鎖定協議
所有任務啟動必須遵循：
1. **定義計畫**：生成 `ExecutionPlan` (JSON)。
2. **物理鎖定**：寫入 `current_plan.json`。
3. **軌跡執行**：每一步執行後，必須對比 `tool_output` 與 `expected_evidence`。
4. **結案驗證**：所有步驟完成 → 檢查所有證據鏈 → 生成結案報告。
