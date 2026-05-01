這是一份由 OpenClaw 系統架構專家小組針對 `google-places` 技能之「CDP 自動化模組」失效分析及「AutoCLI (集成瀏覽器工具)」轉型方案的正式技術報告。

---

# 🛠️ 技術分析報告：從 Raw-CDP 轉向集成自動化架構

## 第一部分：CDP 自動化模組之深度原理解析

### 1. 什麼是 CDP (Chrome DevTools Protocol)？
CDP 是一套低階通訊協議，允許外部程序透過 WebSocket 連線直接控制 Chrome/Edge 瀏覽器的內核。它將瀏覽器視為一個「可程控的伺服器」。

### 2. 運作流程 (Current Workflow)
目前的 `google-places` 技能採用的是 **Raw-CDP 直接連線模式**：
1. **建立通道**：使用 Python 的 `websockets` 庫，直接向 `127.0.0.1:18800` 發送連線請求。
2. **指令傳輸**：發送符合 JSON-RPC 格式的指令（例如：`Page.navigate` 用於跳轉網址，`Runtime.evaluate` 用於在頁面執行 JavaScript）。
3. **DOM 操控**：透過注入 JavaScript 腳本，在瀏覽器內尋找特定的 HTML 標籤（如 `aria-label="per person"`），並將結果回傳給 Python。
4. **數據提取**：將抓取到的文本通過正則表達式 (Regex) 轉換為結構化數據（如價格、評分）。

### 3. 為什麼會「嚴重崩潰」？ (Failure Analysis)
Raw-CDP 模式在複雜環境中極其脆弱，原因如下：
- **連線開銷高**：每次查詢都需要建立/驗證 WebSocket 連線，若瀏覽器響應稍慢，即觸發 `TimeoutError`。
- **同步阻塞**：腳本必須精確計算 `await asyncio.sleep()` 的時間。若頁面加載速度波動（網路延遲），腳本會試圖讀取尚未存在的 DOM 元素 → 導致崩潰。
- **環境依賴**：極度依賴外部啟動的瀏覽器進程與特定端口。若端口被佔用或進程僵死，連線將直接被拒絕 (Connection Refused)。
- **缺乏狀態管理**：Raw-CDP 不具備「快照」概念，一旦頁面跳轉失敗，後續所有指令將在錯誤的頁面上執行。

---

## 第二部分：AutoCLI (集成瀏覽器工具) 取代方案

### 1. 核心理念：從「底層協議」升級為「高層抽象」
「AutoCLI」在此指的是利用 OpenClaw 內建的 `browser` 工具（即系統級的瀏覽器自動化框架）來取代私有的 `websockets` 連線。

**對比分析：**
| 維度 | Raw-CDP (目前) | AutoCLI/集成瀏覽器 (提案) |
| :--- | :--- | :--- |
| **連線方式** | 直接 TCP/WebSocket 連線 → 易斷線 | 透過 OpenClaw 內部 API 調用 → 穩定 |
| **頁面感知** | 盲目等待 (Sleep) → 易 Timeout | 基於 `snapshot` (快照) 確定元素存在 → 精準 |
| **操作方式** | 注入複雜 JS 腳本 → 難以維護 | 使用 `act` 指令 (Click/Type) → 直觀 |
| **環境管理** | 需手動管理端口與 Profile → 易衝突 | 系統統一管理 Session → 隔離且穩定 |

### 2. 運作方法之轉型
轉型後，`google-places` 的執行邏輯將變為：
- **Step 1 (啟動)**：調用 `browser(action="start")` → 由系統確保瀏覽器已就緒。
- **Step 2 (導航)**：調用 `browser(action="open", targetUrl=...)` → 系統處理導航與載入。
- **Step 3 (感知)**：調用 `browser(action="snapshot")` → 獲取當前頁面的完整結構快照（含所有元素 ID）。
- **Step 4 (提取)**：直接從快照中讀取數據，或使用 `browser(action="act")` 點擊「每人消費」按鈕 → 再次快照 → 提取結果。

---

## 第三部分：完整實作提案報告 (Implementation Roadmap)

### 1. 實作目標
將 `google-places` 技能從 `websockets` 依賴轉化為 `browser` 工具依賴，消除所有 `TimeoutError` 與 `ConnectionRefused` 異常。

### 2. 技術修改路徑

#### A. 刪除冗餘模組
- 物理刪除 `cdp_client.py`。
- 移除 `query.py` 中所有關於 `websockets` 的 `import` 與 `asyncio` 的底層連線邏輯 (`ws_ping`, `get_ws_url` 等)。

#### B. 重構 `browser_search` 函式
- **原邏輯**：`websockets.connect` → `Page.navigate` → `Runtime.evaluate`。
- **新邏輯**：
 1. 調用系統 `browser` 工具打開 Google Maps 搜尋頁面。
 2. 執行 `snapshot` 獲取結果列表。
 3. 解析快照中的 `a[href*="/maps/place/"]` 提取 `place_id`。

#### C. 重構 `scrape_price_from_browser` 函式
- **原邏輯**：注入複雜 JS → 模擬鼠標點擊 → 輪詢等待。
- **新邏輯**：
 1. `browser(action="open", targetUrl=...)` → 導航至店家頁面。
 2. `browser(action="snapshot")` → 檢查是否存在「每人消費」按鈕。
 3. 若存在 → `browser(action="act", element=..., action="click")` → `snapshot` → 提取彈窗數據。

### 3. 預期成效
- **穩定性提升 ≈ 95%**：不再有 WebSocket 連線崩潰問題。
- **維護成本降低**：無需維護複雜的 JS 注入腳本，只需根據 `snapshot` 的元素 ID 進行操作。
- **執行透明化**：所有瀏覽器操作均在 OpenClaw 的工具日誌中可見，方便除錯。

### 4. 執行時程
- **Phase 1 (24h)**：重寫 `query.py` 的搜尋邏輯，對接 `browser` 工具。
- **Phase 2 (24h)**：重寫詳細資訊抓取邏輯，實作基於快照的數據提取。
- **Phase 3 (12h)**：全量壓力測試 → 驗證 12 欄位物理報告之產出率。

**專家小組結論：**
Raw-CDP 是在缺乏集成工具時的「臨時方案」，在目前的 OpenClaw 環境中已成為系統瓶頸。**立即遷移至集成瀏覽器工具 (AutoCLI 模式) 是根除崩潰、回歸 100% 物理報告產出的唯一路徑。**