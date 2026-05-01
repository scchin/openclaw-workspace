# 物理渲染抓取 SOP (Physical Rendering Extraction SOP)
## 適用場景：處理虛擬列表 (Virtual List / Lazy Loading)
當目標頁面 (如 Google Maps 評論區) 採取「僅渲染可見區域」且動態銷毀不可見 DOM 元素的機制時，標準的 `innerText` 或單次 `scrollTo` 將失效。必須採取本 SOP 規定的「緩慢渲染捕捉法」。

## 🚫 絕對禁令
1. **禁止一次性抓取**：嚴禁在不執行分段滾動的情況下嘗試提取評論。
2. **禁止快速連續操作**：嚴禁在未通過 `browser state` 確認頁面渲染完成前執行下一次 `eval`。
3. **禁止依賴動態 Class**：禁止使用隨機生成的 CSS Class 作為選擇器，必須使用「文本特徵錨點」。

## ✅ 標準物理路徑 (Standard Operating Procedure)

### 第一階段：物理定位
1. **直接導航**：優先使用 `/review` 結尾的直接連結進入評論分頁，繞過標籤切換。
2. **強制排序**：物理點擊 `Sort` $\rightarrow$ `Newest`。
3. **狀態驗證**：執行 `browser state` 確認 `Newest` 選項已被選中 (aria-checked=true)。

### 第二階段：緩慢渲染循環 (The Render Loop)
重複以下步驟直到滿足目標數量 (例如 6 則評論)：
1. **分段滾動**：`window.scrollTo(0, current_y)`，每次增量 $\le 300\text{px}$。
2. **物理延時**：強制 `sleep` $1.5\text{s} \sim 2.0\text{s}$，確保瀏覽器完成異步渲染。
3. **特徵掃描**：執行 `browser eval` 搜索包含時間特徵的 `div` 元素。
   - **時間錨點正則**：`/(\d+ (day|week|month|year)s? ago)|(\d+ (日|週|月|年)前)/`
4. **緩衝捕捉**：將捕捉到的文本塊存入臨時緩衝池，並對評論正文進行去重處理。

### 第三階段：數據清洗
1. **反向追溯**：利用時間錨點，向上/下提取最近的文本塊作為評論正文。
2. **時間標準化**：將 `X days ago` 統一轉換為相對時間格式 (例如：「X 日前」)。

---
**更新日期**：2026-04-29
**狀態**：正式生效 $\rightarrow$ 適用於所有 Google Maps 深度抓取任務。
