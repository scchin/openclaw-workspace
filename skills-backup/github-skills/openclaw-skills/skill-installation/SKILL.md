---
name: skill-installation
description: 協助安裝、診斷與修復 OpenClaw 技能。當使用者提到「安裝技能」、「技能看不到」、「技能故障」或「更改技能名稱」時觸發。
---

# 技能安裝與診斷指南 (Skill Installation & Diagnostics)

本技能提供一套標準化流程，用於確保 OpenClaw 技能被正確安裝並能在控制面板中顯示。

## ⚠️ 核心前提 (Critical Premise)
**凡涉及任何技能的「安裝」、「配置」、「名稱變更 (Rename)」或「診斷不可見」之操作，必須視為一次完整的「重新安裝」，強制調用本技能並嚴格執行下列 SOP 流程，嚴禁跳步或僅執行部分修改。**

---

## 🛠️ 安裝與檢查流程

當需要安裝新技能、更改技能名稱或診斷「技能不可見」問題時，請遵循以下步驟：

### 1. 驗證實體檔案 (Physical Check)
- **路徑確認**：確認技能資料夾位於 `~/.openclaw/skills/<skill-name>/` 或 `~/.agents/skills/<skill-name>/`。
- **識別文件**：確認資料夾內必須包含 `SKILL.md`。
- **⚠️ 絕對匹配檢查 (Critical)**：**必須確保 `SKILL.md` 內 YAML frontmatter 的 `name` 欄位值，與該技能的「目錄名稱」完全一致（區分大小寫，無多餘空格）。**
  - *錯誤示例*：目錄名為 `backup-github` $\rightarrow$ `name: skills-backup-github` (❌ 導致 UI 消失)
  - *正確示例*：目錄名為 `backup-github` $\rightarrow$ `name: backup-github` (✅ 正常顯示)
- **格式校驗**：檢查 `SKILL.md` 開頭是否具有正確的 YAML frontmatter 格式：
  ```yaml
  ---
  name: <技能名稱>
  description: <描述>
  ---
  ```
- **權限檢查**：確保檔案權限為可讀取（如 `chmod 644 SKILL.md`）。

### 2. 配置註冊 (Configuration)
檢查 `~/.openclaw/openclaw.json` 中的 `skills` 區塊：
- **Entries 啟用**：在 `skills.entries` 中添加該技能並設定 `"enabled": true`。
- **許可清單**：若該技能被視為內建或需強制顯示，請將其名稱加入 `skills.allowBundled` 列表中。

### 3. 生效與重啟 (Activation)
修改配置後，必須重啟 Gateway 才能重新掃描技能目錄：
- 執行指令：`/Users/KS/.nvm/versions/node/v22.22.2/bin/openclaw gateway restart`

---

## 🔍 進階故障排除 (Troubleshooting)

若上述步驟完成後，技能在控制面板中依然**看不到**，請嘗試以下進階方案：

### A. 排除目錄名稱衝突與過濾
部分系統可能會過濾特定關鍵字或長度過長的目錄名。
- **方案**：嘗試將目錄重命名為較簡短的名稱（例如 `skills-backup-github` $\rightarrow$ `backup-github`），並同步更新 `openclaw.json`。

### B. 清理不可見字符 (Invisible Characters)
從網頁複製內容時，可能會帶入 BOM 或非標準空格，導致 YAML 解析失敗。
- **方案**：重新手動撰寫 `SKILL.md` 的 frontmatter 部分，確保沒有多餘的空格或隱形字符。

### C. 驗證 API 回傳
使用 `curl` 直接呼叫 Gateway API 檢查後端是否已認可該技能：
- 指令：`curl -H "Authorization: Bearer <TOKEN>" "http://127.0.0.1:18789/skills/status"`
- 若 API 回傳包含該技能但 UI 不顯示 $\rightarrow$ **前端緩存問題**（請 Hard Refresh 瀏覽器）。
- 若 API 不回傳 $\rightarrow$ **後端加載失敗**（檢查 `SKILL.md` 格式及名稱匹配度）。

---

## 📝 操作記錄建議
每次安裝或修正後，建議在 `MEMORY.md` 記錄該技能的路徑與配置狀態，以便日後維護。
