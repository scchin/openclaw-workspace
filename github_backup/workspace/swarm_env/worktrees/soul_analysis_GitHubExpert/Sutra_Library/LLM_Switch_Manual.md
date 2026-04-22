# OpenClaw 模型配置管理專家 (llm-switch) 實作指南

## 📖 前言
本指南旨在提供一套標準化的流程，用於實作 OpenClaw 的模型生命週期管理技能 `llm-switch`。本技能將模型切換從「危險的手動 JSON 修改」轉化為「安全、可驗證且可回滾的自動化流程」。

## 第一章：核心設計哲學

### 1.1 配方驅動 (Recipe-Based)
禁止在程式碼中硬編碼模型參數。所有模型配置（Provider, ID, 最佳化參數）必須封裝在 `recipes.json` 中。
- **優點**：增加新模型無需修改程式碼，只需新增配方。

### 1.2 原子化操作 (Atomic Operations)
切換模型被定義為一個原子操作鏈：
`建立快照` $\rightarrow$ `修改配置` $\rightarrow$ `連通性驗證` $\rightarrow$ `(失敗則) 自動回滾` $\rightarrow$ `(成功則) 系統重啟`。

---

## 第二章：實作步驟與配置 (標準官方路徑)

### 2.1 創建流程：絕對禁止手動創建
必須使用官方 `skill-creator` 框架以確保系統能正確識別技能：
1. **初始化**：`python3 .../init_skill.py llm-switch --path ~/.openclaw/skills --resources scripts`
2. **實作**：編寫 `config_manager.py` 並配置 `recipes.json`。
3. **驗證**：`python3 .../package_skill.py ~/.openclaw/skills/llm-switch` (確保 `[OK] Skill is valid!`)。

### 2.2 配置文件結構
```text
llm-switch/
├── SKILL.md               # 必須包含正確的 YAML frontmatter (name: llm-switch)
├── recipes.json           # 儲存模型配方 (例如 gemma-4-31b, ollama)
└── scripts/
    └── config_manager.py  # 核心執行引擎
```

---

## 第三章：【核心】避坑指南 (The Pitfalls)

### 3.1 macOS SSL 憑證陷阱
**現象**：`urllib` 請求 HTTPS 時觸發 `CERTIFICATE_VERIFY_FAILED`。
**解決方案**：在 `config_manager.py` 中，若捕獲到 SSL 錯誤，必須立即切換至 `ctx.verify_mode = ssl.CERT_NONE` 重新嘗試。

### 3.2 HTTP 403 「虛假離線」誤判
**現象**：API 端點在無 Key 時返回 `403 Forbidden`，易被誤判為伺服器故障。
**解決方案**：將 `401` 與 `403` 狀態碼視為 「服務在線」 的信號，認證由 OpenClaw 運行時處理。

### 3.3 `reasoning` 參數的物理必要性
針對 Gemma 4 系列，必須在 Recipe 中強制設定 `"reasoning": false`，以消除 `MALFORMED_RESPONSE` 崩潰。

---

## 第四章：安全防禦體系

### 4.1 三試回滾機制 (3-Attempt Auto-Rollback)
- **邏輯**：切換 $\rightarrow$ 驗證 $\rightarrow$ (失敗 $\times 3$) $\rightarrow$ **自動還原至 `.snapshot/` 備份**。
- **目標**：確保使用者永遠不會面對一個不可用的系統。

### 4.2 一站式自動重啟
- 修改配置後，必須執行 `openclaw gateway restart`，禁止要求使用者手動執行 `/reset`。

---

## 第五章：外部接口與協作規範

### 5.1 CLI 接口定義
- **切換模型**：`python config_manager.py switch <recipe_name>`
- **強制回滾**：`python config_manager.py rollback`

### 5.2 協作場景
支援主控 Agent 根據任務複雜度，動態切換執行 Agent 的模型（例如：深度分析用 Gemma 4 $\rightarrow$ 快速處理用 Ollama）。

---

## 第六章：測試驗證集
- **正向路徑**：`Ollama` $\rightleftharpoons$ `Gemma 4` 互換成功且 Gateway 重啟。
- **異常路徑**：模擬端點失效 $\rightarrow$ 確認系統在 3 次嘗試後自動回滾。
- **SSL 測試**：在 macOS 環境下確認可正常連通 Google AI API。

---
*本手冊基於 2026-04-17 實作版本編寫。*
