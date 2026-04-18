#!/usr/bin/env python3
"""
CDP Google Maps 每人消費讀取器
透過 Chrome DevTools Protocol 操控 OpenClaw 瀏覽器分頁，
讀取 Google Maps 的動態「每人消費」資訊。

使用方式：
  python3 cdp_client.py <place_id> [--histogram]

範例：
  python3 cdp_client.py ChIJS2rX4KoXaTQRFmBySDRuXYc
"""

import json
import asyncio
import sys
import re
import argparse

try:
    import websockets
except ImportError:
    print("錯誤：請先安裝 websockets")
    print("  pip3 install --break-system-packages websockets")
    sys.exit(1)

HOST = "127.0.0.1"
PORT = 18800

# ─── CDP 核心 ───────────────────────────────────────────────

class CDPClient:
    """CDP WebSocket 客戶端（簡易單命令模式）"""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._pending = {}
        self._recv_task = None

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url)
        # 啟用必要 domain（不等回應，避免 blocked）
        await self._send(1, "Runtime.enable")
        await self._send(2, "DOM.enable")
        await self._send(3, "Page.enable")
        await asyncio.sleep(0.5)

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def _send(self, mid: int, method: str, params: dict = None):
        msg = {"id": mid, "method": method}
        if params:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))

    async def call(self, mid: int, method: str, params: dict = None, timeout: float = 15.0) -> dict:
        """傳送 CDP 命令，等待並回傳 result"""
        await self._send(mid, method, params)
        try:
            r = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            d = json.loads(r)
            if "error" in d:
                return {"result": {"value": {"error": d["error"]}}}
            return d
        except asyncio.TimeoutError:
            return {"result": {"value": {"timeout": True, "method": method}}}

    # 便利包裝
    async def eval(self, expr: str, timeout: float = 15.0) -> dict:
        r = await self.call(99, "Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True
        }, timeout=timeout)
        return r.get("result", {}).get("result", {}).get("value", {})

    async def eval_bool(self, expr: str) -> bool:
        r = await self.eval(expr, timeout=5)
        return bool(r) if r else False

    async def eval_text(self, expr: str, timeout: float = 15.0) -> str:
        r = await self.eval(expr, timeout=timeout)
        return r if isinstance(r, str) else str(r) if r else ""

# ─── 價格讀取邏輯 ─────────────────────────────────────────

async def scrape_price(client: CDPClient, place_id: str, histogram: bool = False) -> dict:
    """對已連接的分頁讀取每人消費資訊"""

    # 確認是正確的分頁
    url = await client.eval_text("window.location.href", timeout=5)
    target_url = f"place_id:{place_id}"

    if target_url not in url:
        # 導航到目標頁面
        await client.call(10, "Page.navigate", {
            "url": f"https://www.google.com/maps/place/?q={target_url}"
        }, timeout=10)
        await asyncio.sleep(5)

    # 等「每人消費」就緒（輪詢，最長20秒）
    for i in range(20):
        ready = await client.eval_bool(
            "document.body.innerText.includes('per person') && document.body.innerText.includes('$')"
        )
        if ready:
            break
        await asyncio.sleep(1)
    else:
        # 備用：只要有 $ 數字
        await asyncio.sleep(2)

    # ── 讀取價格 ──────────────────────────────────────
    price_text = await client.eval_text("""
(function(){
  var text = document.body.innerText;
  // 解析 "$1–200 per person Reported by 81 people"
  var rangeRe = /\\$([\\d,]+)[\\-–]\\$?([\\d,]+)\\s*per person/i;
  var m = text.match(rangeRe);
  var range = m ? '$' + m[1] + '–$' + m[2] : null;
  var reporterRe = /Reported by (\\d+)/i;
  var rm = text.match(reporterRe);
  var reporter = rm ? rm[1] + '人回報' : null;
  return JSON.stringify({range: range, reporter: reporter, raw: text.match(/\\$[\\d,]+\\$?/g) || []});
})()
""", timeout=15)

    import json as _json
    try:
        price_data = _json.loads(price_text) if price_text else {}
    except:
        price_data = {}

    result = {
        "price_range": price_data.get("range"),
        "reporter": price_data.get("reporter"),
        "histogram": []
    }

    # ── 讀取分布圖（可選）──────────────────────────────
    if histogram:
        # 點擊 per person 按鈕
        click_info = await client.eval("""
(function(){
  var btns = document.querySelectorAll('button');
  for (var i=0; i<btns.length; i++) {
    var b = btns[i];
    var a = b.getAttribute('aria-label') || '';
    var t = b.innerText || '';
    if ((a.includes('per') && a.includes('$')) || (t.includes('per') && t.includes('$'))) {
      var rect = b.getBoundingClientRect();
      if (rect.width > 0) {
        return {found: true, x: Math.round(rect.left + rect.width/2), y: Math.round(rect.top + rect.height/2), label: a || t};
      }
    }
  }
  return {found: false};
})()
""", timeout=10)

        if isinstance(click_info, dict) and click_info.get("found"):
            x, y = click_info["x"], click_info["y"]
            # 滑入 → 按下 → 放開（CDP Input）
            await client.call(20, "Input.dispatchMouseEvent", {
                "type": "mouseMoved", "x": x, "y": y, "button": "none", "modifiers": 0
            }, timeout=3)
            await asyncio.sleep(0.3)
            await client.call(21, "Input.dispatchMouseEvent", {
                "type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1, "modifiers": 0
            }, timeout=3)
            await asyncio.sleep(0.2)
            await client.call(22, "Input.dispatchMouseEvent", {
                "type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1, "modifiers": 0
            }, timeout=3)
            await asyncio.sleep(2.5)

            # 讀取分布圖
            hist = await client.eval("""
(function(){
  var tables = document.querySelectorAll('table');
  for (var i=0; i<tables.length; i++) {
    var rows = tables[i].querySelectorAll('tr');
    var result = [];
    for (var j=0; j<rows.length; j++) {
      var cells = rows[j].querySelectorAll('td');
      if (cells.length >= 2) result.push([cells[0].innerText.trim(), cells[1].innerText.trim()]);
    }
    if (result.length > 0) return JSON.stringify(result);
  }
  return '[]';
})()
""", timeout=10)
            try:
                if hist:
                    result["histogram"] = _json.loads(hist)
            except:
                pass

    return result

# ─── 找分頁 ───────────────────────────────────────────────

def find_maps_tab():
    """用 HTTP 取分頁清單"""
    import urllib.request
    req = urllib.request.Request(f"http://{HOST}:{PORT}/json")
    with urllib.request.urlopen(req, timeout=10) as r:
        tabs = json.loads(r.read())
    for tab in tabs:
        if tab.get("type") == "page" and "google.com/maps" in tab.get("url", ""):
            return tab
    for tab in tabs:
        if tab.get("type") == "page":
            return tab
    return None

# ─── 主程式 ───────────────────────────────────────────────

async def main_async(args):
    place_id = args.place_id
    tab = find_maps_tab()
    if not tab:
        print("錯誤：找不到瀏覽器分頁，請先開啟 Google Maps")
        sys.exit(1)

    ws_url = tab["webSocketDebuggerUrl"]
    client = CDPClient(ws_url)

    try:
        await client.connect()
        result = await scrape_price(client, place_id, args.histogram)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await client.close()

def main():
    parser = argparse.ArgumentParser(description="CDP Google Maps 每人消費讀取器")
    parser.add_argument("place_id", help="Google Places ID")
    parser.add_argument("--histogram", action="store_true", help="讀取價格分布")
    args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
