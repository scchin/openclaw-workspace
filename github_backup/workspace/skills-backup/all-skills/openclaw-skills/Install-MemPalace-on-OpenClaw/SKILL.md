---
name: Install-MemPalace-on-OpenClaw
description: 從零開始在 OpenClaw 上安裝並整合 mempalace for OpenClaw 長期記憶系統的完整指南。包含下載、安裝、Phase 1/2/3 整合流程、自動化 Hook 設定、MCP 設定、以及一鍵搬遷到新機器的完整 SOP。觸發關鍵字：安裝 MemPalace、MemPalace 整合、mempalace 安裝、memcpy、mempalace setup。
author: King Sean of KS
---

# MemPalace for OpenClaw — AI 記憶宮殿 Phase 4 (Hybrid Edition)

## ⚡ Phase 4 核心進化
MemPalace 已從單純的向量儲存進化為**結構化知識圖譜管理系統**：
- ✅ **混合搜尋 (Hybrid Search)**：結合向量相似度 (60%) 與 BM25 關鍵字匹配 (40%)。
- ✅ **索引層 (Closet Layer)**：引入 AAAK 指針索引，大幅提升檢索速度。
- ✅ **跨翼隧道 (Cross-Wing Tunnels)**：支持在不同 Wing 之間建立顯式鏈接。
- ✅ **事實檢查 (Fact Checker)**：可對照實體註冊表驗證記憶碎片。
- ✅ **動態深度查詢 (Dynamic Depth)**：與 `google-reliability-guardian` 聯動，根據系統健康度自動調整檢索深度。

---

## 目錄

1. [前置要求](#前置要求)
# 2. [Phase 4：混合搜尋與知識圖譜整合](#phase-4混合搜尋與知識圖譜整合)
# 3. [驗證與測試](#驗證與測試)
# 4. [一鍵搬遷到新機器](#一鍵搬遷到新機器)
# 5. [疑難排解](#疑難排解)

---

## 前置要求

### 硬體與軟體

| 項目 | 最低需求 | 建議 |
|------|----------|------|
| Python | 3.13+ | 3.13（ARM64 Mac） |
| pip | 最新版 | `pip3 install --upgrade pip` |
| OpenClaw | 最新版 | v12.x+ |
| 磁碟空間 | 500MB | 2GB（隨著記憶增加） |
| RAM | 4GB | 8GB+ |

### 確認 Python 路徑

```bash
# 確認 Python 3.13 的路徑（必須）
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 --version
```

---

## Phase 4：混合搜尋與知識圖譜整合

1. **部署動態查詢引擎**：將 `mp_dynamic.py` 部署至 `~/.openclaw/workspace/`。
2. **配置索引層**：執行 `mempalace repair` 重建 AAAK 索引。
3. **啟用隧道功能**：透過 `mp tunnel` 指令建立跨 Wing 鏈接。
4. **整合可靠性守衛**：確保 `google-reliability-guardian` 運作中，以驅動動態深度檢索。

---

# 驗證與測試

執行以下指令確認 Phase 4 功能：
```bash
# 1. 狀態檢查
~/.openclaw/hooks/mempalace-for-openclaw-memory/mp status

# 2. 測試混合搜尋 (BM25 + Vector)
~/.openclaw/hooks/mempalace-for-openclaw-memory/mp search "精確版本號或冷門術語"

# 3. 測試跨翼隧道 (Tunnels)
~/.openclaw/hooks/mempalace-for-openclaw-memory/mp tunnel list

# 4. 測試動態深度查詢
python3 ~/.openclaw/workspace/mp_dynamic.py "核心原則"
```

---

## 一鍵搬遷到新機器

### 使用自動化安裝腳本
若需在新機器快速部署，請直接執行本技能目錄下的 `install_mempalace.sh`：
```bash
zsh ~/.openclaw/skills/Install-MemPalace-on-OpenClaw/install_mempalace.sh
```

### 數據還原流程
1. **安裝環境**：執行上述安裝腳本。
2. **還原資料**：將舊機器的 `~/.mempalace/` 目錄完整複製到新機器的相同路徑。
3. **重啟 Gateway**：`openclaw gateway restart`

---

## 疑難排解
- **Python 路徑錯誤**：請確認 `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` 存在。
- **ChromaDB Segfault**：執行 `mempalace repair` 或刪除 `~/.mempalace/chroma/` 後重新 init。