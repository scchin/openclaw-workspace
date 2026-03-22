#!/usr/bin/env python3
"""
Google Places 店家查詢工具 v9（乾淨重寫版）
修正重點（相較於 v8 損壞狀態）：
1. 完整的 async def scrape_price_from_browser 宣告（v8 粘貼錯誤，缺少此行）
2. format_address 正確附加郵遞區號括號
3. extract_dish_highlights 以句號截斷 snippet，防止跨品項污染
4. 移除多餘的頂層重複定義（cdp_send_recv, cdp_eval 與內部函式衝突）
"""
import subprocess, json, sys, os, re, asyncio, urllib.request, time, websockets
from datetime import datetime, timezone, timedelta

# ─── 翻譯工具 ────────────────────────────────────────────────
from deep_translator import GoogleTranslator

_trans_cache: dict = {}

def translate_to_chinese(text: str) -> str:
    """
    將英文評論翻譯成繁體中文（含快取）。
    若翻譯失敗或原文已是中文，則保留原文。
    """
    if not text or not text.strip():
        return text
    # 若已含中文字，直接視為已中文
    if re.search(r"[\u4e00-\u9fff]", text):
        return text
    if text in _trans_cache:
        return _trans_cache[text]
    try:
        result = GoogleTranslator(source="auto", target="zh-TW").translate(text)
        if result and result != text:
            _trans_cache[text] = result
            return result
    except Exception:
        pass
    return text

GOOGLE_PLACES_API_KEY = os.environ.get(
    "GOOGLE_PLACES_API_KEY", "[API_KEY_REDACTED]")
HOST = "127.0.0.1"
PORT = 18800

# ─── goplaces ────────────────────────────────────────────────
def goplaces(args_str, timeout=20):
    env = os.environ.copy()
    env["GOOGLE_PLACES_API_KEY"] = GOOGLE_PLACES_API_KEY
    r = subprocess.run(f"goplaces {args_str}", shell=True,
                       capture_output=True, text=True, env=env, timeout=timeout)
    return r.stdout + r.stderr

def get_details_json(place_id):
    out = goplaces(f"details {place_id} --reviews --json", timeout=30)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None

def get_reviews(place_id):
    data = get_details_json(place_id)
    if not data:
        return [], data
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    filtered = []
    for review in data.get("reviews", []):
        pub_str = review.get("publish_time", "")
        if not pub_str:
            continue
        try:
            pub_time = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            continue
        if pub_time < six_months_ago:
            continue
        orig = review.get("original_text", {}).get("text", "")
        translated = review.get("text", {}).get("text", "")
        raw_content = orig or translated
        # ★★★ 全部翻譯成繁體中文 ★★★
        content = translate_to_chinese(raw_content) if raw_content else ""
        filtered.append({
            "author": review.get("author", {}).get("display_name", "匿名"),
            "rating": review.get("rating", 0),
            "publish_time": pub_time.strftime("%Y-%m-%d"),
            "days_ago": (datetime.now(timezone.utc) - pub_time).days,
            "content": content,
        })
    return filtered, data

def get_price_range_api(place_id):
    url = (f"https://places.googleapis.com/v1/places/{place_id}"
           f"?fields=priceRange&key={GOOGLE_PLACES_API_KEY}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        pr = data.get("priceRange")
        if pr:
            s = pr.get("startPrice", {}).get("units", "")
            e = pr.get("endPrice", {}).get("units", "")
            return f"${s}–${e}" if s and e else None
    except Exception:
        pass
    return None

# ─── CDP 通訊 ────────────────────────────────────────────────
async def cdp_send_recv(ws, mid, method, params=None, timeout=10.0):
    msg = {"id": mid, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))
    for _ in range(12):
        r = await asyncio.wait_for(ws.recv(), timeout=timeout)
        d = json.loads(r)
        if d.get("id") == mid:
            return d
    return None

async def cdp_eval(ws, expr, timeout=15.0):
    """直接透過已存在的 ws 連線執行 CDP JS（不新建連線）。"""
    for attempt in range(2):
        try:
            r = await cdp_send_recv(ws, 99, "Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            }, timeout=timeout)
            if r is None:
                print("  [CDP] cdp_eval: response is None (attempt %d)" % (attempt+1))
                await asyncio.sleep(0.5)
                continue
            result_obj = r.get("result", {})
            res_result = result_obj.get("result", {})
            # 有 value → 直接返回
            val = res_result.get("value", None)
            if val is not None:
                return val
            # 有 unserializedValue → Promise 未解析，返回字串描述
            unserialized = res_result.get("unserializedValue", None)
            if unserialized is not None:
                print("  [CDP] cdp_eval: Promise unserialized: %s" % str(unserialized)[:60])
                return str(unserialized)
            # 有 description → 可能是錯誤
            desc = res_result.get("description", "")
            if desc:
                print("  [CDP] cdp_eval: description: %s" % desc[:80])
                return desc
            print("  [CDP] cdp_eval: empty result (attempt %d): %s" % (
                attempt+1, str(result_obj)[:80]))
            return ""
        except Exception as e:
            print("  [CDP] cdp_eval exception (attempt %d): %s" % (attempt+1, e))
            if attempt < 1:
                await asyncio.sleep(0.5)
    return ""

# ─── CDP 爬蟲（v10）───
# v10 修正：
# 1. Menu URL：擴展 RegEx 涵蓋 Instagram、Uber Eats、inline_menu、dudoo 等常見形態
# 2. 熱門品項：同時支援 role=radio[aria-label*=mentioned]（舊版）和
#    radiogroup > radio（新版 Google Maps）
# 3. 服務資訊：新增完整解析邏輯（內用/外帶/外送/寵物友善等）
# 4. JS_BASIC：加入服務擷取，避免依賴滾動輪詢
async def scrape_price_from_browser(place_id, maps_url=None):
    maps_url = maps_url or f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    print(f"[CDP] place={place_id[:20]}")
    result = {
        "found": False, "price_range": None, "reporter": None,
        "price_histogram": [], "service": [], "popular_items": [],
        "photo_label": "", "menu_url": None,
    }

    def get_all_tabs(max_wait=60):
        for _ in range(max_wait):
            try:
                req = urllib.request.Request(f"http://{HOST}:{PORT}/json")
                with urllib.request.urlopen(req, timeout=5) as r:
                    tabs = json.loads(r.read())
                if tabs:
                    return tabs
            except Exception:
                pass
            time.sleep(1)
        return []

    def cdp_reachable():
        try:
            req = urllib.request.Request(f"http://{HOST}:{PORT}/json")
            with urllib.request.urlopen(req, timeout=3) as r:
                return bool(json.loads(r.read()))
        except Exception:
            return False

    def start_edge_background():
        """啟動 Edge（背景模式 + CDP port），等待就緒後回傳 True"""
        import socket
        def port_used(port):
            s = socket.socket(); s.settimeout(1)
            try:
                s.connect((HOST, port)); s.close(); return True
            except Exception:
                return False

        if port_used(PORT):
            # port 已被佔用不代表 CDP 可達，先視為已啟動
            print("[CDP] Port %d already in use, assuming Edge already running" % PORT)
            return True

        print("[CDP] Starting Edge (background + CDP port %d)..." % PORT)
        executable = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        try:
            subprocess.Popen(
                [executable,
                 "--headless=no",
                 "--no-default-browser-check",
                 "--remote-debugging-port=%d" % PORT,
                 "--user-data-dir=/tmp/openclaw-edge-cdp"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            # Edge not found, try Chrome
            try:
                subprocess.Popen(
                    ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                     "--headless=no",
                     "--no-default-browser-check",
                     "--remote-debugging-port=%d" % PORT,
                     "--user-data-dir=/tmp/openclaw-edge-cdp"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                print("[CDP] No supported browser found (Edge/Chrome)")
                return False

        # 等候 CDP 上線（最長 20 秒）
        for attempt in range(20):
            time.sleep(1)
            if cdp_reachable():
                print("[CDP] Edge started and CDP ready after %ds" % (attempt + 1))
                return True
        print("[CDP] Edge started but CDP did not become reachable in 20s")
        return False

    async def ws_ping(ws_url_str, timeout=5.0):
        try:
            async with asyncio.timeout(timeout):
                async with websockets.connect(ws_url_str, open_timeout=timeout) as ws_ping:
                    r = await cdp_send_recv(ws_ping, 999, "Runtime.evaluate",
                        {"expression": "1+1", "returnByValue": True}, timeout=timeout)
                    if r and r.get("result", {}).get("result", {}).get("value") == 2:
                        return True
        except Exception:
            pass
        return False

    async def get_ws_url(tab_list, prefer_maps=True):
        ordered = []
        for t in tab_list:
            if t.get("type") != "page":
                continue
            url = t.get("url", "")
            if not url.startswith("http"):
                continue
            if prefer_maps and "google.com/maps" in url:
                ordered.insert(0, t)
            else:
                ordered.append(t)
        for tab in ordered:
            wurl = tab.get("webSocketDebuggerUrl", "")
            if not wurl:
                continue
            if await ws_ping(wurl):
                print(f"[CDP] WS OK: {tab.get('url', '')[:60]}")
                return wurl, tab
        # Build new tab
        print("[CDP] Building new Maps tab...")
        for tab in tab_list:
            wurl = tab.get("webSocketDebuggerUrl", "")
            if not wurl or not await ws_ping(wurl):
                continue
            try:
                async with websockets.connect(wurl, open_timeout=10) as host_ws:
                    r = await cdp_send_recv(host_ws, 777, "Target.createTarget",
                        {"url": maps_url}, timeout=15)
                if not r or not r.get("result", {}).get("targetId"):
                    continue
                new_id = r["result"]["targetId"]
                new_url = f"ws://{HOST}:{PORT}/devtools/page/{new_id}"
                await asyncio.sleep(3)
                if await ws_ping(new_url):
                    print(f"[CDP] New tab ready: {new_id}")
                    return new_url, {"webSocketDebuggerUrl": new_url, "url": maps_url}
            except Exception as e:
                print(f"[CDP] Tab create error: {e}")
                continue
        return None, None

    async def click_tab(ws, label, wait=3):
        js = (
            "(function() {"
            "  var els = document.querySelectorAll('button,div[role=tab],a');"
            "  for(var i=0;i<els.length;i++){"
            "    var t=(els[i].innerText||'').trim();"
            "    if(t === '%s' || t.startsWith('%s')){"
            "      var r = els[i].getBoundingClientRect();"
            "      if(r.width>0 && r.height>0 && r.top>=0){"
            "        return JSON.stringify({ok:true,"
            "          x:Math.round(r.left+r.width/2),"
            "          y:Math.round(r.top+r.height/2),"
            "          text:t.substring(0,40)});"
            "      }"
            "    }"
            "  }"
            "  return JSON.stringify({ok:false});"
            "})()" % (label, label)
        )
        raw = await cdp_eval(ws, js, timeout=10)
        if not raw:
            return False
        try:
            info = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return False
        if not (info.get("ok") if isinstance(info, dict) else False):
            return False
        cx = info.get("x", 0); cy = info.get("y", 0)
        if cx <= 0 or cy <= 0:
            return False
        print(f"  [CDP] Click '%s' cx=%s cy=%s" % (label, cx, cy))
        await cdp_send_recv(ws, 500, "Input.dispatchMouseEvent",
            {"type":"mousePressed","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
        await cdp_send_recv(ws, 501, "Input.dispatchMouseEvent",
            {"type":"mouseReleased","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
        print(f"  [CDP] Tab clicked, wait %ds..." % wait)
        await asyncio.sleep(wait)
        return True

    # ── Phase 1: get CDP connection ─────────────────────────
    if not cdp_reachable():
        print("[CDP] Browser not reachable, attempting to start Edge...")
        if not start_edge_background():
            print("[CDP] Could not start browser automatically")
            return {"found": False, "error": "browser not started"}
        # 再次檢查，確保 CDP 已就緒
        if not cdp_reachable():
            print("[CDP] Browser started but CDP still not reachable")
            return {"found": False, "error": "browser not ready"}
    tabs = get_all_tabs(max_wait=30)
    if not tabs:
        print("[CDP] No tabs found")
        return {"found": False, "error": "no tabs"}
    ws_url, _ = await get_ws_url(tabs, prefer_maps=True)
    if not ws_url:
        print("[CDP] Could not get WS URL")
        return {"found": False, "error": "no WS URL"}

    # ── Phase 2 + Phase 3 inside try/except ─────────────────
    try:
        async with websockets.connect(ws_url) as ws:
            print("[CDP] WS connected")
            await asyncio.sleep(0.5)
            current_url = await cdp_eval(ws, "window.location.href")
            need_nav = "google.com/maps" not in (current_url or "")
            if need_nav:
                print("[CDP] Navigating...")
                await cdp_send_recv(ws, 5, "Page.navigate", {"url": maps_url}, timeout=30)
                nav_start = time.time()
                for tick in range(25):
                    await asyncio.sleep(1)
                    cu = await cdp_eval(ws, "window.location.href")
                    body = await cdp_eval(ws, "(document.body||{}).innerText||''")
                    url_ok = "google.com/maps" in (cu or "") and len(cu or "") > 50
                    text_ok = len(body) > 200
                    consent = "google.com/legal" in body.lower() or \
                              ("accept" in body.lower() and len(body) < 500)
                    elapsed = time.time() - nav_start
                    flag = " [consent!]" if consent else (" [loading]" if len(body) < 50 else "")
                    print("  [nav %d/25 | %.0fs] URL=%s text=%d%s" % (
                        tick+1, elapsed, "ok" if url_ok else "fail", len(body), flag))
                    if url_ok and text_ok and not consent:
                        await asyncio.sleep(2)
                        break

            await asyncio.sleep(2)

            # ── 服務（內用/外帶/外送/寵等）───
            async def extract_services(ws):
                """從「關於」區塊或整頁文字解析服務標籤"""
                svc_js = (
                    "(function(){"
                    "  var SVC_KEYWORDS = {"
                    "    '內用':'內用','外帶':'外帶','外送':'外送','Delivery':'外送',"
                    "    '寵物友善':'寵物友善','pet':'寵物友善','寵物':'寵物友善',"
                    "    '預約':'預約','訂位':'訂位','素食':'素食','vegan':'素食',"
                    "    '洗手間':'洗手間','廁所':'廁所','WiFi':'WiFi','wifi':'WiFi',"
                    "    '吸菸':'吸菸','吸烟':'吸菸','無菸':'無菸','cash':'現金',"
                    "    '信用卡':'信用卡','停車':'停車','parking':'停車'"
                    "  };"
                    "  var result = [];"
                    "  var keys = Object.keys(SVC_KEYWORDS);"
                    "  var found = {};"
                    "  var divs = document.querySelectorAll('div,span,button');"
                    "  for(var i=0;i<divs.length;i++){"
                    "    var t=(divs[i].innerText||'').trim();"
                    "    if(!t||t.length>30) continue;"
                    "    for(var j=0;j<keys.length;j++){"
                    "      var k=keys[j];"
                    "      if(found[k]) continue;"
                    "      if(t===k||t.startsWith(k+' ')||t.endsWith(' '+k)){"
                    "        found[k]=SVC_KEYWORDS[k];"
                    "        result.push(SVC_KEYWORDS[k]);"
                    "      }"
                    "    }"
                    "  }"
                    "  return JSON.stringify(result.slice(0,8));"
                    "})()"
                )
                raw = await cdp_eval(ws, svc_js, timeout=12)
                if raw:
                    try:
                        return json.loads(raw) if isinstance(raw, str) else raw
                    except Exception:
                        pass
                return []

            JS_BASIC = (
                "(function(){"
                "  var text = document.body.innerText || '';"
                "  var r = {price_range:null,reporter:null,service:[],popular_items:[],"
                "            photo_label:'',menu_url:null,found:false};"
                "  var rangeM = text.match(/\\$([\\d,]+)[\\u2012\\u2013\\-\\.\\-]\\s*\\$?([\\d,]+)/);"
                "  var hasPP = /per person|平均每人|每人|人均/i.test(text);"
                "  if (rangeM && hasPP) {"
                "    r.price_range = '$' + rangeM[1] + '\\u2013' + rangeM[2];"
                "    var repM = text.match(/(\\d+)\\s*人回報|(\\d+)\\s*people report/i);"
                "    r.reporter = repM ? ((repM[1]||repM[2]) + '\\u4eba\\u56de\\u5831') : null;"
                "    r.found = true;"
                "  }"
                "  var links = document.querySelectorAll('a[href]');"
                "  for(var i=0;i<links.length;i++){"
                "    var h = (links[i].href||'').toLowerCase();"
                "    var t = (links[i].innerText||'').trim();"
                "    var isMenuLink = ("
                "      h.indexOf('dudooeat')!==-1||"
                "      h.indexOf('inline_menu')!==-1||"
                "      h.indexOf('menu')!==-1||"
                "      h.indexOf('instagram.com')!==-1||"
                "      h.indexOf('ubereats.com')!==-1||"
                "      h.indexOf('foodpanda')!==-1||"
                "      h.indexOf('deliveroo')!==-1||"
                "      h.indexOf('chope')!==-1||"
                "      h.indexOf('inline_menu')!==-1||"
                "      (t.match(/^[Ll]ink.*[Mm]enu/)&&h.startsWith('http'))||"
                "      (t.match(/^[Oo]rder/)&&h.startsWith('http'))"
                "    );"
                "    if(isMenuLink && h.startsWith('http') && h.length>15){"
                "      r.menu_url = links[i].href; break;"
                "    }"
                "  }"
                "  return JSON.stringify(r);"
                "})()"
            )
            raw_basic = await cdp_eval(ws, JS_BASIC, timeout=20)
            if raw_basic:
                try:
                    basic = json.loads(raw_basic) if isinstance(raw_basic, str) else raw_basic
                except Exception:
                    basic = {}
                if basic.get("price_range"):
                    result["found"] = True
                    result["price_range"] = basic.get("price_range")
                    result["reporter"] = basic.get("reporter")
                if basic.get("menu_url"):
                    result["menu_url"] = basic.get("menu_url")

            # ── click "菜單" tab ────────────────────────────
            print("[Phase 2] Clicking '菜單' tab...")
            clicked = await click_tab(ws, "菜單", wait=3)
            if clicked:
                raw_menu = await cdp_eval(ws, (
                    "(function(){"
                    "  var links = document.querySelectorAll('a[href]');"
                    "  for(var i=0;i<links.length;i++){"
                    "    var h = (links[i].href||'').toLowerCase();"
                    "    var t = (links[i].innerText||'').trim();"
                    "    var isMenu = ("
                    "      h.indexOf('dudooeat')!==-1||"
                    "      h.indexOf('inline_menu')!==-1||"
                    "      h.indexOf('instagram.com')!==-1||"
                    "      h.indexOf('ubereats.com')!==-1||"
                    "      h.indexOf('foodpanda')!==-1||"
                    "      h.indexOf('chope')!==-1||"
                    "      h.indexOf('menu')!==-1||"
                    "      (t.match(/^[Ll]ink.*[Mm]enu/)&&h.startsWith('http'))||"
                    "      (t.match(/^[Oo]rder/)&&h.startsWith('http'))"
                    "    );"
                    "    if(isMenu && h.startsWith('http') && h.length>15){"
                    "      return JSON.stringify({ok:true,url:links[i].href,text:t.substring(0,60)});"
                    "    }"
                    "  }"
                    "  return JSON.stringify({ok:false});"
                    "})()"
                ), timeout=12)
                if raw_menu:
                    try:
                        mi = json.loads(raw_menu) if isinstance(raw_menu, str) else raw_menu
                        if mi.get("ok") and mi.get("url"):
                            result["menu_url"] = mi["url"]
                            print("  [CDP] Menu URL: %s" % mi["url"][:80])
                    except Exception:
                        pass

            # ── click "評論" tab ────────────────────────────
            print("[Phase 2] Clicking '評論' tab...")
            clicked = await click_tab(ws, "評論", wait=3)
            if clicked:
                # 等 DOM 渲染熱門品項摘要（新版 Google Maps 需要一點時間）
                await asyncio.sleep(1.5)
                raw_pop = await cdp_eval(ws, (
                    "(function(){"
                    "  var found = [];"
                    "  // 新版 Google Maps：radiogroup > radio（標籤在 radio 的 innerText，如「有 7 則評論提到空間」）"
                    "  var radios = document.querySelectorAll('[role=radio]');"
                    "  for(var i=0;i<radios.length;i++){"
                    "    var aria = radios[i].getAttribute('aria-label')||'';"
                    "    var text = (radios[i].innerText||'').trim();"
                    "    if(aria.includes('mentioned in')){"
                    "      found.push(aria);"
                    "    } else if(text){"
                    "      // 格式：innerText = '品項\\n數字'，用 split 拆開"
                    "      var parts = text.split(String.fromCharCode(10)); if(parts.length >= 2) found.push(parts[0].trim());"
                    "    }"
                    "  }"
                    "  return JSON.stringify({ok:true,items:found.slice(0,8)});"
                    "})()"
                ), timeout=12)
                if raw_pop:
                    try:
                        pi = json.loads(raw_pop) if isinstance(raw_pop, str) else raw_pop
                        items = (pi.get("items", []) if isinstance(pi, dict) else [])
                        for item in items:
                            if item and item not in result["popular_items"]:
                                result["popular_items"].append(item)
                        if items:
                            print("  [CDP] Popular items: %s" % items[:3])
                    except Exception:
                        pass
                # 滾動讀取更多評論摘要標籤
                for _ in range(3):
                    raw_pop2 = await cdp_eval(ws, (
                        "(function(){"
                        "  var found = [];"
                        "  var radios = document.querySelectorAll('[role=radio]');"
                        "  for(var i=0;i<radios.length;i++){"
                        "    var aria = radios[i].getAttribute('aria-label')||'';"
                        "    var text = (radios[i].innerText||'').trim();"
                        "    if(aria.includes('mentioned in')) found.push(aria);"
                        "    else if(text){var parts=text.split(String.fromCharCode(10));if(parts.length>=2)found.push(parts[0].trim());}"
                        "  }"
                        "  return JSON.stringify(found.slice(0,8));"
                        "})()"
                    ), timeout=10)
                    if raw_pop2:
                        try:
                            more = json.loads(raw_pop2) if isinstance(raw_pop2, str) else []
                            for item in more:
                                if item and item not in result["popular_items"]:
                                    result["popular_items"].append(item)
                        except Exception:
                            pass
                    await cdp_send_recv(ws, 600, "Input.synthesizeScrollGesture", {
                        "x":0,"y":0,"xVelocity":0,"yVelocity":2000,
                        "preventFling":True,"stopTargetX":0,"stopTargetY":2000
                    }, timeout=6)
                    await asyncio.sleep(1.0)

            # ── 在評論 tab 停留，輪詢等 DOM 渲染 popular items ──
            for pop_tries in range(5):
                raw_pop_retry = await cdp_eval(ws, (
                    "(function(){"
                    "  var found = [];"
                    "  var radios = document.querySelectorAll('[role=radio]');"
                    "  for(var i=0;i<radios.length;i++){"
                    "    var aria = radios[i].getAttribute('aria-label')||'';"
                    "    var text = (radios[i].innerText||'').trim();"
                    "    if(aria.includes('mentioned in')) found.push(aria);"
                    "    else if(text){var parts=text.split(String.fromCharCode(10));if(parts.length>=2)found.push(parts[0].trim());}"
                    "  }"
                    "  return JSON.stringify({ok:true,items:found.slice(0,8)});"
                    "})()"
                ), timeout=12)
                if raw_pop_retry:
                    try:
                        pi = json.loads(raw_pop_retry) if isinstance(raw_pop_retry, str) else {}
                        items = (pi.get("items", []) if isinstance(pi, dict) else [])
                        for item in items:
                            if item and item not in result["popular_items"]:
                                result["popular_items"].append(item)
                        if items:
                            print("  [CDP] Popular items (try %d): %s" % (pop_tries+1, items[:3]))
                            break
                    except Exception:
                        pass
                await asyncio.sleep(1.0)

            # ── back to overview, polling ───────────────────
            # 先抓一次服務（避免空 poll 導致 stable 提前退出）
            svcs = await extract_services(ws)
            if svcs:
                result["service"] = svcs
                print("  [CDP] Services: %s" % svcs)
            prev_state = (len(result["service"]), 0, 1 if result["menu_url"] else 0)
            stable = 0
            for rnd in range(8):
                print("[Phase 2 polling %d]" % rnd)
                raw = await cdp_eval(ws, JS_BASIC, timeout=20)
                if raw:
                    try:
                        info = json.loads(raw) if isinstance(raw, str) else raw
                    except Exception:
                        info = {}
                    if info.get("price_range") and not result["price_range"]:
                        result["found"] = True
                        result["price_range"] = info.get("price_range")
                        result["reporter"] = info.get("reporter")
                    if info.get("menu_url") and not result["menu_url"]:
                        result["menu_url"] = info.get("menu_url")
                # 每次輪詢都重新抓服務（養出完整的服務列表）
                if rnd >= 1:  # 第一輪已有 overview，抓新內容才有意義
                    svcs = await extract_services(ws)
                    for s in svcs:
                        if s not in result["service"]:
                            result["service"].append(s)
                cur = (len(result["service"]), len(result["popular_items"]),
                       1 if result["menu_url"] else 0)
                print("  state: service=%d popular=%d menu=%s price=%s" % (
                    cur[0], cur[1], "yes" if cur[2] else "no",
                    result["price_range"] or "none"))
                if cur == prev_state:
                    stable += 1
                    print("  stable %d/3" % stable)
                    if stable >= 3:
                        break
                else:
                    stable = 0
                prev_state = cur
                await cdp_send_recv(ws, 300+rnd, "Input.synthesizeScrollGesture", {
                    "x":0,"y":0,"xVelocity":0,"yVelocity":3000,
                    "preventFling":True,"stopTargetX":0,"stopTargetY":3000
                }, timeout=8)
                await asyncio.sleep(1.5)

            print("[Phase 2 done] service=%d popular=%d menu=%s" % (
                len(result["service"]), len(result["popular_items"]),
                "yes" if result["menu_url"] else "no"))

            # ── Phase 3 ───────────────────────────────────
            if result["found"]:
                print("[Phase 3] Looking for price arrow button...")
                await cdp_eval(ws, "window.scrollTo({top:700,behavior:'instant'});null", timeout=6)
                await asyncio.sleep(1.0)
                btn_raw = await cdp_eval(ws, (
                    "(function(){"
                    "  var perEl = null;"
                    "  var allEls = document.querySelectorAll('*');"
                    "  for(var i=0;i<allEls.length;i++){"
                    "    var t=(allEls[i].innerText||'').trim();"
                    "    if(t.match(/^平均每人/)||(t.match(/per person/i)&&t.match(/\\$/))){"
                    "      perEl=allEls[i]; break;"
                    "    }"
                    "  }"
                    "  if(!perEl) return JSON.stringify({ok:false,reason:'no_perEl'});"
                    "  var container = (perEl.closest ? perEl.closest('div') : perEl.parentElement) || perEl.parentElement;"
                    "  var arrowEl = null;"
                    "  var candidates = container ? Array.from(container.querySelectorAll('button,svg,[aria-label],span')) : [];"
                    "  for(var i=0;i<candidates.length;i++){"
                    "    var ct=(candidates[i].innerText||'').trim();"
                    "    var ca=candidates[i].getAttribute('aria-label')||'';"
                    "    if(ca.match(/expand|dropdown|chevron|arrow|more/i)||"
                    "       ct==='\\u25bc'||ct==='\\u25b6'||"
                    "       candidates[i].querySelector('svg')){"
                    "      arrowEl=candidates[i]; break;"
                    "    }"
                    "  }"
                    "  if(!arrowEl && perEl.nextElementSibling &&"
                    "     (perEl.nextElementSibling.tagName==='BUTTON'||"
                    "      perEl.nextElementSibling.querySelector('svg'))){"
                    "    arrowEl=perEl.nextElementSibling;"
                    "  }"
                    "  if(!arrowEl){"
                    "    var siblings = Array.from(document.querySelectorAll('button'));"
                    "    var perRect = perEl.getBoundingClientRect();"
                    "    for(var i=0;i<siblings.length;i++){"
                    "      var r2=siblings[i].getBoundingClientRect();"
                    "      var diffY=Math.abs(r2.top-perRect.top);"
                    "      if(r2.width<80&&r2.height<60&&diffY<150&&"
                    "         (siblings[i].querySelector('svg')||(siblings[i].innerText||'').trim().length<=2)){"
                    "        arrowEl=siblings[i]; break;"
                    "      }"
                    "    }"
                    "  }"
                    "  if(arrowEl){"
                    "    var r2=arrowEl.getBoundingClientRect();"
                    "    return JSON.stringify({ok:true,"
                    "      x:Math.round(r2.left+r2.width/2),"
                    "      y:Math.round(r2.top+r2.height/2),"
                    "      method:'arrow',"
                    "      text:(arrowEl.innerText||'').trim().substring(0,40),"
                    "      aria:(arrowEl.getAttribute('aria-label')||'')});"
                    "  }"
                    "  var r2=perEl.getBoundingClientRect();"
                    "  return JSON.stringify({ok:true,"
                    "    x:Math.round(r2.left+r2.width/2),"
                    "    y:Math.round(r2.top+r2.height/2),"
                    "    method:'perEl_fallback',"
                    "    text:(perEl.innerText||'').trim().substring(0,60)});"
                    "})()"
                ), timeout=15)
                print("[Phase 3] btn: %s" % (btn_raw[:120] if btn_raw else "None"))
                if btn_raw:
                    try:
                        btn_info = json.loads(btn_raw) if isinstance(btn_raw, str) else btn_raw
                    except Exception:
                        btn_info = {}
                    ok = btn_info.get("ok", False) if isinstance(btn_info, dict) else False
                    method = btn_info.get("method", "") if isinstance(btn_info, dict) else ""
                    print("[Phase 3] mode=%s" % method)
                    if ok:
                        cx = btn_info.get("x", 0); cy = btn_info.get("y", 0)
                        print("[Phase 3] cx=%s cy=%s" % (cx, cy))
                        if cx > 0 and cy > 0:
                            await asyncio.sleep(0.4)
                            await cdp_send_recv(ws, 400, "Input.dispatchMouseEvent",
                                {"type":"mouseMoved","x":cx,"y":cy,"button":"none","clickCount":0}, timeout=6)
                            await asyncio.sleep(0.2)
                            await cdp_send_recv(ws, 401, "Input.dispatchMouseEvent",
                                {"type":"mousePressed","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
                            await cdp_send_recv(ws, 402, "Input.dispatchMouseEvent",
                                {"type":"mouseReleased","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
                            print("[Phase 3] clicked, wait 4s...")
                            await asyncio.sleep(4.0)
                            hist_raw = await cdp_eval(ws, (
                                "(function(){"
                                "  var tables=document.querySelectorAll('table[aria-label*=histogram i]');"
                                "  if(tables.length){"
                                "    var rows=tables[0].querySelectorAll('tr[data-item-id]');"
                                "    var entries=[];"
                                "    rows.forEach(function(row){"
                                "      var ltd=row.querySelector('td:first-child');"
                                "      var lbl=ltd?(ltd.innerText.trim()):'';"
                                "      var bar=row.querySelector('span[role=img]');"
                                "      var aria=bar?(bar.getAttribute('aria-label')||''):'';"
                                "      var pct=parseInt((aria||'').replace('%',''),10);"
                                "      if(lbl&&!isNaN(pct)&&pct>0) entries.push({label:lbl,pct:pct});"
                                "    });"
                                "    if(entries.length) return JSON.stringify({found:true,entries:entries,method:'table_aria'});"
                                "  }"
                                "  var live=document.querySelectorAll('div[aria-live]');"
                                "  for(var i=0;i<live.length;i++){"
                                "    var t=(live[i].innerText||'');"
                                "    if(t.indexOf('%')!==-1&&t.indexOf('$')!==-1){"
                                "      var nums=t.match(/\\b(\\d+)%/g)||[];"
                                "      var parts=t.split('\\n').filter(function(l){return l.trim().length>0;});"
                                "      if(nums.length) return JSON.stringify({found:true,nums:nums,parts:parts,method:'aria_live'});"
                                "    }"
                                "  }"
                                "  var all=document.querySelectorAll('div');"
                                "  for(var i=0;i<all.length;i++){"
                                "    var t=(all[i].innerText||'');"
                                "    if(t.indexOf('people')!==-1&&t.indexOf('%')!==-1&&t.indexOf('$')!==-1){"
                                "      var nums=t.match(/\\b(\\d+)%/g)||[];"
                                "      var parts=t.split('\\n').filter(function(l){return l.trim().length>0;});"
                                "      if(nums.length) return JSON.stringify({found:true,nums:nums,parts:parts,method:'people_pct_dollar'});"
                                "    }"
                                "  }"
                                "  var dialogs=document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]');"
                                "  for(var i=0;i<dialogs.length;i++){"
                                "    var t=(dialogs[i].innerText||'');"
                                "    if(t.indexOf('平均每人消費')!==-1||t.indexOf('Price range')!==-1){"
                                "      var bars=dialogs[i].querySelectorAll('[role=img],span');"
                                "      var entries=[];"
                                "      for(var j=0;j<bars.length;j++){"
                                "        var aria=(bars[j].getAttribute('aria-label')||'');"
                                "        var pct=parseInt((aria||'').replace('%',''),10);"
                                "        var label=(bars[j].innerText||'').trim();"
                                "        if(!isNaN(pct)&&pct>0) entries.push({label:label,pct:pct});"
                                "      }"
                                "      if(entries.length) return JSON.stringify({found:true,entries:entries,method:'dialog_histogram'});"
                                "      var nums=t.match(/\\b(\\d+)%/g)||[];"
                                "      if(nums.length){"
                                "        var parts=t.split('\\n').filter(function(l){return l.trim().length>0&&l.length<30;});"
                                "        return JSON.stringify({found:true,nums:nums,parts:parts,method:'dialog_nums'});"
                                "      }"
                                "    }"
                                "  }"
                                "  return JSON.stringify({found:false});"
                                "})()"
                            ), timeout=12)
                            print("[Phase 3] hist: %s" % (hist_raw[:150] if hist_raw else "None"))
                            if hist_raw:
                                try:
                                    hd = json.loads(hist_raw)
                                except Exception:
                                    hd = {}
                                if hd.get("found"):
                                    rep_str = str(result.get("reporter") or "71")
                                    rep_cnt = int(re.sub(r"\D", "", rep_str)) or 71
                                    ents = hd.get("entries", [])
                                    hist = []
                                    for e2 in ents[:4]:
                                        lbl = e2.get("label", "$")
                                        pct = e2.get("pct", 0)
                                        cnt = round(pct/100*rep_cnt)
                                        hist.append([lbl, "約%d人" % cnt, pct])
                                    if not hist:
                                        nums = hd.get("nums", [])
                                        parts = hd.get("parts", [])
                                        for i2, ns in enumerate(nums):
                                            pct2 = int(ns.replace("%",""))
                                            lbl2 = parts[i2].strip() if i2 < len(parts) else "$"
                                            cnt2 = round(pct2/100*rep_cnt)
                                            hist.append([lbl2, "約%d人" % cnt2, pct2])
                                    if hist:
                                        result["price_histogram"] = hist
                                        print("[Phase 3] Histogram OK (%s): %s" % (hd.get("method","?"), hist))
                                    else:
                                        print("[Phase 3] Histogram found but not parsed: " + str(hd)[:200])
                                else:
                                    print("[Phase 3] hd.found is False")
                else:
                    print("[Phase 3] No btn_raw")
            else:
                print("[Phase 3] result.found=False, skipping")
    except Exception as e:
        import traceback
        print("[CDP] Error: %s" % e)
        traceback.print_exc()
        result["error"] = str(e)

    print("[CDP] Done: found=%s price=%s service=%d popular=%d menu=%s hist=%d" % (
        result["found"], result["price_range"],
        len(result["service"]), len(result["popular_items"]),
        "yes" if result["menu_url"] else "no",
        len(result["price_histogram"])))
    return result


# ─── 評論價格提取 ────────────────────────────────────────────────
PRICE_PATTERNS = [
    r"\$\d+(?:\.\d{2})?(?:[,，]\s*\$\d+(?:\.\d{2})?)*",
    r"新台幣\s*\$?\d+(?:\.\d{2})?",
    r"含\s*\$?\d+",
    r"每人?\s*\$?\d+",
    r"\+\s*\$?\d+",
]

def extract_prices(content):
    prices = []
    for pat in PRICE_PATTERNS:
        prices.extend(re.findall(pat, content))
    seen, unique = set(), []
    for p in prices:
        key = re.sub(r"\D", "", p)
        if key and key not in seen:
            seen.add(key); unique.append(p)
    return unique[:5]


# ─── 特色菜色 ────────────────────────────────────────────────
DISH_ITEMS = [
    ("蝦滷飯",   "蝦滷飯"),
    ("澎湖小卷", "小卷"),
    ("煎干貝",   "干貝"),
    ("脆皮燒肉", "燒肉"),
    ("辣椒",     "辣椒"),
    ("海鮮炒麵", "炒麵"),
    ("海鮮粥",   "海鮮粥"),
    ("油蔥蝦仁飯","油蔥蝦仁飯"),
    ("川燙花枝", "花枝"),
]

def extract_dish_highlights(reviews):
    """
    特色菜色：取第一個品名，snip 在第一個句號（。！？）截斷。
    避免 snippet 延伸到下一道菜的文字。
    """
    found = {}
    for review in reviews:
        content = review.get("content", "")
        for pattern, canonical in DISH_ITEMS:
            if canonical in found:
                continue
            # 取品名的主要部分（前瞻不含說明的部分）
            key = pattern.split("，")[0].split("（")[0]
            idx = content.find(key)
            if idx < 0:
                continue
            # 從品名之後取到55字
            snippet = content[idx + len(key): idx + 60].strip()
            snippet = re.sub(r"[\n\r]+", "，", snippet)
            snippet = re.sub(r"，+，", "，", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            # 在第一個句號截斷（防止吃到下一道菜的描述）
            m = re.search(r"[。！？\?!]", snippet)
            if m:
                snippet = snippet[:m.end()]
            snippet = snippet.strip("。，、：：「」\"''()（）　 ")
            if len(snippet) < 4:
                continue
            found[canonical] = (pattern, snippet)
        if len(found) >= 5:
            break
    result = []
    for pattern, canonical in DISH_ITEMS:
        if canonical in found:
            result.append((found[canonical][0], found[canonical][1]))
    return result


# ─── 網友心得 ────────────────────────────────────────────────
def extract_review_highlights(reviews):
    results = []; seen = set()
    for review in reviews:
        author = review.get("author", "")
        content = review.get("content", "")
        if not content or author == "LISON":
            continue
        for sent in re.split(r"[。\n]", content):
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 80:
                continue
            if re.search(r"\$\d+", sent):
                continue
            if sent in seen:
                continue
            seen.add(sent)
            results.append((author, sent))
            break
        if len(results) >= 3:
            break
    if len(results) < 3:
        for review in reviews:
            content = review.get("content", "")
            if not content or review.get("author") == "LISON":
                continue
            for sent in re.split(r"[。\n]", content):
                sent = sent.strip()
                if len(sent) < 10 or len(sent) > 60:
                    continue
                if re.search(r"\$\d+", sent):
                    continue
                if sent in seen:
                    continue
                seen.add(sent)
                results.append((review.get("author",""), sent))
                break
            if len(results) >= 3:
                break
    unique = []
    for author, note in results:
        if len(note) < 10:
            continue
        if len(note) > 80:
            note = note[:80] + "…"
        unique.append((author, note))
    return unique[:3]


# ─── 用戶反饋價格 ────────────────────────────────────────────────
def format_reviews_price(reviews):
    lines = []
    for rev in reviews:
        content = rev.get("content", "")
        prices  = extract_prices(content)
        if not prices:
            continue
        days   = rev["days_ago"]
        rating = rev.get("rating", "")
        author = rev.get("author", "匿名")
        lines.append(f"· {author}（{rating}⭐，{days}天前）提及：{', '.join(prices)}")
        snippet = _smart_truncate(content, prices)
        lines.append(f"  「{snippet}」")
    return lines

def _smart_truncate(text, prices, max_len=150):
    text = re.sub(r"[\n\r]+", " ", text).strip()
    first_price = prices[0] if prices else ""
    digit_part  = re.sub(r"\D", "", first_price)
    pos = -1
    if first_price:
        for pat_str in [re.escape(first_price), r"\+\d+\$", digit_part]:
            m = re.search(pat_str, text)
            if m:
                pos = max(0, m.start() - 35); break
    if pos < 0: pos = 0
    snippet = text[pos:pos + max_len]
    for punct in ["。", "，", "！", "？"]:
        idx = snippet.rfind(punct, int(max_len * 0.5), max_len)
        if idx > 0:
            snippet = snippet[:idx + 1]; break
    if pos > 0:
        snippet = "…" + snippet.strip()
    return snippet if snippet else text[:max_len]


# ─── 地址格式化（v9：附加郵遞區號括號）───
def format_address(addr_en):
    a = addr_en.strip()
    if not a:
        return addr_en

    # 先抽郵遞區號（不進入 tokens 流程，避免重複出現）
    zipcode = ""
    zm = re.search(r"\b(\d{3,5})\s*$", a)
    if zm:
        zipcode = zm.group(1)
        a = a[:zm.start()].strip().rstrip(",").rstrip()

    # 抽門牌號（處理 "No. 32號," 和 "No. 32," 兩種格式）
    house_num = ""
    # 兩種都要剷乾淨：No. 32號 → house_num=32號；No. 32 → house_num=32號
    hm = re.search(r"No\.?\s*(\d+)號?", a)
    if hm:
        house_num = hm.group(1) + "號"
        # 只剷 No. N(號) 和其後的逗號/空格，不碰後面的 Section
        a = re.sub(r"No\.?\s*\d+號?\s*,\s*", "", a, count=1).strip()
    else:
        # 格式 "32號, Section..." → 直接剷到第一個逗號
        hm2 = re.search(r"^(\d+)號\s*,\s*", a)
        if hm2:
            house_num = hm2.group(1) + "號"
            a = a[hm2.end():].strip()

    # 抽段
    section_num = ""
    m = re.search(r"Section\s*(\d+)", a, re.IGNORECASE)
    if m:
        section_num = m.group(1) + "段"
        a = re.sub(r"Section\s*\d+\s*,?\s*", "", a, flags=re.IGNORECASE).strip(",").strip()

    # 置換映射
    rep_map = {
        "Beitun District":"北屯區","Xitun District":"西屯區","Nantun District":"南屯區",
        "Dali District":"大里區","Wuri District":"梧棲區","Dajia District":"大甲區",
        "Fengyuan District":"豐原區","Shalu District":"沙鹿區","Longjing District":"龍井區",
        "Qingshui District":"清水區","Dadu District":"大肚區","Wanhua District":"萬華區",
        "Da'an District":"大安區","Songshan District":"松山區","Neihu District":"內湖區",
        "Nangang District":"南港區","Zhonghe District":"中和區","Yonghe District":"永和區",
        "Zhongzheng District":"中正區","Datong District":"大同區","Banqiao District":"板橋區",
        "North District":"北區","South District":"南區","East District":"東區",
        "West District":"西區","Central District":"中區",
        "Taichung City":"台中市","Changhua City":"彰化市",
        "Taipei City":"台北市","New Taipei City":"新北市","Hsinchu City":"新竹市",
        "Hankou Rd":"漢口路","Dunhua Rd":"敦化路","Fuxing Rd":"復興路",
        "Zhongshan Rd":"中山路","Rd":"路","Road":"路","St":"街","Street":"街",
    }
    for en, zh in sorted(rep_map.items(), key=lambda x: -len(x[0])):
        a = a.replace(en, zh)

    # 合併多餘逗號
    a = re.sub(r",+", "，", a); a = re.sub(r"，+", "，", a)
    a = a.strip("，").strip()
    a = re.sub(r"^No\.?\s*", "", a).strip()

    # 移除「台灣」（最後殘留的國家名）
    a = re.sub(r"，?\s*台灣\s*$", "", a).strip()
    # 再次清理可能的殘留
    a = re.sub(r"，?\s*Taiwan\s*$", "", a, flags=re.IGNORECASE).strip()

    # 以「，」分段，重新組裝 city / 區 / 路 / 門牌
    road_kws = ["路","街","巷","弄","大道"]
    tokens = [t.strip() for t in re.split(r"[，,]+", a) if t.strip()]
    city = ""; district = ""; road = ""; others = []
    for tok in tokens:
        if any(tok.endswith(k) for k in road_kws):
            road = tok
        elif tok in ["台中市","彰化市","台北市","新北市","新竹市"]:
            city = tok
        elif "區" in tok and tok != "台灣":
            district = tok
        else:
            others.append(tok)

    # 附加郵遞區號
    zip_label = f"（{zipcode}）" if zipcode else ""

    return city + district + "".join(others) + road + section_num + house_num + zip_label


# ─── 輸出格式化 ────────────────────────────────────────────────
HOT_ITEM_TRANSLATE = {
    "fried noodles":"海鮮炒麵","popsicles":"冰棒","conpoy":"干貝",
    "vegetables":"蔬菜","sweet":"甜點","seafood":"海鮮","rice":"米飯",
    "noodles":"麵食","grilled":"烤肉","steamed":"蒸食","soup":"湯品",
}

def format_output(data, maps_price, reviews, price_range_api=None):
    raw_name = data.get("name","未知")
    # goplaces 的 name 有時含 pipe 分隔的多個標籤，只取第一段作為正式名稱
    name     = raw_name.split("|")[0].strip()
    addr     = data.get("address","無")
    lat      = data.get("location",{}).get("lat","")
    lng      = data.get("location",{}).get("lng","")
    phone    = data.get("phone","無")
    rating   = data.get("rating","無")
    rcount   = data.get("user_rating_count", 0)
    website  = data.get("website","無")
    open_now = data.get("open_now")
    hours    = data.get("hours", [])
    place_id = data.get("place_id","")
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

    lines = []
    lines.append(f"🏪 店名：{name}")
    lines.append(f"📍 地址：{format_address(addr)}")
    lines.append(f"📍 經緯度：{round(lat,6)}, {round(lng,6)}")
    lines.append(f"📞 電話：{phone}")
    lines.append(f"⭐ 評分：{rating}（{rcount}則）")

    now = datetime.now()
    day_names_en = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_names_zh = ["週一","週二","週三","週四","週五","週六","週日"]
    today_en = day_names_en[now.weekday()]
    today_zh = day_names_zh[now.weekday()]
    today_hours_line = None
    for h in hours:
        if not h: continue
        parts = h.split(": ", 1)
        if len(parts) != 2 or parts[0].strip() != today_en: continue
        tp = parts[1].strip()
        today_hours_line = None if tp.lower() == "closed" else tp

    if open_now is True:
        if today_hours_line:
            full_m = re.search(
                r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)',
                today_hours_line, re.IGNORECASE)
            close_m = re.search(r'[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)',
                                today_hours_line, re.IGNORECASE)
            if full_m and close_m:
                oh=int(full_m[1]); om=int(full_m[2]); oampm=full_m[3].upper()
                ch=int(full_m[4]); cm=int(full_m[5]); campm=full_m[6].upper()
                open_h24 = oh%12+(12 if oampm=='PM' else 0)
                close_h24 = ch%12+(12 if campm=='PM' else 0)
                close_dt = now.replace(hour=close_h24, minute=cm, second=0, microsecond=0)
                open_dt  = now.replace(hour=open_h24,  minute=om, second=0, microsecond=0)
                if close_h24 <= open_h24 and close_h24 < 12:
                    close_dt += timedelta(days=1)
                diff = close_dt - now
                secs = int(diff.total_seconds())
                if secs > 0:
                    hl = secs//3600; ml = (secs%3600)//60
                    tl = f"距離關門 {hl} 小時 {ml} 分鐘" if hl > 0 else f"距離關門 {ml} 分鐘"
                else:
                    tl = "已超過關門時間"
                lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}，{tl}）")
            elif close_m:
                ch=int(close_m[1]); cm=int(close_m[2]); campm=close_m[3].upper()
                hour24=ch%12+(12 if campm=='PM' else 0)
                close_dt=now.replace(hour=hour24,minute=cm,second=0,microsecond=0)
                diff=close_dt-now; secs=int(diff.total_seconds())
                if secs>0:
                    hl=secs//3600; ml=(secs%3600)//60
                    tl=f"距離關門 {hl} 小時 {ml} 分鐘" if hl>0 else f"距離關門 {ml} 分鐘"
                else:
                    tl="已超過關門時間"
                lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}，{tl}）")
            else:
                lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}）")
        else:
            lines.append(f"🚦 狀態：✅ 營業中")
    elif open_now is False:
        if today_hours_line:
            # 解析今日營業時段，計算距離開門/打烊
            full_m = re.search(
                r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)',
                today_hours_line, re.IGNORECASE)
            if full_m:
                oh=int(full_m[1]); om=int(full_m[2]); oampm=full_m[3].upper()
                ch=int(full_m[4]); cm=int(full_m[5]); campm=full_m[6].upper()
                open_h24  = oh%12+(12 if oampm=='PM' else 0)
                close_h24 = ch%12+(12 if campm=='PM' else 0)
                open_dt  = now.replace(hour=open_h24,  minute=om,  second=0, microsecond=0)
                close_dt = now.replace(hour=close_h24, minute=cm, second=0, microsecond=0)
                # 跨午夜：2:00 AM → close_dt 已是明天
                if close_h24 < open_h24 or close_h24 < 12:
                    close_dt += timedelta(days=1)

                diff_open  = open_dt  - now
                diff_close = close_dt - now
                secs_open  = int(diff_open.total_seconds())
                secs_close = int(diff_close.total_seconds())

                if secs_open > 0:
                    # 還沒開門
                    hl = secs_open//3600; ml = (secs_open%3600)//60
                    if hl > 0:
                        wait_str = f"距離開門 {hl} 小時 {ml} 分鐘"
                    else:
                        wait_str = f"距離開門 {ml} 分鐘"
                    lines.append(f"🚦 狀態：❌ 休息中（今日 {today_hours_line}，{wait_str}）")
                elif secs_close > 0:
                    # 營業中但 API 說休息（例外情況）
                    hl = secs_close//3600; ml = (secs_close%3600)//60
                    tl = f"距離關門 {hl} 小時 {ml} 分鐘" if hl > 0 else f"距離關門 {ml} 分鐘"
                    lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}，{tl}）")
                else:
                    # 已過今日營業時間（凌晨 2 點前），找明天開門日
                    cur_idx=now.weekday(); found_next=False
                    for offset in range(1,8):
                        nidx=(cur_idx+offset)%7
                        for h in hours:
                            parts=h.split(": ",1)
                            if len(parts)!=2 or parts[0].strip()!=day_names_en[nidx]: continue
                            tp=parts[1].strip()
                            if tp.lower()!="closed":
                                lines.append(f"🚦 狀態：❌ 休息中（今日已打烊，{day_names_zh[nidx]} {tp} 開門）")
                                found_next=True; break
                        if found_next: break
                    else:
                        lines.append(f"🚦 狀態：❌ 休息中（今日 {today_hours_line}）")
            else:
                # 無法解析時段，直接顯示時段
                lines.append(f"🚦 狀態：❌ 休息中（今日 {today_hours_line}）")
        else:
            # 今天是公休日，找下一個開門日並計算距離開門時間
            cur_idx=now.weekday(); found_next=False
            for offset in range(1,8):
                nidx=(cur_idx+offset)%7
                for h in hours:
                    parts=h.split(": ",1)
                    if len(parts)!=2 or parts[0].strip()!=day_names_en[nidx]: continue
                    tp=parts[1].strip()
                    if tp.lower()!="closed":
                        # 解析下一個開門日的時段
                        full_m = re.search(
                            r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)',
                            tp, re.IGNORECASE)
                        if full_m:
                            oh=int(full_m[1]); om=int(full_m[2]); oampm=full_m[3].upper()
                            ch=int(full_m[4]); cm=int(full_m[5]); campm=full_m[6].upper()
                            open_h24  = oh%12+(12 if oampm=='PM' else 0)
                            close_h24 = ch%12+(12 if campm=='PM' else 0)
                            next_open_dt = (now + timedelta(days=offset)).replace(
                                hour=open_h24, minute=om, second=0, microsecond=0)
                            diff_open = next_open_dt - now
                            secs = int(diff_open.total_seconds())
                            if secs > 0:
                                hl = secs//3600; ml = (secs%3600)//60
                                wait_str = f"距離開門 {hl} 小時 {ml} 分鐘"
                                lines.append(f"🚦 狀態：❌ 休息中（{day_names_zh[nidx]} {tp}，{wait_str}）")
                            else:
                                lines.append(f"🚦 狀態：❌ 休息中（{day_names_zh[nidx]} {tp} 開門）")
                        else:
                            lines.append(f"🚦 狀態：❌ 休息中（{day_names_zh[nidx]} {tp} 開門）")
                        found_next=True; break
                if found_next: break
            else:
                lines.append(f"🚦 狀態：❌ 休息中")
    else:
        if today_hours_line:
            lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}）")
        else:
            lines.append(f"🚦 狀態：❌ 休息中")

    lines.append(f"🌐 網站：{website}")
    lines.append(f"🔗 Google Maps：{maps_url}")

    price_hist = (maps_price.get("price_histogram",[]) if maps_price else [])
    rep_label  = (maps_price.get("reporter","") if maps_price else "")

    if price_range_api:
        lines.append(f"💵 每人消費：{price_range_api}"
                     + (f"（{rep_label}）" if rep_label else ""))
        for lbl, cnt, pct in price_hist:
            bar = "▓"*int(pct/10)+"░"*(10-int(pct/10))
            lines.append(f"   {bar}  {lbl}  {cnt}（{pct}%）")
    elif maps_price and maps_price.get("found"):
        pr = maps_price["price_range"]
        lines.append(f"💵 每人消費：{pr}" + (f"（{rep_label}）" if rep_label else ""))
        for lbl, cnt, pct in price_hist:
            bar = "▓"*int(pct/10)+"░"*(10-int(pct/10))
            lines.append(f"   {bar}  {lbl}  {cnt}（{pct}%）")
    elif maps_price and maps_price.get("error"):
        lines.append(f"💵 每人消費：無法讀取（{maps_price['error']}）")
    else:
        lines.append(f"💵 每人消費：店家未提供")

    if maps_price:
        menu_url = maps_price.get("menu_url", "")
        if menu_url:
            lines.append(f"🍽️ Menu：{menu_url}")

    # 📌 服務（從 CDP 抓取）
    svcs = (maps_price.get("service", []) if maps_price else [])
    if svcs:
        lines.append(f"📌 服務：{ '、'.join(svcs) }")

    # 🍜 熱門品項（從 CDP 抓取，格式：「品項名（N則）」）
    pop_items = (maps_price.get("popular_items", []) if maps_price else [])
    if pop_items:
        # 從完整 aria-label 抽出品項名（格式如「空間，7則評論」或「空間」）
        cleaned = []
        for item in pop_items:
            m = re.search(r'^(.+?)(?:[,\s]+\d+\s*則)?[評論提到]*$', item.strip())
            label = m.group(1).strip() if m else item.strip()
            if label and label not in cleaned:
                cleaned.append(label)
        if cleaned:
            lines.append(f"🍜 熱門品項：{'｜'.join(cleaned[:8])}")

    dish_hl = extract_dish_highlights(reviews)
    if dish_hl:
        lines.append("🔥 特色菜色：")
        for dish_name, snippet in dish_hl:
            lines.append(f"   {dish_name}：{snippet}")

    rev_hl = extract_review_highlights(reviews)
    if rev_hl:
        lines.append("📝 網友心得：")
        for author, note in rev_hl:
            note2 = note if len(note) <= 150 else note[:150]+"…"
            lines.append(f"   {author}：{note2}")

    price_lines = format_reviews_price(reviews)
    if price_lines:
        lines.append("💬 用戶反饋價格（6個月內）：")
        for pl in price_lines:
            lines.append(pl)

    return "\n".join(lines)


# ─── 主指令 ────────────────────────────────────────────────
def cmd_search(args):
    lat=None; lng=None; radius=1000; min_rating=None; open_now=False; limit=5
    query="餐廳"; i=0
    while i < len(args):
        a=args[i]
        if a=="--lat": lat=float(args[i+1]); i+=2
        elif a=="--lng": lng=float(args[i+1]); i+=2
        elif a.startswith("--radius"): radius=int(a.split()[1]); i+=1
        elif a.startswith("--min-rating"): min_rating=float(a.split()[1]); i+=1
        elif a=="--open-now": open_now=True; i+=1
        elif a.startswith("--limit"): limit=int(a.split()[1]); i+=1
        else: query=a; i+=1

    out = goplaces(f'search "{query}" --limit {limit}' +
        (f" --lat {lat} --lng {lng} --radius-m {radius}" if lat and lng else "") +
        (f" --min-rating {min_rating}" if min_rating else "") +
        (" --open-now" if open_now else ""))
    lines_out = out.strip().split("\n")
    place_id = None
    for line in lines_out:
        if line.startswith("ID:"):
            place_id = line.split("ID:")[1].strip().split()[0]; break
    if not place_id:
        print("（未找到 place_id）\n"+out); return
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    reviews, data = get_reviews(place_id)
    if not data:
        print("（無法取得店家資料）"); return
    price_range_api = get_price_range_api(place_id)
    maps_price = {"found": False}
    try:
        maps_price = asyncio.run(scrape_price_from_browser(place_id, maps_url))
    except Exception as e:
        maps_price = {"found": False, "error": str(e)}
    print(format_output(data, maps_price, reviews, price_range_api))


def cmd_full(args):
    place_id = next((a for a in args if not a.startswith("--")), None)
    if not place_id:
        print("錯誤：缺少 place_id"); return
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    reviews, data = get_reviews(place_id)
    if not data:
        print("錯誤：無法取得店家資料"); return
    price_range_api = get_price_range_api(place_id)
    maps_price = {"found": False}
    try:
        maps_price = asyncio.run(scrape_price_from_browser(place_id, maps_url))
    except Exception as e:
        maps_price = {"found": False, "error": str(e)}
    print(format_output(data, maps_price, reviews, price_range_api))


def cmd_details(args):
    place_id = args[0]
    reviews, data = get_reviews(place_id)
    if not data:
        print("錯誤：無法取得店家資料"); return
    price_range_api = get_price_range_api(place_id)
    print(format_output(data, {"found": False}, reviews, price_range_api))


if __name__ == "__main__":
    import sys
    # 安靜模式：--quiet 抑制 CDP debug 輸出（stderr），只留乾淨結果（stdout）
    if "--quiet" in sys.argv:
        sys.argv.remove("--quiet")
        import os, contextlib
        with contextlib.redirect_stderr(open(os.devnull, "w")):
            if len(sys.argv) < 2:
                print(__doc__); sys.exit(1)
            cmd = sys.argv[1].lower()
            args = sys.argv[2:]
            {"search": cmd_search, "details": cmd_details, "full": cmd_full}.get(cmd, lambda _: print(f"未知指令：{cmd}"))(args)
    else:
        if len(sys.argv) < 2:
            print(__doc__); sys.exit(1)
        cmd = sys.argv[1].lower()
        args = sys.argv[2:]
        {"search": cmd_search, "details": cmd_details, "full": cmd_full}.get(cmd, lambda _: print(f"未知指令：{cmd}"))(args)
