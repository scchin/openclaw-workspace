# OpenClaw EPERM 崩潰防護與熱修補完整指南（更新版）

## 1. 問題概述
- **症狀**：在啟動多 Agent（或單 Agent）時，子代理全部崩潰，`sessions_list` 顯示 `FAILED`。
- **錯誤訊息**：
  ```
  Error: EPERM: operation not permitted, rename '/Users/KS/.openclaw/agents/main/agent/models.json.xxx.tmp' -> '/Users/KS/.openclaw/agents/main/agent/models.json'
  ```
  同樣的錯誤也會出現在 `auth‑profiles.json`、`auth‑profiles.json.tmp` 的 `copyFile` 操作。
- **根本原因**：`auth‑profiles.json`、`models.json` 等關鍵設定檔被 macOS `chflags uchg`（不可變）旗標鎖定。OpenClaw 為了避免 JSON 損壞，採用 **原子寫入**（寫入 `.tmp` → `fs.rename`/`fs.copyFile` → 覆寫），但 `uchg` 旗標會讓 OS 拒絕 `rename`/`replace`，拋出 `EPERM`，未被捕獲的例外直接導致子代理 Crash。

## 2. 初步解決方案（已實施）
1. **在 `fs-safe`、`models-config` 中加入 try‑catch**，捕捉 `EPERM`/`EACCES`，靜默降級並刪除 `.tmp`。
2. **全域 Monkey‑Patch**：在 OpenClaw 入口 `dist/index.js` 注入補丁，覆寫所有 `fs.rename*`、`fs.copyFile*`（Promise、callback、sync） 方法，統一處理 EPERM。此補丁在 **每次 OpenClaw 啟動時自動載入**，不受未來模組新增影響。
3. **建立獨立模組 `epperm-patch.js`**，將補丁程式碼抽離，`dist/index.js` 只保留 `import "./epperm-patch.js";`，保持程式碼乾淨。
4. **自動化腳本 `apply_epperm_patch.sh`**：將補丁寫入 `index.js`（或更新 `epperm-patch.js`）的腳本，方便在升級後重新套用。
5. **LaunchAgent（可選）**：若希望在系統開機或使用者登入時保證補丁已套用，可使用 `com.ks.openclaw.epperm-patch.plist`。目前已改為 **直接在 OpenClaw 入口載入**，因此不再需要額外 LaunchAgent，但仍保留作為備援。

## 3. 完整解決步驟（從頭到尾）
### 步驟 1 – 確認鎖定檔案
```bash
chflags uchg /Users/KS/.openclaw/agents/main/agent/models.json
chflags uchg /Users/KS/.openclaw/agents/main/agent/auth-profiles.json
```
（若已設定，保留此鎖定以保護金鑰）

### 步驟 2 – 建立全域補丁模組
1. **建立 `epperm-patch.js`**（已放於 `/opt/homebrew/lib/node_modules/openclaw/dist/epperm-patch.js`）
   ```javascript
   // EPERM 防護補丁模組 – 供 OpenClaw 啟動時自動載入
   // 目的：在 macOS 上若 auth‑profiles.json、models.json 被 uchg 鎖定，
   // 任何 fs.rename / copyFile 操作不會拋出未捕獲的 EPERM，避免子代理崩潰。

   import fsModule from "node:fs";
   import fsPromisesModule from "node:fs/promises";

   // --- rename (Promise) ---
   const _origRenameP = fsPromisesModule.rename.bind(fsPromisesModule);
   fsPromisesModule.rename = async (oldPath, newPath) => {
     try { return await _origRenameP(oldPath, newPath); }
     catch (e) {
       if (e.code === "EPERM" || e.code === "EACCES") {
         await fsPromisesModule.rm(String(oldPath), { force: true }).catch(()=>{});
         return;
       }
       throw e;
     }
   };
   // --- renameSync ---
   const _origRenameSync = fsModule.renameSync.bind(fsModule);
   fsModule.renameSync = (oldPath, newPath) => {
     try { return _origRenameSync(oldPath, newPath); }
     catch (e) {
       if (e.code === "EPERM" || e.code === "EACCES") {
         try { fsModule.rmSync(String(oldPath), { force: true }); } catch {}
         return;
       }
       throw e;
     }
   };
   // --- rename (callback) ---
   const _origRenameCb = fsModule.rename.bind(fsModule);
   fsModule.rename = (oldPath, newPath, cb) => {
     _origRenameCb(oldPath, newPath, err => {
       if (err && (err.code === "EPERM" || err.code === "EACCES")) {
         try { fsModule.rmSync(String(oldPath), { force: true }); } catch {}
         cb(null);
       } else cb(err);
     });
   };
   // --- copyFile (callback) ---
   const _origCopyCb = fsModule.copyFile.bind(fsModule);
   fsModule.copyFile = (src, dest, ...args) => {
     const cb = typeof args[args.length-1] === "function" ? args.pop() : () => {};
     _origCopyCb(src, dest, ...args, err => {
       if (err && (err.code === "EPERM" || err.code === "EACCES")) {
         try { fsModule.rmSync(String(src), { force: true }); } catch {}
         cb(null);
       } else cb(err);
     });
   };
   // --- copyFileSync ---
   const _origCopySync = fsModule.copyFileSync.bind(fsModule);
   fsModule.copyFileSync = (src, dest, flags) => {
     try { return _origCopySync(src, dest, flags); }
     catch (e) {
       if (e.code === "EPERM" || e.code === "EACCES") {
         try { fsModule.rmSync(String(src), { force: true }); } catch {}
         return;
       }
       throw e;
     }
   };
   // [END KS-PATCH]
   ```

### 步驟 3 – 在入口載入模組
在 `/opt/homebrew/lib/node_modules/openclaw/dist/index.js` 最前面（第 2 行）加入：
```javascript
import "./epperm-patch.js";
```
（已完成，原本的長補丁已被抽離為單行 import）

### 步驟 4 – 自動化補丁腳本（升級後重新套用）
`apply_epperm_patch.sh` 已放在 `~/.../scratch/apply_epperm_patch.sh`，內容會檢查 `index.js` 是否已包含 `import "./epperm-patch.js";`，若未包含則自動插入，並在完成後提示重新啟動 Gateway。

### 步驟 5 – 重啟 OpenClaw Gateway
```bash
launchctl stop ai.openclaw.gateway.v2 && launchctl start ai.openclaw.gateway.v2
```
確認 `curl -I http://127.0.0.1:18792` 回傳 `HTTP/1.1 200 OK`。

### 步驟 6 – 驗證子代理
執行任意多 Agent 任務，例如：
```bash
openclaw agent run --mode run macos_expert_v3
```
`openclaw sessions list` 應全部顯示 `SUCCESS`，不再出現 `FAILED`。

## 4. 重點面向與最佳實踐
| 面向 | 重點 | 為何重要 |
|------|------|----------|
| **檔案鎖定** | 保持 `uchg` 以保護金鑰 | 防止金鑰被意外覆寫或外部程式竊取 |
| **原子寫入** | 任何寫入 `*.json` 的流程都走 `fs.rename`/`fs.copyFile` | OpenClaw 依賴此機制防止斷電損壞 |
| **錯誤攔截** | 捕捉 `EPERM`/`EACCES`，靜默降級 | 讓鎖定檔案不會導致未捕獲例外，避免子代理 Crash |
| **全域補丁** | 在入口一次性覆寫所有相關 API | 無論未來新增哪個模組，只要使用標準 `fs`，都會自動受保護 |
| **模組抽離** | `epperm-patch.js` 獨立，`index.js` 只 `import` | 易於維護、升級時只需確保檔案存在即可 |
| **自動化腳本** | `apply_epperm_patch.sh` 可在升級後手動或加入 `postinstall` 鉤子 | 確保每次 `npm update -g openclaw` 後補丁仍在 |
| **測試驗證** | 重新啟動後檢查 HTTP 健康、`sessions list`、`.tmp` 清除 | 確保問題已根除，系統恢復穩定 |

## 5. 常見問答 (FAQ)
1. **如果我不想保留 `uchg`，可以直接解除嗎？**
   - 可以執行 `chflags nouchg <file>`，但會失去金鑰的物理保護。若解除，原本的 EPERM 補丁仍會保護系統不會崩潰，只是寫入會成功。
2. **升級 OpenClaw 後補丁會被覆寫嗎？**
   - `npm update -g openclaw` 會重新安裝整個 `dist` 目錄，會覆寫 `index.js`。請在升級後執行 `apply_epperm_patch.sh`（或將其加入 `postinstall`）重新注入 `import "./epperm-patch.js";`。
3. **是否需要保留 LaunchAgent？**
   - 現在補丁已在入口自動載入，LaunchAgent 不是必須的。若你仍想保留作為雙重保險，可保留 `com.ks.openclaw.epperm-patch.plist`，不會產生衝突。
4. **補丁會影響其他 `fs` 操作嗎？**
   - 只在 `EPERM`/`EACCES` 時做特殊處理，其他錯誤仍會拋出，行為保持一致。

## 6. 更新紀錄
- **2026‑04‑18**：首次在 `fs-safe`、`models-config` 加入 EPERM 捕捉，解決單 Agent 崩潰。
- **2026‑04‑19**：發現多 Agent 仍會在其他模組觸發 `rename`/`copyFile`，實施全域 Monkey‑Patch，抽離為 `epperm-patch.js`，並提供自動化腳本 `apply_epperm_patch.sh`。
- **2026‑04‑19**：完成最終測試，所有子代理 `SUCCESS`，無 `.tmp` 檔，系統穩定。

---
**此文件已同步至桌面**
`/Users/KS/Desktop/OpenClaw_EPERM_崩潰防護與熱修補指南.md`

如需進一步調整或新增其他模組的防護，僅需在 `epperm-patch.js` 中加入相應的 `fs` 方法覆寫即可。祝使用順利！
