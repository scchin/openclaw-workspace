# MemPalace 版本對比測試計畫 (Phase 4 Hybrid vs Hybrid v5)

## 任務目標
對比 MemPalace Phase 4 Hybrid 與 Hybrid v5 在六個關鍵維度的表現差異，並提供基於真實數據的差異報告。

## 測試維度
1. 搜尋引擎 (Search Engine)
2. 檢索率 (R@10)
3. 記憶結構 (Memory Structure)
4. 後端支援 (Backend Support)
5. MCP 工具 (MCP Tools)
6. 知識圖譜 (Knowledge Graph)

## 執行步驟

### 第一階段：基線測試 (Phase 4 Hybrid)
- 紀錄目前安裝版本與配置。
- 針對六個維度執行測試：
    - 搜尋引擎：驗證目前採用的索引與檢索邏輯。
    - 檢索率 (R@10)：使用標準測試集，計算前 10 個結果的命中率。
    - 記憶結構：分析目前的數據儲存模型。
    - 後端支援：確認支援的資料庫與向量庫。
    - MCP 工具：清點目前可用的 MCP 接口與功能。
    - 知識圖譜：測試實體關聯與路徑查詢能力。
- 將結果寫入 `mempalace_benchmark_v4.json`。

### 第二階段：環境升級 (Hybrid v5/Develop)
- 全量備份現有 MemPalace 數據與配置。
- 從官方倉庫 `https://github.com/MemPalace/mempalace` 下載最新版本。
- 執行全套安裝流程並驗證啟動狀態。
- 配置環境以確保與 Phase 4 測試條件一致。

### 第三階段：新版本測試 (Hybrid v5/Develop)
- 重複第一階段的六個維度測試。
- 將結果寫入 `mempalace_benchmark_v5.json`。

### 第四階段：對比分析與報告
- 提取 v4 與 v5 的數據進行量化對比。
- 分析每個維度的提升或衰減。
- 調用 `purify_output.py` 生成最終的《MemPalace Hybrid v4 與 v5 差異分析報告》。

## 狀態追蹤
- 紀錄將同步至 `pending_tasks.json` 與 `memory/2026-04-17.md`。
- 任何中斷後，優先檢查此計畫以接續進度。
