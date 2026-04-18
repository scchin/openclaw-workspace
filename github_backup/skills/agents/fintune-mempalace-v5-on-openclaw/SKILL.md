---
name: fintune-mempalace-v5-on-openclaw
description: 專業級 MemPalace v5 (Develop) OpenClaw 深度整合與優化實作技能。本技能封裝了將 MemPalace 從官方版升級為 OpenClaw 客製化高能版本的完整流程，包含關聯喚醒、異構索引、時序有效性與智能分流四個核心維度的實作與驗證。
metadata:
  author: King Sean of KS
---

# Fintune-MemPalace-V5-on-OpenClaw

本技能旨在將 MemPalace 的原生能力轉化為 OpenClaw 系統的自動化行為，實現從「工具集成」到「認知系統工程」的跨越。

## 🛠️ 核心實作維度 (Optimization Pillars)

### 1. 關聯喚醒 (Relational Wake-up)
- **目標**：將啟動時的線性時間軸讀取升級為「核心實體 $\rightarrow$ 關聯狀態」的圖譜跳轉。
- **實作路徑**：修改 `wakeup.py` $\rightarrow$ 實作 `get_relational_context` $\rightarrow$ 注入高價值實體鏈接。

### 2. 異構索引隔離 (Heterogeneous Indexing)
- **目標**：根除技術術語與個人記憶之間的信號干擾。
- **實作路徑**：建立虛擬房映射 $\rightarrow$ 技術 $\rightarrow$ `skills` / 事實 $\rightarrow$ `memory` $\rightarrow$ 強制執行 Scoped Search。

### 3. 時序有效性 (Temporal Validity)
- **目標**：實現對動態事實的精確回溯 (State-over-Time)。
- **實作路徑**：配置時序實體關係圖 $\rightarrow$ 定義有效期限 (Validity Window) $\rightarrow$ 實作時序切片檢索。

### 4. 智能分流 (Intelligent Routing)
- **目標**：實現 0 噪音檢索，降低 Token 損耗。
- **實作路徑**：建立 lllm-level 路由判定 $\rightarrow$ 自動映射至正確 Room $\rightarrow$ 執行局部精準檢索。

## 🚀 實作流水線 (Implementation Pipeline)

### 第一階段：底層部署
1. **環境克隆**：從 `develop` 分支安裝最新版 `mempalace`。
2. **數據遷移**：執行原位升級，確保所有 Wing/Room 結構繼承。
3. **版本對標**：更新 `pyproject.toml` 版本號至 `5.0.0-dev`。

### 第二階段：行為對齊 (The Logic Alignment)
1. **喚醒邏輯重構**：更新 `wakeup.py` 實作關聯喚醒。
2. **技能指導更新**：修改 `SKILL.md` 強制 AI 使用路由搜尋模式。
3. **隔離層激活**：配置虛擬房間映射表。

### 第三階段：量化驗證 (Benchmark)
1. **R@10 測試**：驗證檢索率提升。
2. **SNR 測試**：驗證噪音率降低。
3. **時序回溯測試**：驗證狀態變遷追蹤精度。
4. **Latency 測試**：驗證路由後的響應速度。

## 📖 參考文獻
- `Sutra_Library/GRAND_ARCHIVE_MASTER_LIST.md` (藏經閣總表)
- `mempalace_v5_final_summary.md` (全量驗證總結)
- `mempalace_v5_comparison_report.md` (維度對比報告)

## ⚠️ 注意事項
- 必須確保 `mempalace` 安裝在正確的 Python 3.13 環境中。
- 任何對 `Sutra_Library` 的修改必須遵循「原子結案協議」。
