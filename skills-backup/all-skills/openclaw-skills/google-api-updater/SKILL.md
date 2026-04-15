---
name: google-api-updater
description: 更新 Google Places API Key 與記錄專案編號。觸發場景：「更新 Google API」、「更改 API Key」
author: King Sean of KS
---

# Google API 更新工具 (Google API Updater)

本技能用於快速更新 `google-places` 技能所需的 API Key，並記錄對應的 Google Cloud 專案編號。

## 🛠️ 使用方式

執行路徑：`python3 ~/.openclaw/skills/google-api-updater/scripts/update.py --project <專案編號> --key <API_KEY>`

### 參數說明：
- `--project`: Google Cloud 專案編號（例如：481924623086），用於記錄對應關係。
- `--key`: 實際的 Google API Key（以 `AIza` 開頭）。

### 執行範例：
`python3 ~/.openclaw/skills/google-api-updater/scripts/update.py --project 481924623086 --key AIzaSyDlz5BN5QjXhmQ-x0uB4O3zTJTxNF8-PKE`

## ⚙️ 運作邏輯
1. 修改 `~/.openclaw/openclaw.json` 中的 `skills.entries.goplaces.env.GOOGLE_PLACES_API_KEY`。
2. 將專案編號與更新時間儲存至 `~/.openclaw/skills/google-api-updater/project_info.json` 以供日後核對。