---
name: Install-MemPalace-on-OpenClaw
description: 從零開始在 OpenClaw 上安裝並整合 mempalace for OpenClaw 長期記憶系統的完整指南。支持從穩定版 (Phase 4) 到前瞻版 (Hybrid v5 Develop) 的完整部署路徑。包含下載、安裝、自動化 Hook 設定、MCP 設定及一鍵搬遷 SOP。觸發關鍵字：安裝 MemPalace、MemPalace 整合、mempalace 安裝、memcpy、mempalace setup。
author: King Sean of KS
---

# MemPalace for OpenClaw — AI 記憶宮殿安裝指南

本技能專注於**「物理安裝」**與**「環境部署」**。它確保 MemPalace 引擎正確地在 OpenClaw 環境中運行。

> ⚠️ **重要定義：安裝 $\neq$ 優化**
> 本技能負責將「軟體裝上去」 (Physical Install)。
> 若要將安裝後的 v5 引擎轉化為 OpenClaw 的自動化行為（如關聯喚醒、智能分流），請在完成本指南後，立即執行 **`Fintune-MemPalace-V5-on-OpenClaw`** 技能。

---

## 🚀 版本選擇路徑

根據您的需求，請選擇對應的安裝路徑：

### 路徑 A：穩定版 (Phase 4 Hybrid Edition)
適合追求極致穩定、不頻繁變動的環境。
- **特點**：BM25 混合搜尋、AAAK 索引、跨翼隧道。
- **部署**：執行本技能中的 `install_mempalace.sh` 腳本 $\rightarrow$ 完成基礎部署。

### 路徑 B：前瞻版 (Hybrid v5 Develop Branch) $\leftarrow$ **推薦**
適合需要最高認知效能、時序狀態追蹤與 0 噪音檢索的環境。
- **特點**：時序實體關係圖、動態分流路由、關聯喚醒能力。
- **部署流程 (專家級精準實作)**：
    1. **目標鎖定**：直接從 GitHub `develop` 分支克隆最新版本 $\rightarrow$ `https://github.com/MemPalace/mempalace` (Branch: `develop`)。
    2. **原位升級/安裝**：執行 `mempalace init` $\rightarrow$ 並在保留現有記憶數據的前提下完成底層引擎替換。
    3. **版本鎖定**：手動更新 `pyproject.toml` 中的版本號至 `5.0.0-dev` $\rightarrow$ 確保依賴庫與 v5 核心完全對標。
    4. **基礎 Hook 建立**：部署基礎的 `wakeup.py` 與 `mp` 快捷指令至 `~/.openclaw/hooks/`。

---

## 🛠️ 部署詳細步驟

### 1. 前置要求
| 項目 | 最低需求 | 建議 |
|------|----------|------|
| Python | 3.13+ | 3.13（ARM64 Mac） |
| pip | 最新版 | `pip3 install --upgrade pip` |
| OpenClaw | 最新版 | v12.x+ |

### 2. 執行安裝 (以 v5 Develop 為例)
```bash
# 1. 克隆 develop 分支
git clone -b develop https://github.com/MemPalace/mempalace.git ~/.mempalace_src

# 2. 安裝核心引擎
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pip install ~/.mempalace_src

# 3. 初始化宮殿
mempalace init --yes ~/.mempalace

# 4. 鎖定版本號 (編輯 pyproject.toml)
# 將 version 修改為 "5.0.0-dev"
```

### 3. 驗證與測試
執行以下指令確認引擎已就緒：
```bash
# 狀態檢查 (應顯示 v5 或 develop 相關標記)
mempalace status

# 測試基礎搜尋
mempalace search "測試關鍵字"
```

---

## 🔄 協同工作流：從安裝到激活

為了實現最高效能，請遵循以下**「兩步走」**戰略：

1. **第一步：物理安裝 (本技能)**
   - 使用 `Install-MemPalace-on-OpenClaw` $\rightarrow$ 達成 **「引擎就緒 (Engine Ready)」**。
   - 此階段完成後，系統擁有 v5 的能力，但行為仍是原生的（被動式）。

2. **第二步：行為激活 (配套技能)**
   - 執行 `Fintune-MemPalace-V5-on-OpenClaw` $\rightarrow$ 達成 **「行為對齊 (Behavior Active)」**。
   - 此階段將實作：關聯喚醒、智能分流、異構隔離。

**結論：只有 $\text{安裝} + \text{對齊} = \text{完整認知升級}$。**

---

## 📦 一鍵搬遷到新機器

### 自動化腳本
若需在新機器快速部署基礎環境，請執行：
```bash
zsh ~/.openclaw/skills/Install-MemPalace-on-OpenClaw/install_mempalace.sh
```

### 數據還原
1. 將舊機器的 `~/.mempalace/` 目錄完整複製到新機器相同路徑。
2. 重啟 Gateway：`openclaw gateway restart`。

---

## 疑難排解
- **Python 路徑錯誤**：請確認 `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` 存在。
- **版本衝突**：若升級後出現 `ImportError`，請重新執行 `pip install --force-reinstall ~/.mempalace_src`。
