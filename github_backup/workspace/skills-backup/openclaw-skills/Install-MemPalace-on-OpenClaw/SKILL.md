---
name: Install-MemPalace-on-OpenClaw
description: 從零開始在 OpenClaw 上安裝並整合 mempalace for OpenClaw 長期記憶系統的完整指南。包含下載、安裝、Phase 1/2/3 整合流程、自動化 Hook 設定、MCP 設定、以及一鍵搬遷到新機器的完整 SOP。觸發關鍵字：安裝 MemPalace、MemPalace 整合、mempalace 安裝、memcpy、mempalace setup。
author: King Sean of KS
---

# Install-MemPalace-on-OpenClaw

> **完整安裝指南**：從下載到 Phase 3 完全接管，所有流程與關鍵設定。
> 
> **建立日期**：2026-04-11
> **更新日期**：2026-04-14 (Updated to mempalace for OpenClaw)
> **作者**：King Sean of KS
> **適用版本**：MemPalace v3.1.0 + OpenClaw 最新版

---

## 目錄

1. [前置要求](#前置要求)
2. [Phase 0：下載與安裝 MemPalace](#phase-0下載與安裝-mempalace)
3. [Phase 1：MCP Server 整合](#phase-1mcp-server-整合)
4. [Phase 2：雙寫 Hook 整合](#phase-2雙寫-hook-整合)
5. [Phase 3：完全取代舊記憶系統](#phase-3完全取代舊記憶系統)
6. [驗證與測試](#驗證與測試)
7. [一鍵搬遷到新機器](#一鍵搬遷到新機器)
8. [疑難排解](#疑難排解)

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

## Phase 0：下載與安裝 MemPalace

### Step 0.1：安裝 MemPalace
```bash
pip3 install mempalace
```

### Step 0.2：初始化 Palace 目錄
```bash
mempalace init --path ~/.mempalace --name KingSeanKS --agent KingSeanKS
```

---

## Phase 1：MCP Server 整合

**更新 `mcporter.json`：**
```json
"mempalace": {
 "command": "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
 "args": ["-m", "mempalace.mcp_server", "--palace", "/Users/[username]/.mempalace"]

```

---

## Phase 2：雙寫 Hook 整合

1. **建立目錄**：`mkdir -p ~/.openclaw/hooks/mempalace-for-openclaw-memory/`
2. **部署檔案**：部署 `hook_writer.py`, `handler.ts`, `HOOK.json` 及 `mp` CLI 工具。
3. **設定權限**：`chmod +x ~/.openclaw/hooks/mempalace-for-openclaw-memory/mp`

---

## Phase 3：完全取代舊記憶系統

1. **遷移資料**：執行記憶遷移腳本，將 `MEMORY.md` 與每日日誌搬遷至 MemPalace。
2. **部署喚醒引擎**：安裝 `wakeup.py` 用於 Session 啟動時的上下文注入。
3. **建立技能**：安裝 `mempalace for OpenClaw` 技能（SKILL.md）。

---

## 驗證與測試

執行以下指令確認系統健康：
```bash
# 狀態檢查
~/.openclaw/hooks/mempalace-for-openclaw-memory/mp status

# 記憶搜尋
~/.openclaw/hooks/mempalace-for-openclaw-memory/mp search "核心原則"

# 喚醒測試
python3 ~/.openclaw/hooks/mempalace-for-openclaw-memory/wakeup.py
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