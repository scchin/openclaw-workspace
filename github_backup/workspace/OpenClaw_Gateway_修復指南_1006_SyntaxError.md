# OpenClaw Gateway 修復指南：1006 斷線與底層語法錯誤 (SyntaxError)

**系統版本:** OpenClaw 2026.4.15
**問題狀態:** 已解決
**問題特徵:** 
- 前端 WebUI 出現 `disconnected (1006): no reason` 錯誤。
- 終端機執行 `openclaw gateway restart` 時提示 `Gateway service not loaded`。
- 本地 18792 通訊埠無法正確被 Gateway 綁定。

---

## 1. 狀況概述與現象

當使用者嘗試登入 OpenClaw 時，無論是區域網路還是本地端，都遭遇 WebSocket 斷線錯誤 (1006)。這通常代表伺服器端主動或異常終止了連線，且沒有給出正常的 WebSocket 關閉代碼。
進一步於終端機檢查服務時，發現原本該受 macOS `launchd` 控制的 `ai.openclaw.gateway.v2` 服務狀態極不穩定，甚至處於離線未載入的情形。

## 2. 深度診斷與排查邏輯

為確保不盲目修改設定檔（不冒險導致系統崩潰），採取了嚴謹的分段診斷模式：

### 步驟 2.1：埠口與服務狀態確認
首先利用 `lsof -i :18792` 與 `launchctl list | grep gateway` 檢查，發現：
- `lan_https_proxy.py` 依然佔據了區域網路 IP 的 `18792`。
- 但主 Gateway 的 PID 卻時有時無（一直變更），且結束代碼 (Exit Code) 呈現 `1`。
這代表 **Gateway 原本有啟動，但在啟動的瞬間立刻崩潰，隨後被系統無限重啟，導致 Port 一直無法讓出與接管**。

### 步驟 2.2：核心日誌抓取
至 `/tmp/openclaw` 目錄下撈取紀錄，發現了核心報錯：
```text
[gateway] starting...
Gateway failed to start: SyntaxError: missing ) after argument list
```

### 步驟 2.3：排除 JSON 設定檔異常
原先懷疑是 `openclaw.json` 或 `models.json` 中輸入了包含括號的特異字元，導致 Gateway 內部的 Node.js 解析引擎崩潰。但在完整驗證過所有的設定 JSON 皆合法後，此可能性被排除。這意味著問題藏在**開源包自身的底層編譯代碼**。

### 步驟 2.4：追蹤 Error Stack 以定位原始碼
Node.js 對於 Top-level `import()` 失敗時拋出的 SyntaxError，預設會丟失檔案路徑。因此，我們透過直接修改 CLI 進入點模組：
將 `/opt/homebrew/lib/node_modules/openclaw/dist/gateway-cli-CMMHuc-I.js` 檔案中，捕獲錯誤的邏輯由原本單純的：
`String(err)`
調整為：
`err instanceof Error ? err.stack : String(err)`

這讓我們成功擷取到崩潰的原始檔為：
`/opt/homebrew/lib/node_modules/openclaw/dist/server.impl-GQ72oJBa.js`。

---

## 3. 根源與解決方案

透過追溯報錯行數，我們發現本次更新的 JavaScript 編譯輸出檔，在兩處事件推送的代碼裡，發生了**原生的「漏字」錯誤 (Typo)**。在呼叫 `JSON.stringify` 並包裝 `_purify` 函數時，結尾缺少了一個 `)`。

### 具體修復範圍（嚴守不更動非相關代碼原則）
目標檔案：`/opt/homebrew/lib/node_modules/openclaw/dist/server.impl-GQ72oJBa.js`

**修正點一 (約置於 16040 行)：**
```javascript
// 【修正前】
node.client.socket.send(JSON.stringify(_purify({
    type: "event",
    event,
    payload
})); // <- 缺少一個括號

// 【修正後】
node.client.socket.send(JSON.stringify(_purify({
    type: "event",
    event,
    payload
})));
```

**修正點二 (約置於 17830 行)：**
```javascript
// 【修正前】
body = JSON.stringify(_purify({
    ok: true,
    status
}); // <- 缺少一個括號

// 【修正後】
body = JSON.stringify(_purify({
    ok: true,
    status
}));
```

---

## 4. 修復驗證與後續維護

在精確補上缺失的兩處右括號後：
1. `launchctl` 成功喚醒 Gateway。
2. 背景進程順利啟動並穩定持有本機的 `127.0.0.1:18792` 與區網憑證代理。
3. `curl HTTP 200` 返回連線健康，前端 `1006` 錯誤徹底消失。

**給後續系統維護之建議：**
- **勿依賴表面提示：** 遇到 `1006 no reason` 不要直接懷疑網路環境，應優先看服務是否進入「崩潰重啟死循環」。
- **修改底層時的穩健原則：** Node.js 經常會模糊化 SyntaxError，必要時必須主動在啟動處印出 `err.stack` 來捕獲真正的原始引發點。
- **針對套件升級的風險：** 系統編譯（特別是具有過渡依賴或混淆代碼時）可能極其罕見地引發這種靜態漏字。不要重新安裝大版本的 `npm` 包，精準點修可以免除其他環境變數全部丟失的風險。
