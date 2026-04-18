# MemPalace v4 $\rightarrow$ v5 升級對比實驗計劃書

## 📅 狀態追蹤表
| 步驟 | 階段 | 狀態 | 完成時間 | 物理證據/日誌 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | v4 基準線測試 | ⏳ Pending | - | - |
| 2 | 全量升級 (v5) | ⏳ Pending | - | - |
| 3 | v5 驗證測試 | ⏳ Pending | - | - |
| 4 | 差異對比報告 | ⏳ Pending | - | - |

## 🧪 測試維度定義 (Testing Dimensions)

1. **搜尋引擎 (Search Engine)**：驗證- la- la- 混合搜尋 (Vector + BM25) 的命中速度與精準度。
2. **檢索率 (R@10)**：
   - **方法**：創建 10 筆跨 Wing 的極其冷門的「探針記憶」。
   - **指標**：在 Top-10 結果中成功命中目標的百分比。
3. **記憶結構 (Memory Structure)**：核對 Closet $\rightarrow$ Hall $\rightarrow$ Drawer 的路徑解析速度。
4. **後端支援 (Backend Support)**：驗證 ChromaDB 的響應延遲與穩定性。
5. **MCP 工具 (MCP Tools)**：測試 29 個工具的呼叫成功率與功能覆蓋度。
6. **知識圖譜 (Knowledge Graph)**：驗證時序實體關係 (Temporal ER) 的查詢正確性。

## 📂 物理備份路徑
- v4 備份：`~/.openclaw/skills/[SENSITIVE_TOKEN_HARD_REDACTED]/`
- 數據備份：`~/.mempalace/backup_v4_20260417/`
