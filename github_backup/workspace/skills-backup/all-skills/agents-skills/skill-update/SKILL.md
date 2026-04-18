---
name: skill-update
description: 技能更新標準流程。當需要將某項修正、更新或重構落地到指定技能時呼叫此技能。觸發時機：技能行為異常修復、版本更新、依賴路徑變更、輸出格式調整、成員變更（新增/移除函式/指令碼）。此技能不是用来创建新技能，而是用来更新现有技能。
---

# 技能更新（Skill Update）

將修正內容系統性落地到技能的所有相關檔案，確保未來所有呼叫都能正確執行更新後的結果。

---

## 觸發條件

當遇到以下任一情況時，**必須**呼叫此技能：
- 技能行為異常，修正後需驗證
- 技能版本號更新（SKILL.md + 對應執行檔同步更新）
- 執行依賴改變（Python 路徑、venv、新增工具）
- 輸出格式調整（模板、欄位、成員）
- 函式或腳本新增/移除/重構

---

## 更新流程（5 步驟）

### Step 1：確認修正範圍

**取得修正前後的差異**，明確定義：
- 哪些檔案被修改？
- 修改的性質？（語法錯誤修復、邏輯變更、版本號更新、依賴變更）
- 為什麼需要這個修正？

```
修正範圍確認清單：
□ 修改的檔案路徑
□ 修改的性質
□ 需要同步更新的相依檔案
□ 預期更新後的行為
```

### Step 2：更新執行檔（核心邏輯）

找到技能的核心執行檔（通常是 `SKILL.md` 同目錄下的 `scripts/` 或直接是 `SKILL.md` 引用的主程式）。

**檢查清單：**
- [ ] 語法正確（import / 執行無錯誤）
- [ ] 版本號已更新（若適用）
- [ ] 所有函式/類別 export 完整
- [ ] 路徑依賴使用 `os.path.expanduser("~/...")` 或絕對路徑
- [ ] Python 直譯器版本正確（`#!/usr/bin/env python3` vs `python3.12` venv）

### Step 3：同步更新 SKILL.md

**SKILL.md 抬頭（YAML frontmatter）更新：**
- `description` 描述若變更，同步更新
- 版本號註記（建議格式）：`# {技能名（{版本（{日期：{更新摘要））`

**SKILL.md 正文更新：**
- 任何與執行檔同步的說明、參數、指令，必須保持一致
- 移除廢棄指令、新增變更的指令

### Step 4：同步更新 MEMORY.md

在 `~/.openclaw/workspace/MEMORY.md` 中找到該技能的紀錄區塊，更新：

```
## {技能名（自建 {版本）
- **v{版本（{日期）：{更新摘要**
```

若技能記錄區塊不存在，在地點查詢規則 / 技能設定 之後合適位置新增。

### Step 5：驗證測試

**三層驗證，全部通過才算完成：**

| 順序 | 驗證項目 | 標準 |
|------|----------|------|
| ① | 執行檔語法檢查 | `python3 -c "import sys; sys.path.insert(0,'scripts'); import xxx"` 無錯誤 |
| ② | SKILL.md 格式檢查 | YAML frontmatter 完整（`name` + `description`），標題含版本 |
| ③ | 實際執行測試 | 跑一次真實案例，確認輸出符合預期 |

若①失敗 → 停在 Step 2，先修語法
若②失敗 → 停在 Step 3，修 SKILL.md
若③失敗 → 停在 Step 2/3，找出根因再重來

**驗證完成後，更新 MEMORY.md 的版本紀錄才算正式落地。**

---

## 依賴路徑變更需要額外檢查

當更新涉及 Python 執行環境變更（例如從系統 python3 改為 venv python）時：

1. 確認目標 Python 直譯器存在且版本正確
2. 確認所有必要模組已安裝在目標環境
3. 更新所有 `subprocess.run(["python3", ...])` 為 `subprocess.run(["/abs/path/to/python", ...])`
4. 若有多個 subprocess 呼叫同一腳本，全部同步更新

---

## 複雜案例參考

### 案例：子技能呼叫路徑不一致

**情境：** `where-to-go/run.py` 用 `python3` 呼叫 `google-places/scripts/query.py`，但 playwright 只裝在 `.venv/bin/python`。

**處理流程：**
1. 在目標環境（`.venv`）測試確認哪些指令可正常執行
2. 找出所有呼叫點（`grep -n "python3.*query.py\|query.py.*full"`）
3. 統一置換為絕對路徑
4. 三層驗證

### 案例：翻譯對照表（rep_map）漏列 key

**情境：** `google-places` 的 `format_address()` 用 `rep_map` 置換地址中的英文，但 `Lane`（巷）、`Alley`（弄）等常見縮寫未列入，導致輸出地址殘留英文。

**處理流程：**
1. 找出翻譯對照表所在位置（`grep -n "rep_map" scripts/query.py`）
2. 確認滲漏的英文字根（WGS84 坐標網常用：`Lane`、`Alley`、`Ave`、`Avenue`、`St`/`Street`、`Rd`/`Road`）
3. 全部補入 `rep_map`，並確保替換順序為「長優先」（避免 `Rd` 先吃掉 `Zhongqing Rd` 的 `Rd`）
4. 更新版本號、SKILL.md、MEMORY.md

**預防原則：** 每當新增地址解析功能，必須同步列舉所有 WGS84 坐標網的標準縮寫。

### 案例：外部 CLI 回傳非目標語言（API fallback 設計）

**情境：** `goplaces` CLI 只回英文名稱，但輸出要求繁體中文。直接採用 CLI 回傳值會導致輸出夾雜英文。

**處理流程：**
1. 確認有替代資料來源（Google Places Details API v1 支援 `language=zh-TW` 回傳繁體）
2. 新增一個專屬函式取目標語言（`get_localized_name_addr()`）
3. 在 `format_output()` 中優先採用 API 回傳值，CLI 值降為 fallback
4. 更新版本號、SKILL.md、MEMORY.md

**預防原則：** 所有外部資料來源（CLI、API）一律以「輸出語言需求」為準，不默認 CLI 回傳語言等於可用語言。

### 案例：輸出格式上限寫死且缺附時間戳

**情境：** `extract_review_highlights()` 數量寫死 `>= 3` 而非參數化；網友心得輸出時只 `(author, note)` 缺時間戳；`format_reviews_price` 時間顯示「96天前」數字格式而非「3個月前」友好格式。

**處理流程：**
1. 將數量上限改為 10（`>= 10` / `[:10]`），非寫死常數
2. 增加 `reviews` 攜帶 `days_ago`，`extract_review_highlights` 回傳 `(author, note, time_str)`
3. 新增 `_days_friendly()` 將天數轉為「N天前」「N個月前」
4. `format_output` 中心得末尾附加 `（{time_str）`

**預防原則：** 每次變更輸出格式，必須全链路追蹤（`get_reviews` → `extract_*` → `format_output`），確認所有 consumers 都跟著更新。

### 案例：同一資料來源不同用途需不同時間範圍

**情境：** `get_reviews` 只回 6 個月內評論，但「網友心得」要全部時間、「用戶反饋價格」只留 6 個月內。若讓 `get_reviews` 預設值為無限制，則所有 callers 都需跟著調整。

**處理流程：**
1. `get_reviews(place_id, months=None)` 參數化，None 表示無限制
2. 在 `cmd_*` 層過濾 `reviews_6m = [r for r in all_reviews if r.get("days_ago",999) <= 180]`
3. `format_output` 多接一個 `all_reviews` 參數，用於網友心得；原有 `reviews` 繼續給價格回饋
4. 更新版本號、SKILL.md、MEMORY.md

**預防原則：** 同一底層資料有多種用途時，先確認每個 consumer 的需求再動手串改呼叫鏈。

### 案例：版本號跳號

**情境：** SKILL.md 版本為 v10，但執行檔已達 v10.1，MEMORY.md 未同步。

**處理流程：**
1. 以執行檔版本為準（因為是實際部署的版本）
2. SKILL.md 標題 + MEMORY.md 同時更新到 v10.1
3. 備註：MEMORY.md 需記載每次版本跳號的來龍去脈

---

## 快速參考

- 技能根目錄：`~/.openclaw/skills/{技能名/` 或 `~/.agents/skills/{技能名/`
- MEMORY.md：`~/.openclaw/workspace/MEMORY.md`
- 驗證指令：
 ```bash
 # 語法檢查
 python3 -c "import sys; sys.path.insert(0,'/path/to/scripts'); import target_module"
 
 # 實際執行測試
 cd /path/to/skill && python3 scripts/run.py "測試關鍵字"
 ```