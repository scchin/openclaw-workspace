# MEMORY.md 歸檔（2026-03-22 以前）
# 此檔案由 MEMORY.md 優化流程自動產生
# 儲存已被取代但可能仍需參考的歷史記錄
# 不在主要載入路徑，節省上下文空間

---

## 使用記錄（舊）

### 2026-03-15：經緯度查詢規則建立
- 問題：TGOS地圖不支援直接經緯度坐標搜尋，需透過地址查詢
- 解決：TGOS → 圖面定位 → 選擇縣市/鄉鎮/村里
- 限制：TGOS無法直接輸入坐標

### 2026-03-15：陳平國小午餐查詢結果
- 學校：臺中市北屯區陳平國民小學（24.185067, 120.667822）
- 附近5間午餐推薦（需實際確認）

### 2026-03-19：MCP 伺服器安裝
- 設定檔：`~/.openclaw/workspace/config/mcporter.json`
- 5個MCP伺服器：playwright, filesystem, github, memory, puppeteer

### 2026-03-21：google-places 重大修正（v7）
- CDP WS健康檢查修正
- 中文「平均每人 $X-$Y」支援
- Phase 3中文按鈕定位修正
- 已移除Playwright相依

### 2026-03-21：MEMORY.md審核
- 發現並修正使用記錄格式問題

### 2026-03-22：skills-backup-github 建立
- commit `7ce660b` — 全量技能同步至GitHub
- 每日03:00自動備份（launchd排程）

### 彰化早餐、陳平國小資料
（已移至 memory/ 目錄供日後參考）
