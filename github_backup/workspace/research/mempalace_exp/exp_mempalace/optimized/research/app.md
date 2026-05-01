# OpenClaw 應用層 (Application Layer) 研究分析報告

## 1. 技能系統 (Skills System) — 插件化能力擴展
OpenClaw 採用**解耦的插件式架構**，將具體功能從核心邏輯中抽離，實現能力的高靈活性擴展。

### 核心結論
- **定義驅動 (Definition-Driven)**：每個技能以 `SKILL.md` 為核心，定義了 AI 調用該能力的指令集、參數規範與操作流程。
- **分層部署 (Layered Deployment)**：
    - **系統層** (`/opt/homebrew/...`)：提供標準化、通用化的基礎技能。
    - **用戶層** (`~/.agents/skills/`)：支持高度自定義的私人技能與實驗性擴展。
- **資源封裝 (Resource Encapsulation)**：技能不僅包含指令，還可封裝 `_meta.json` (元數據)、`scripts/` (執行腳本) 與 `references/` (知識庫)，形成獨立的「能力單元」。

---

## 2. 交互邏輯 (Interaction Logic) — 行為約束框架
系統通過一套**三位一體 (Trinity Orchestration)** 的協同機制，將 AI 從單純的對話機器人轉化為具有「執行意識」的代理。

### 核心結論
- **協同矩陣 (The Trinity)**：
    - `mempalace` → 解決 **上下文/記憶** 的連續性。
    - `system-task-manager` → 解決 **物理狀態/進程** 的持久化（跨 Session 追蹤）。
    - `discipline-guardian` → 解決 **行為準則/回報紀律** 的強制執行。
- **狀態機恢復 (Recovery State-Machine)**：
    - 啟動時強制進入 `STATUS: RECOVERING` → 核對 `pending_tasks.json` → 補完報告 → 切換至 `STATUS: READY`。
- **原子化回報協議 (Atomic Reporting Protocol)**：
    - **首位標記**：所有工具執行結果必須以 `## 📋 任務結案報告` 開頭。
    - **主動同步**：複雜任務每 5 分鐘執行一次進度同步，杜絕「沉默執行」。
    - **哨兵機制 (Sentry)**：利用 `cron` 實現遞迴喚醒，確保任務在無人干預下能自動完結並回報。

---

## 3. 用戶界面 (User Interface) — 通訊層分析
UI 被設計為獨立的客戶端，通過輕量級橋接層與 AI 核心同步。

### 核心結論
- **通訊架構 (Communication Architecture)**：採用 **WebSocket + Sidecar** 模式。
- **同步橋接 (Sync Bridge)**：`sync_sidecar` (Port 18793) 作為中繼站，負責將 AI 核心的狀態變更推送到 UI 客戶端。
- **控制流 (Control Flow)**：支持通過外部觸發端點 (`/trigger-refresh`) 強制 UI 全量刷新，確保界面狀態與後端物理狀態的高度一致性。

## 關鍵參數總結
| 維度 | 關鍵組件/參數 | 核心功能 |
| :--- | :--- | :--- |
| **技能** | `SKILL.md` | 定義 AI 調用接口與行為準則 |
| **狀態** | `pending_tasks.json` | 跨 Session 任務持久化紀錄 |
| **紀律** | `discipline-guardian` | 強制執行回報協議與恢復流程 |
| **UI 通訊** | `sync_sidecar` (18793) | AI 核心 → UI 客戶端的同步橋接 |
