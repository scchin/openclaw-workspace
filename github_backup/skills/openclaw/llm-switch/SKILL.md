---
name: llm-switch
description: "模型配置管理專家。透過自然語言在 Gemma 4、Ollama 等模型之間無縫切換，支援自動快照、連通性驗證與自動回滾。觸發場景：『切換到 Gemma 4』、『使用 Ollama』、『切換模型』"
---

# LLM Switch (模型配置管理專家)

## 技能描述
`llm-switch` 是一個專業的模型生命週期管理技能，允許使用者透過自然語言或程式化接口，在不同的 LLM 配置方案（Recipes）之間無縫切換。它整合了自動快照、連通性驗證與自動回滾機制，確保模型切換過程絕對安全且透明。

## 觸發條件 (Triggers)
當使用者輸入包含以下關鍵字或意圖時，必須觸發此技能：
- `切換到 [模型名稱]`
- `使用 [模型名稱]`
- `Switch to [模型名稱]`
- `更改模型為 [模型名稱]`
- `設定模型 [模型名稱]`

## 執行指令 (Execution)

### 1. 模型切換 (Switch)
**指令**：`uv run python ~/.openclaw/skills/llm-switch/scripts/config_//_manager.py switch <recipe_name>`

### 2. 強制回滾 (Rollback)
**指令**：`uv run python ~/.openclaw/skills/llm-switch/scripts/config_manager.py rollback`

## 執行紀律 (Operational Discipline)
1. **前置操作**：執行切換前，告知使用者目標模型。
2. **後置操作**：切換成功後，引導使用者執行 `/reset`。
3. **故障處理**：若觸發回滾，明確告知使用者。

## 資源路徑
- **配方庫**：`~/.openclaw/skills/llm-switch/recipes.json`
- **核心引擎**：`~/.openclaw/skills/llm-switch/scripts/config_manager.py`
