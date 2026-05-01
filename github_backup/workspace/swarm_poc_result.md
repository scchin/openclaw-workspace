# Swarm Synthesis: Memory_Analysis_PoC

## Perspective: ShortTerm_Expert

# OpenClaw 短期記憶 (Context Window) 分析報告

## 1. 記憶機制概述
OpenClaw 的短期記憶主要依賴於 LLM 的 Context Window。其運作邏輯可分為以下三個層次：

### A. 靜態上下文注入 (Bootstrap Context)
- **機制**：在 Session 啟動時，系統自動讀取並注入核心配置文件（如 `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`）。
- **限制**：存在物理上限。當文件過大時，會觸發 `Bootstrap truncation warning`，導致部分內容被捨棄。這表明系統優先保證啟動速度與 Token 空間，而非全量讀取。

### B. 動態對話流 (Conversation Flow)
- **機制**：包含用戶指令、代理人的思考過程、工具調用（Tool Call）及其返回結果。
- **特點**：具有強烈的時間序列特性。越早期的資訊在 Token 壓力下越容易被捨棄或壓縮。

### C. 外部記憶擴展 (External Memory)
- **機制**：通過 `memory/YYYY-MM-DD.md` 與 `MEMORY.md` 將短期記憶「固化」為長期記憶。
- **目的**：緩解 Context Window 的壓力，實現跨 Session 的知識持久化。

## 2. 關鍵觀察與分析

### 記憶污染與管理
- **截斷風險**：如本次 PoC 所示，`AGENTS.md` 被截斷了約 22%。這意味著如果關鍵指令位於文件末尾，代理人可能會在啟動時遺忘該指令。
- **Token 競爭**：工具輸出的量越大，對對話歷史的擠壓越嚴重。這解釋了為何系統需要 `token-optimizer` 等技能來精簡輸出。

### 隔離驗證 (Swarm Isolation)
- **路徑鎖定**：在 Swarm 模式下，子代理被限定在特定的工作路徑（如 `sources/swarm_temp/...`）。這種物理路徑的隔離有效地防止了子代理在分析過程中意外修改主代理的記憶文件或核心配置。
- **協議強制**：通過 `swarm_integrity_checker.py` 強制執行寫入前的驗證，確保了短期記憶在分發到多個子代理時的完整性與安全性。

## 3. 結論
OpenClaw 的短期記憶是一個「漏斗狀」結構：
`全量配置文件` → `截斷後注入` → `對話流累積` → `Token 飽和` → `被動遺忘/主動歸檔`。

目前的優化方向應著重於：
1. **動態切片讀取**：取代啟動時的全量注入。
2. **智能摘要**：在 Context 飽和前對舊對話進行語義壓縮。


---

## Perspective: LongTerm_Expert

# OpenClaw 長期記憶系統 (MemPalace) 分析報告

## 1. 系統定位
MemPalace (Phase 4 Hybrid Edition) 已從早期的簡單向量儲存進化為一個**結構化知識圖譜管理系統**。它不再僅僅依賴於語意相似度，而是將記憶組織成一個具有層級結構的「宮殿」，旨在解決大規模記憶檢索中的精準度與延遲問題。

## 2. 核心技術架構
### 2.1 混合搜尋機制 (Hybrid Search)
- **組成**：向量相似度 (60%) + BM25 關鍵字匹配 (40%)。
- **目的**：克服純向量搜尋在處理冷門術語、特定版本號或精確名稱時容易產生的「語意偏移」問題，確保精確命中。

### 2.2 層級索引路徑
系統採取 `Closet (索引層) → Hall (路由層) → Drawer (儲存層)` 的檢索路徑：
- **Closet (衣櫥)**：快速 AAAK 指針匹配，迅速定位目標區域。
- **Hall (走廊)**：根據內容類型（如技術、情感、身份等）進行過濾路由。
- **Drawer (抽屜)**：儲存最原始的 verbatim 記憶片段。

### 2.3 知識關聯與驗證
- **跨翼隧道 (Cross-Wing Tunnels)**：支持在不同的知識域 (Wings) 之間建立顯式鏈接，將碎片化的資訊轉化為網狀的知識體系。
- **事實檢查 (Fact Checker)**：通過對照實體註冊表與知識圖譜，在輸出前驗證記憶片段的真實性，有效降低 AI 幻覺。

## 3. 動態適應能力 (Dynamic Depth)
MemPalace 與 `google-reliability-guardian` 聯動，根據系統健康狀態動態調整檢索深度 (`MP_LIMIT`)：
- **Normal**: 深度 5 (完整認知)
- **Warning**: 深度 3 (速度優先)
- **Critical**: 深度 1 (極簡生存模式)

## 4. 記憶分佈 (Wing Distribution)
- **ks-system**: 儲存核心原則與系統級決策。
- **openclaw-workspace**: 儲存開發日誌與技能配置。
- **wing_kingseanks**: 儲存個人生活紀錄與日記。

## 5. 總結
MemPalace Phase 4 通過引入 BM25 混合搜尋、層級索引和知識圖譜鏈接，成功將 AI 的長期記憶從「模糊的聯想」提升到了「精確的檢索」與「邏輯化的關聯」層級。


---

