#!/usr/bin/env python3
"""
Google Places 店家查詢工具 v10.1（穩定強化版）
修正重點：
1. 修正 CDP 流程：將「概要頁面輪詢 (Stability Polling)」移至最前方，避免在切換分頁後於錯誤頁面輪詢導致卡死。
2. 強化元素定位：click_tab 改用 .includes()，提高在不同 Google Maps 版本中的命中率。
3. 增加導航檢查：在執行分頁操作前，確保頁面已完全加載且無驗證碼攔截。
4. 移除冗餘的後置輪詢，將所有概要數據抓取集中在起始階段。
"""
import subprocess, json, sys, os, re, asyncio, urllib.request, urllib.parse, time, websockets, shutil
from datetime import datetime, timezone, timedelta

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

def get_reviews(place_id, months=None):
    data = get_details_json(place_id)
    if not data:
        return [], data
    cutoff = None
    if months is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    filtered = []
    for review in data.get("reviews", []):
        pub_str = review.get("publish_time", "")
        if not pub_str:
            continue
        try:
            pub_time = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            continue
        if cutoff and pub_time < cutoff:
            continue
        orig = review.get("original_text", {}).get("text", "")
        translated = review.get("text", {}).get("text", "")
        content = orig or translated
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

def get_localized_name_addr(place_id):
    url = ("https://maps.googleapis.com/maps/api/place/details/json"
           f"?place_id={place_id}&fields=name,formatted_address&language=zh-TW"
           f"&key={GOOGLE_PLACES_API_KEY}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result = data.get("result", {})
        return result.get("name"), result.get("formatted_address", "")
    except Exception:
        return None, None

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
    for attempt in range(2):
        try:
            r = await cdp_send_recv(ws, 99, "Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            }, timeout=timeout)
            if r is None:
                await asyncio.sleep(0.5)
                continue
            result_obj = r.get("result", {})
            res_result = result_obj.get("result", {})
            val = res_result.get("value", None)
            if val is not None:
                return val
            unserialized = res_result.get("unserializedValue", None)
            if unserialized is not None:
                return str(unserialized)
            desc = res_result.get("description", "")
            if desc:
                return desc
            return ""
        except Exception:
            if attempt < 1:
                await asyncio.sleep(0.5)
    return ""

# ─── CDP 爬蟲 ────────────────────────────────────────────────
async def scrape_price_from_browser(place_id, maps_url=None):
    maps_url = maps_url or f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    print(f"[CDP] place={place_id[:20]}")
    result = {
        "found": False, "price_range": None, "reporter": None,
        "price_histogram": [], "service": [], "popular_items": [],
        "photo_label": "", "menu_url": None, "food_categories": [],
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
        import socket
        def port_used(port):
            s = socket.socket(); s.settimeout(1)
            try:
                s.connect((HOST, port)); s.close(); return True
            except Exception:
                return False

        CDP_PROFILE = "/tmp/openclaw-chrome-cdp-warmup"
        def _copy_login_profile():
            try:
                shutil.rmtree(CDP_PROFILE, ignore_errors=True)
                os.makedirs(CDP_PROFILE, exist_ok=True)
                copied = False
                for browser_name, base_path in [
                    ("Chrome", os.path.expanduser("~/Library/Application Support/Google/Chrome")),
                    ("Edge",   os.path.expanduser("~/Library/Application Support/Microsoft Edge")),
                ]:
                    default_path = os.path.join(base_path, "Default")
                    if os.path.isdir(default_path):
                        shutil.copytree(default_path, os.path.join(CDP_PROFILE, "Default"), dirs_exist_ok=True)
                        for item in ["Extensions", "Extension State", "Local App Settings", "Local Storage", "Session Storage", "Sync Data"]:
                            src = os.path.join(base_path, item)
                            dst = os.path.join(CDP_PROFILE, item)
                            if os.path.isdir(src):
                                shutil.copytree(src, dst, dirs_exist_ok=True)
                        copied = True
                        break
                return copied
            except Exception:
                return False

        _copy_login_profile()
        if port_used(PORT):
            os.system("lsof -ti :%d 2>/dev/null | xargs kill -9 2>/dev/null; sleep 2" % PORT)

        executable = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        try:
            subprocess.Popen([executable, "--headless=no", "--no-default-browser-check", "--remote-debugging-port=%d" % PORT, "--user-data-dir=%s" % CDP_PROFILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            try:
                subprocess.Popen(["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "--headless=no", "--no-default-browser-check", "--remote-debugging-port=%d" % PORT, "--user-data-dir=%s" % CDP_PROFILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                return False

        for attempt in range(20):
            time.sleep(1)
            if cdp_reachable():
                return True
        return False

    async def ws_ping(ws_url_str, timeout=5.0):
        try:
            async with asyncio.timeout(timeout):
                async with websockets.connect(ws_url_str, open_timeout=timeout) as ws_ping:
                    r = await cdp_send_recv(ws_ping, 999, "Runtime.evaluate", {"expression": "1+1", "returnByValue": True}, timeout=timeout)
                    if r and r.get("result", {}).get("result", {}).get("value") == 2:
                        return True
        except Exception:
            pass
        return False

    async def get_ws_url(tab_list, prefer_maps=True):
        ordered = []
        for t in tab_list:
            if t.get("type") != "page": continue
            url = t.get("url", "")
            if not url.startswith("http"): continue
            if prefer_maps and "google.com/maps" in url: ordered.insert(0, t)
            else: ordered.append(t)
        for tab in ordered:
            wurl = tab.get("webSocketDebuggerUrl", "")
            if wurl and await ws_ping(wurl):
                return wurl, tab
        for tab in tab_list:
            wurl = tab.get("webSocketDebuggerUrl", "")
            if wurl and await ws_ping(wurl):
                try:
                    async with websockets.connect(wurl, open_timeout=10) as host_ws:
                        r = await cdp_send_recv(host_ws, 777, "Target.createTarget", {"url": maps_url}, timeout=15)
                    if r and r.get("result", {}).get("targetId"):
                        new_id = r["result"]["targetId"]
                        new_url = f"ws://{HOST}:{PORT}/devtools/page/{new_id}"
                        await asyncio.sleep(1)
                        if await ws_ping(new_url):
                            return new_url, {"webSocketDebuggerUrl": new_url, "url": maps_url}
                except Exception:
                    continue
        return None, None

    async def click_tab(ws, label, wait=1):
        js = (
            "(function() {"
            "  var els = document.querySelectorAll('button,div[role=tab],a');"
            "  for(var i=0;i<els.length;i++){"
            "    var t=(els[i].innerText||'').trim();"
            "    if(t.includes('%s')){"
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
            "})()" % (label)
        )
        raw = await cdp_eval(ws, js, timeout=10)
        if not raw: return False
        try:
            info = json.loads(raw) if isinstance(raw, str) else raw
            if not (info.get("ok") if isinstance(info, dict) else False): return False
            cx, cy = info.get("x", 0), info.get("y", 0)
            if cx <= 0 or cy <= 0: return False
            await cdp_send_recv(ws, 500, "Input.dispatchMouseEvent", {"type":"mousePressed","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
            await cdp_send_recv(ws, 501, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
            await asyncio.sleep(wait)
            return True
        except Exception:
            return False

    if not start_edge_background():
        return {"found": False, "error": "browser not started"}
    tabs = get_all_tabs(max_wait=30)
    if not tabs:
        return {"found": False, "error": "no tabs"}
    ws_url, _ = await get_ws_url(tabs, prefer_maps=True)
    if not ws_url:
        return {"found": False, "error": "no WS URL"}

    try:
        async with websockets.connect(ws_url) as ws:
            print("[CDP] WS connected")
            current_url = await cdp_eval(ws, "window.location.href")
            if "google.com/maps" not in (current_url or ""):
                await cdp_send_recv(ws, 5, "Page.navigate", {"url": maps_url}, timeout=30)
                for tick in range(20):
                    await asyncio.sleep(1)
                    body = await cdp_eval(ws, "(document.body||{}).innerText||''")
                    if len(body or "") > 200 and "google.com/legal" not in (body or "").lower():
                        break
            await asyncio.sleep(1)

            # --- Phase 1: Overview Polling (Moved to Front) ---
            async def extract_services(ws):
                svc_js = (
                    "(function(){"
                    "  var SVC_KEYWORDS = {'內用':'內用','外帶':'外帶','外送':'外送','Delivery':'外送','寵物友善':'寵物友善','pet':'寵物友善','寵物':'寵物友善','預約':'預約','訂位':'訂位','素食':'素食','vegan':'素食','洗手間':'洗手間','廁所':'廁所','WiFi':'WiFi','wifi':'WiFi','吸菸':'吸菸','吸烟':'吸菸','無菸':'無菸','cash':'現金','信用卡':'信用卡','停車':'停車','parking':'停車'};"
                    "  var result = []; var found = {}; var divs = document.querySelectorAll('div,span,button');"
                    "  for(var i=0;i<divs.length;i++){"
                    "    var t=(divs[i].innerText||'').trim(); if(!t||t.length>30) continue;"
                    "    for(var j=0;j<Object.keys(SVC_KEYWORDS).length;j++){"
                    "      var k=Object.keys(SVC_KEYWORDS)[j];"
                    "      if(found[k]) continue;"
                    "      if(t===k||t.startsWith(k+' ')||t.endsWith(' '+k)){ found[k]=SVC_KEYWORDS[k]; result.push(SVC_KEYWORDS[k]); }"
                    "    }"
                    "  }"
                    "  return JSON.stringify(result.slice(0,8));"
                    "})()"
                )
                raw = await cdp_eval(ws, svc_js, timeout=12)
                try: return json.loads(raw) if raw else []
                except: return []

            JS_BASIC = (
                "(function(){"
                "  var text = document.body.innerText || '';"
                "  var r = {price_range:null,reporter:null,service:[],popular_items:[],photo_label:'',menu_url:null,found:false};"
                "  var rangeM = text.match(/\\$([\\d,]+)[\\u2012\\u2013\\-\\.\\-]\\s*\\$?([\\d,]+)/);"
                "  var hasPP = /per person|平均每人|每人|人均/i.test(text);"
                "  if (rangeM && hasPP) { r.price_range = '$' + rangeM[1] + '\\u2013' + rangeM[2];"
                "    var repM = text.match(/(\\d+)\\s*人回報|(\\d+)\\s*people report/i);"
                "    r.reporter = repM ? ((repM[1]||repM[2]) + '\\u4eba\\u56de\\u5831') : null; r.found = true; }"
                "  var links = document.querySelectorAll('a[href]');"
                "  for(var i=0;i<links.length;i++){"
                "    var h = (links[i].href||'').toLowerCase(); var t = (links[i].innerText||'').trim();"
                "    if((h.indexOf('dudooeat')!==-1||h.indexOf('inline_menu')!==-1||h.indexOf('menu')!==-1||h.indexOf('instagram.com')!==-1||h.indexOf('ubereats.com')!==-1||h.indexOf('foodpanda')!==-1||h.indexOf('deliveroo')!==-1||h.indexOf('chope')!==-1||(t.match(/^[Ll]ink.*[Mm]enu/)&&h.startsWith('http'))||(t.match(/^[Oo]rder/)&&h.startsWith('http'))) && h.startsWith('http') && h.length>15){"
                "      r.menu_url = links[i].href; break; }"
                "  }"
                "  return JSON.stringify(r);"
                "})()"
            )

            # Stability Loop on Overview Page
            svcs = await extract_services(ws)
            result["service"] = svcs
            prev_state = (len(svcs), 0, 0)
            stable = 0
            for rnd in range(8):
                raw = await cdp_eval(ws, JS_BASIC, timeout=20)
                if raw:
                    try:
                        info = json.loads(raw) if isinstance(raw, str) else raw
                        if info.get("price_range") and not result["price_range"]:
                            result["found"] = True
                            result["price_range"] = info.get("price_range")
                            result["reporter"] = info.get("reporter")
                        if info.get("menu_url"): result["menu_url"] = info.get("menu_url")
                    except: pass
                
                cur_svcs = await extract_services(ws)
                result["service"] = list(set(result["service"] + cur_svcs))
                cur = (len(result["service"]), 1 if result["price_range"] else 0, 1 if result["menu_url"] else 0)
                if cur == prev_state:
                    stable += 1
                    if stable >= 3: break
                else:
                    stable = 0
                    prev_state = cur
                await cdp_send_recv(ws, 300+rnd, "Input.synthesizeScrollGesture", {"x":0,"y":0,"xVelocity":0,"yVelocity":3000,"preventFling":True,"stopTargetX":0,"stopTargetY":3000}, timeout=8)
                await asyncio.sleep(0.8)

            # --- Phase 2: Tab Navigation (Only if Browser is still responsive) ---
            print("[Phase 2] Clicking '菜單' tab...")
            if await click_tab(ws, "菜單"):
                raw_menu = await cdp_eval(ws, "(function(){ var links = document.querySelectorAll('a[href]'); for(var i=0;i<links.length;i++){ var h = (links[i].href||'').toLowerCase(); var t = (links[i].innerText||'').trim(); if((h.indexOf('dudooeat')!==-1||h.indexOf('inline_menu')!==-1||h.indexOf('instagram.com')!==-1||h.indexOf('ubereats.com')!==-1||h.indexOf('foodpanda')!==-1||h.indexOf('deliveroo')!==-1||h.indexOf('chope')!==-1||h.indexOf('menu')!==-1||(t.match(/^[Ll]ink.*[Mm]enu/)&&h.startsWith('http'))||(t.match(/^[Oo]rder/)&&h.startsWith('http'))) && h.startsWith('http') && h.length>15){ return JSON.stringify({ok:true,url:links[i].href}); } } return JSON.stringify({ok:false}); })()", timeout=12)
                try:
                    mi = json.loads(raw_menu) if isinstance(raw_menu, str) else raw_menu
                    if mi.get("ok"): result["menu_url"] = mi["url"]
                except: pass

            print("[Phase 2] Clicking '評論' tab...")
            if await click_tab(ws, "評論"):
                await asyncio.sleep(0.8)
                # 抓取評論區上方的食物分類（特色食品）
                raw_food_cats = await cdp_eval(ws, "(function(){ var cats = []; var els = document.querySelectorAll('[role=navigation] button,[role=tablist] button,[role=tab]'); for(var i=0;i<els.length;i++){ var t=(els[i].innerText||'').trim(); if(t.length>0 && t.length<=10 && !t.match(/^[0-9]+則$/)) cats.push(t); } if(cats.length===0){ var navs=document.querySelectorAll('[role=navigation],nav'); for(var n=0;n<navs.length;n++){ var btns=navs[n].querySelectorAll('button'); for(var b=0;b<btns.length;b++){ var t=(btns[b].innerText||'').trim(); if(t.length>0 && t.length<=10 && !t.match(/^[0-9]+則$/)) cats.push(t); } } } return JSON.stringify({ok:true,cats:cats.slice(0,15)}); })()", timeout=12)
                try:
                    fc = json.loads(raw_food_cats) if isinstance(raw_food_cats, str) else raw_food_cats
                    result["food_categories"] = fc.get("cats", []) if isinstance(fc, dict) else []
                except: pass

                # 熱門品項（既有邏輯）
                raw_pop = await cdp_eval(ws, "(function(){ var found = []; var radios = document.querySelectorAll('[role=radio]'); for(var i=0;i<radios.length;i++){ var aria = radios[i].getAttribute('aria-label')||''; var text = (radios[i].innerText||'').trim(); if(aria.includes('mentioned in')) found.push(aria); else if(text){ var parts=text.split(String.fromCharCode(10)); if(parts.length>=2) found.push(parts[0].trim()); } } return JSON.stringify({ok:true,items:found.slice(0,8)}); })()", timeout=12)
                try:
                    pi = json.loads(raw_pop) if isinstance(raw_pop, str) else raw_pop
                    items = pi.get("items", []) if isinstance(pi, dict) else []
                    for item in items:
                        if item and item not in result["popular_items"]: result["popular_items"].append(item)
                except: pass

            # --- Phase 3: Histogram ---
            print("[Phase 3] Looking for price arrow button...")
            await cdp_eval(ws, "window.scrollTo({top:700,behavior:'instant'});null", timeout=6)
            await asyncio.sleep(1.0)
            btn_raw = await cdp_eval(ws, "(function(){ var perEl = null; var allEls = document.querySelectorAll('*'); for(var i=0;i<allEls.length;i++){ var t=(allEls[i].innerText||'').trim(); if(t.indexOf('平均每人')!==-1||(t.match(/per person/i)&&t.match(/\\$/))){perEl=allEls[i]; break;} } if(!perEl) return JSON.stringify({ok:false}); var r2=perEl.getBoundingClientRect(); return JSON.stringify({ok:true,x:Math.round(r2.left+r2.width/2),y:Math.round(r2.top+r2.height/2)}); })()", timeout=15)
            if btn_raw:
                try:
                    btn_info = json.loads(btn_raw) if isinstance(btn_raw, str) else btn_raw
                    if btn_info.get("ok"):
                        cx, cy = btn_info.get("x", 0), btn_info.get("y", 0)
                        await cdp_send_recv(ws, 400, "Input.dispatchMouseEvent", {"type":"mousePressed","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
                        await cdp_send_recv(ws, 401, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":cx,"y":cy,"button":"left","clickCount":1}, timeout=6)
                        await asyncio.sleep(2.0)
                        hist_raw = await cdp_eval(ws, "(function(){ var tables=document.querySelectorAll('table[aria-label*=histogram i]'); if(tables.length){ var rows=tables[0].querySelectorAll('tr[data-item-id]'); var entries=[]; rows.forEach(function(row){ var ltd=row.querySelector('td:first-child'); var lbl=ltd?(ltd.innerText.trim()):''; var bar=row.querySelector('span[role=img]'); var aria=bar?(bar.getAttribute('aria-label')||''):''; var pct=parseInt((aria||'').replace('%',''),10); if(lbl&&!isNaN(pct)&&pct>0) entries.push({label:lbl,pct:pct}); }); if(entries.length) return JSON.stringify({found:true,entries:entries}); } return JSON.stringify({found:false}); })()", timeout=12)
                        if hist_raw:
                            hd = json.loads(hist_raw) if isinstance(hist_raw, str) else {}
                            if hd.get("found"):
                                rep_cnt = int(re.sub(r"\\D", "", str(result.get("reporter") or "71"))) or 71
                                ents = hd.get("entries", [])
                                hist = []
                                for e2 in ents[:4]:
                                    lbl = e2.get("label", "$")
                                    pct = e2.get("pct", 0)
                                    hist.append([lbl, "約%d人" % round(pct/100*rep_cnt), pct])
                                result["price_histogram"] = hist
                except: pass

    except Exception as e:
        import traceback
        print(f"[CDP] Error: {e}")
        traceback.print_exc()
        result["error"] = str(e)

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
    # ── 火鍋/燒烤（保留並擴充）──────────────────────────────
    ("麻辣鍋","麻辣鍋"),("石頭火鍋","石頭火鍋"),("涮涮鍋","涮涮鍋"),
    ("羊肉爐","羊肉爐"),("薑母鴨","薑母鴨"),("汕頭火鍋","汕頭火鍋"),
    ("燒肉","燒肉"),("烤肉","烤肉"),("和牛","和牛"),("牛舌","牛舌"),
    ("豬五花","豬五花"),("牛五花","牛五花"),("雞腿肉","雞腿肉"),
    ("海鮮拼盤","海鮮拼盤"),("大草蝦","草蝦"),("蛤蜊","蛤蜊"),
    ("生蠔","生蠔"),("干貝","干貝"),("透抽","透抽"),
    ("牛肉串","牛肉串"),("羊肉串","羊肉串"),("雞肉串","雞肉串"),("豬五花串","豬五花串"),
    ("一夜干","一夜干"),("烤麻糬","烤麻糬"),("明太子","明太子"),
    ("柳葉魚","柳葉魚"),("烤飯糰","烤飯糰"),("飛魚卵","飛魚卵"),
    # ── 日式（保留並擴充）──────────────────────────────
    ("握壽司","握壽司"),("生魚片","生魚片"),("炙燒","炙燒"),("花壽司","花壽司"),
    ("拉麵","拉麵"),("豚骨拉麵","豚骨"),("味噌拉麵","味噌"),("醬油拉麵","醬油"),
    ("咖喱飯","咖喱飯"),("咖哩飯","咖哩飯"),("牛井","牛井"),("鰻魚飯","鰻魚飯"),
    ("烏龍麵","烏龍麵"),("蕎麥麵","蕎麥"),("咖喱烏龍","咖喱烏龍"),("咖哩烏龍","咖哩烏龍"),
    ("天婦羅","天婦羅"),("炸蝦","炸蝦"),("唐揚","唐揚"),("和風炸雞","和風炸雞"),
    ("壽喜燒","壽喜燒"),("牛丼","牛丼"),("叉燒","叉燒"),("溫泉蛋","溫泉蛋"),
    ("玉子燒","玉子燒"),("章魚燒","章魚燒"),("大阪燒","大阪燒"),("炒麵","炒麵"),
    # ── 義式/美式（保留）──────────────────────────────
    ("義大利麵","義大利麵"),("披薩","披薩"),("薯條","薯條"),("漢堡","漢堡"),
    ("炸雞","炸雞"),("雞軟骨","雞軟骨"),("雞胗","雞胗"),
    ("牛排","牛排"),("肋眼","肋眼"),("菲力","菲力"),
    # ── 飲料（保留並擴充）──────────────────────────────
    ("泰式奶茶","泰奶"),("檸檬愛玉","愛玉"),("冬瓜茶","冬瓜茶"),
    ("青茶","青茶"),("烏龍茶","烏龍茶"),("決明子茶","決明子"),
    ("手搖飲","手搖飲"),("珍奶","珍奶"),("波霸奶茶","波霸"),("波霸","波霸"),
    ("芋泥","芋泥"),("芋頭","芋頭"),("綠豆","綠豆"),("薏米","薏米"),
    ("豆漿","豆漿"),("米漿","米漿"),("冬瓜牛奶","冬瓜牛奶"),("杏仁茶","杏仁茶"),
    ("黑豆茶","黑豆茶"),("花茶","花茶"),("果茶","果茶"),("氣泡水","氣泡水"),
    ("氣泡飲","氣泡飲"),("咖啡","咖啡"),("拿鐵","拿鐵"),("卡布奇諾","卡布"),
    (" espresso","espresso"),("摩卡","摩卡"),("焦糖","焦糖"),
    ("冰沙","冰沙"),("果昔","果昔"),("smoothie","smoothie"),
    # ── 早餐品項（新增大擴充）──────────────────────────────
    ("蛋餅","蛋餅"),("蛋餅皮","蛋餅皮"),("烙餅","烙餅"),("煎餅","煎餅"),("薄餅","薄餅"),
    ("肉包","肉包"),("菜包","菜包"),("豆沙包","豆沙包"),("饅頭","饅頭"),
    ("割包","割包"),("花卷","花卷"),("銀捲","銀捲"),
    ("飯糰","飯糰"),("紫米飯糰","紫米飯糰"),("傳統飯糰","傳統飯糰"),
    ("肉粽","肉粽"),("鹼粽","鹼粽"),("南部粽","南部粽"),("北部粽","北部粽"),
    ("油條","油條"),("燒餅","燒餅"),("酥餅","酥餅"),("餡餅","餡餅"),
    ("蔥油餅","蔥油餅"),("抓餅","抓餅"),("千層餅","千層餅"),
    ("水煎包","水煎包"),("煎包","煎包"),("小籠包","小籠包"),("湯包","湯包"),
    ("蒸餃","蒸餃"),("水餃","水餃"),("鍋貼","鍋貼"),("餛飩","餛飩"),
    ("餛飩麵","餛飩麵"),("餛飩湯","餛飩湯"),("大腸麵線","大腸麵線"),("蚵仔麵線","蚵仔麵線"),
    ("蘿蔔糕","蘿蔔糕"),("菜頭粿","菜頭粿"),("碗粿","碗粿"),("米糕","米糕"),
    ("肉圓","肉圓"),("蚵仔煎","蚵仔煎"),("肉燥飯","肉燥飯"),("滷肉飯","滷肉飯"),
    ("雞腿飯","雞腿飯"),("便當","便當"),("自助餐","自助餐"),
    ("皮蛋瘦肉粥","皮蛋瘦肉粥"),("蚵仔粥","蚵仔粥"),("海鮮粥","海鮮粥"),
    ("鹹粥","鹹粥"),("白粥","白粥"),("地瓜粥","地瓜粥"),
    ("陽春麵","陽春麵"),("擔仔麵","擔仔麵"),("意麵","意麵"),
    ("鍋燒麵","鍋燒麵"),("鍋燒意麵","鍋燒意麵"),("刀削麵","刀削麵"),
    ("麻醬麵","麻醬麵"),("炸醬麵","炸醬麵"),("榨菜肉絲麵","榨菜肉絲麵"),
    ("鹹豆漿","鹹豆漿"),("甜豆漿","甜豆漿"),("豆花","豆花"),
    ("米苔目","米苔目"),("愛玉","愛玉"),("石花凍","石花凍"),
    ("仙草","仙草"),("芋圓","芋圓"),("地瓜圓","地瓜圓"),
    ("燒仙草","燒仙草"),("杏仁豆腐","杏仁豆腐"),("楊枝甘露","楊枝甘露"),
    ("油蔥蝦仁飯","油蔥蝦仁飯"),("蝦仁飯","蝦仁飯"),("蝦滷飯","蝦滷飯"),
    ("脆皮燒肉","脆皮燒肉"),("燒肉飯","燒肉飯"),
    ("鐵板麵","鐵板麵"),("蘑菇鐵板麵","蘑菇鐵板麵"),("黑胡椒鐵板麵","黑胡椒鐵板麵"),
    ("鮪魚蛋漢堡","鮪魚蛋漢堡"),("雞肉吐司","雞肉吐司"),("豬肉漢堡","豬肉漢堡"),
    ("總匯","總匯"),("三明治","三明治"),("吐司","吐司"),
    ("荷包蛋","荷包蛋"),("煎蛋","煎蛋"),("嫩蛋","嫩蛋"),("蔥蛋","蔥蛋"),
    ("剝皮辣椒","剝皮辣椒"),("胡麻","胡麻"),("胡麻豬","胡麻豬"),
    ("霹靂霹靂","霹靂霹靂"),("剝皮辣椒雞","剝皮辣椒雞"),
    # ── 中式小吃（擴充）──────────────────────────────
    ("臭豆腐","臭豆腐"),("大腸","大腸"),("小腸","小腸"),("香腸","香腸"),
    ("胗","胗"),("雞心","雞心"),("雞肝","雞肝"),
    ("豬血糕","豬血糕"),("米血","米血"),("糯米腸","糯米腸"),
    ("滷味","滷味"),("滷大腸","滷大腸"),("滷雞腿","滷雞腿"),("滷牛腱","滷牛腱"),
    ("鹹酥雞","鹹酥雞"),("雞排","雞排"),("魷魚","魷魚"),
    ("炸物","炸物"),("甜不辣","甜不辣"),("百頁豆腐","百頁豆腐"),
    ("關東煮","關東煮"),("黑輪","黑輪"),
    ("牛肉湯","牛肉湯"),("羊肉湯","羊肉湯"),("虱目魚","虱目魚"),
    ("蚵仔","蚵仔"),("蛤仔","蛤仔"),("文蛤","文蛤"),
    ("花枝","花枝"),("小卷","小卷"),("透抽","透抽"),
    ("川燙","川燙"),("川燙花枝","川燙花枝"),
    # ── 甜點/冰品（擴充）──────────────────────────────
    ("冰淇淋","冰淇淋"),("冰淇淋聖代","聖代"),("聖代","聖代"),
    ("雪花冰","雪花冰"),("剉冰","剉冰"),("芒果冰","芒果冰"),
    ("珍珠","珍珠"),("布丁","布丁"),("奶酪","奶酪"),
    ("提拉米蘇","提拉米蘇"),("蛋糕","蛋糕"),("巴斯克","巴斯克"),
    ("乳酪蛋糕","乳酪蛋糕"),("戚風蛋糕","戚風蛋糕"),("磅蛋糕","磅蛋糕"),
    ("泡芙","泡芙"),("千層","千層"),("千層蛋糕","千層蛋糕"),
    ("蛋撻","蛋撻"),("菠蘿包","菠蘿包"),("奶油包","奶油包"),
    ("司康","司康"),("瑪德蓮","瑪德蓮"),("費南雪","費南雪"),
    ("巧克力","巧克力"),("生巧克力","生巧克力"),("抹茶","抹茶"),
    ("果醬","果醬"),("蜂蜜","蜂蜜"),
    # ── 火鍋湯底/鍋物（擴充）──────────────────────────────
    ("麻辣湯底","麻辣"),("豚骨湯","豚骨"),("蔬菜湯","蔬菜湯"),
    ("牛奶鍋","牛奶鍋"),("起司鍋","起司鍋"),("咖喱鍋","咖喱鍋"),
    ("泡菜鍋","泡菜鍋"),("酸白菜鍋","酸白菜鍋"),("麻油雞","麻油雞"),
    # ── 其他主食（擴充）──────────────────────────────
    ("炒飯","炒飯"),("炒麵","炒麵"),("燴飯","燴飯"),("蓋飯","蓋飯"),
    ("雞肉飯","雞肉飯"),("排骨飯","排骨飯"),("牛腩飯","牛腩飯"),
    ("焢肉飯","焢肉飯"),("控肉飯","控肉飯"),("爌肉飯","爌肉飯"),
    ("羊肉炒麵","羊肉炒麵"),("蝦仁炒麵","蝦仁炒麵"),
    ("剝皮辣椒麵","剝皮辣椒麵"),("剝皮辣椒雞麵","剝皮辣椒雞麵"),
]

def extract_dish_highlights(reviews):
    found = {}
    for review in reviews:
        content = review.get("content", "")
        for pattern, canonical in DISH_ITEMS:
            if canonical in found: continue
            key = pattern.split("，")[0].split("（")[0]
            idx = content.find(key)
            if idx < 0: continue
            snippet = content[idx + len(key): idx + 80].strip()
            snippet = re.sub(r"[\n\r]+", "，", snippet)
            snippet = re.sub(r"，+，", "，", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            m = re.search(r"[。！？\?!]", snippet)
            if m: snippet = snippet[:m.end()]
            snippet = snippet.strip("。，、：：「」\"''()（）　 ")
            if len(snippet) < 4: continue
            found[canonical] = (pattern, snippet)
        if len(found) >= 10: break
    result = []
    for pattern, canonical in DISH_ITEMS:
        if canonical in found:
            result.append((found[canonical][0], found[canonical][1]))
    return result[:8]


def _days_friendly(days):
    if days <= 0: return "今天"
    if days < 30: return f"{days}天前"
    return f"{days // 30}個月前"

# ─── 網友心得 ────────────────────────────────────────────────
def extract_review_highlights(reviews):
    # 按發布時間由新到舊排序
    sorted_reviews = sorted(reviews, key=lambda r: r.get("days_ago", 999))
    results = []; seen = set()
    for review in sorted_reviews:
        author = review.get("author", "")
        content = review.get("content", "")
        if not content or author == "LISON": continue
        days_ago = review.get("days_ago", 0)
        time_str = _days_friendly(days_ago)
        for sent in re.split(r"[。\n]", content):
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 80: continue
            if re.search(r"\$\d+", sent): continue
            if sent in seen: continue
            seen.add(sent); results.append((author, sent, time_str)); break
        if len(results) >= 5: break
    unique = []
    for author, note, time_str in results:
        if len(note) < 10: continue
        if len(note) > 80: note = note[:80] + "…"
        unique.append((author, note, time_str))
    return unique[:5]


# ─── 用戶反饋價格 ────────────────────────────────────────────────
def format_reviews_price(reviews):
    lines = []
    for rev in reviews:
        content = rev.get("content", "")
        prices  = extract_prices(content)
        if not prices: continue
        author = rev.get("author", "匿名")
        rating = rev.get("rating", 0)
        days = rev.get("days_ago", 0)
        time_str = _days_friendly(days)
        lines.append(f"· {author}（{rating}⭐，{time_str}）提及：{', '.join(prices)}")
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
            if m: pos = max(0, m.start() - 35); break
    if pos < 0: pos = 0
    snippet = text[pos:pos + max_len]
    for punct in ["。", "，", "！", "？"]:
        idx = snippet.rfind(punct, int(max_len * 0.5), max_len)
        if idx > 0: snippet = snippet[:idx + 1]; break
    if pos > 0: snippet = "…" + snippet.strip()
    return snippet if snippet else text[:max_len]


# ─── 地址格式化 ────────────────────────────────────────────────
def format_address(addr_en):
    a = addr_en.strip()
    if not a: return addr_en
    zipcode = ""
    zm = re.search(r"\b(\d{3,5})\s*$", a)
    if zm:
        zipcode = zm.group(1)
        a = a[:zm.start()].strip().rstrip(",").rstrip()
    house_num = ""
    hm = re.search(r"No\.?\s*(\d+)號?", a)
    if hm:
        house_num = hm.group(1) + "號"
        a = re.sub(r"No\.?\s*\d+號?\s*,\s*", "", a, count=1).strip()
    else:
        hm2 = re.search(r"^(\d+)號\s*,\s*", a)
        if hm2:
            house_num = hm2.group(1) + "號"
            a = a[hm2.end():].strip()
    section_num = ""
    m = re.search(r"Section\s*(\d+)", a, re.IGNORECASE)
    if m:
        section_num = m.group(1) + "段"
        a = re.sub(r"Section\s*\d+\s*,?\s*", "", a, flags=re.IGNORECASE).strip(",").strip()
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
        "Zhongshan Rd":"中山路","Zhongqing Rd":"重慶路","Zhongqing Road":"重慶路",
        "Zhongqing":"重慶",
        "Shunping Rd":"順平路","Shunping":"順平",
        "Chang'an Rd":"長安路","Changan Rd":"長安路","ChangAn":"長安",
        "Shenyang Rd":"瀋陽路","Shenyang":"瀋陽",
        "Leizhong Rd":"累中 路","Leizhong":"累中",
        "Rd":"路","Road":"路","St":"街","Street":"街",
        "Lane":"巷","Alley":"巷","Ave":"路","Avenue":"路",
    }
    for en, zh in sorted(rep_map.items(), key=lambda x: -len(x[0])):
        a = a.replace(en, zh)
    a = re.sub(r",+", "，", a); a = re.sub(r"，+", "，", a)
    a = a.strip("，").strip()
    a = re.sub(r"^No\.?\s*", "", a).strip()
    a = re.sub(r"Taiwan", "台灣", a, flags=re.IGNORECASE)
    a = re.sub(r"，?\s*台灣\s*$", "", a, flags=re.IGNORECASE).strip()
    a = re.sub(r"，?\s*Taiwan\s*$", "", a, flags=re.IGNORECASE).strip()
    a = re.sub(r"台灣\s*", "", a)
    a = re.sub(r"\b\d{5,6}(?=\S)", "", a)
    road_kws = ["路","街","巷","弄","大道"]
    tokens = [t.strip() for t in re.split(r"[，,]+", a) if t.strip()]
    city = ""; district = ""; road = ""; others = []
    for tok in tokens:
        if any(tok.endswith(k) for k in road_kws): road = tok
        elif tok in ["台中市","彰化市","台北市","新北市","新竹市"]: city = tok
        elif "區" in tok and tok != "台灣": district = tok
        else: others.append(tok)
    zip_label = f"（{zipcode}）" if zipcode else ""
    return city + district + "".join(others) + road + section_num + house_num + zip_label


# ─── 輸出格式化 ────────────────────────────────────────────────
def format_output(data, maps_price, reviews, price_range_api=None, all_reviews=None):
    raw_name = data.get("name","未知")
    name     = raw_name.split("|")[0].strip()
    addr     = data.get("address","無")
    lat      = data.get("location",{}).get("lat","")
    lng      = data.get("location",{}).get("lng","")
    phone    = data.get("phone","無")
    rating   = data.get("rating","無")
    rcount   = data.get("user_rating_count", 0)
    website  = data.get("website","無")
    open_now = data.get("open_now")
    # 營業時間解析
    hours_data = data.get("currentOpeningHours") or data.get("hours")
    place_id = data.get("place_id","")
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    api_name, api_addr = get_localized_name_addr(place_id)
    if api_name: name = api_name
    if api_addr: addr = api_addr
    lines = []
    lines.append(f"🏪 店名：{name}")
    lines.append(f"📍 地址：{format_address(addr)}")
    lines.append(f"📍 經緯度：{round(lat,6)}, {round(lng,6)}")
    lines.append(f"📞 電話：{phone}")
    lines.append(f"⭐ 評分：{rating}（{rcount}則）")
    now = datetime.now()
    day_names_en = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    today_en = day_names_en[now.weekday()]
    today_hours_line = None

    if isinstance(hours_data, dict):
        reg_hours = hours_data.get("regularHours", [])
        for h in reg_hours:
            if isinstance(h, dict) and h.get("day") == today_en:
                tp = h.get("hours", "")
                today_hours_line = None if "closed" in tp.lower() else tp
                break
    elif isinstance(hours_data, list):
        for h in hours_data:
            if not h: continue
            if isinstance(h, dict) and h.get("day") == today_en:
                tp = h.get("hours", "")
                today_hours_line = None if "closed" in tp.lower() else tp
                break
            elif isinstance(h, str):
                parts = h.split(": ", 1)
                if len(parts) == 2 and parts[0].strip() == today_en:
                    tp = parts[1].strip()
                    today_hours_line = None if tp.lower() == "closed" else tp
                    break
    if open_now is True:
        if today_hours_line:
            full_m = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)', today_hours_line, re.IGNORECASE)
            close_m = re.search(r'[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)', today_hours_line, re.IGNORECASE)
            if full_m and close_m:
                ch=int(full_m[4]); cm=int(full_m[5]); campm=full_m[6].upper()
                close_h24 = ch%12+(12 if campm=='PM' else 0)
                close_dt = now.replace(hour=close_h24, minute=cm, second=0, microsecond=0)
                if close_h24 <= 0: close_dt += timedelta(days=1)
                diff = close_dt - now
                secs = int(diff.total_seconds())
                tl = f"距離關門 {secs//3600} 小時 {(secs%3600)//60} 分鐘" if secs > 0 else "已超過關門時間"
                lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}，{tl}）")
            else:
                lines.append(f"🚦 狀態：✅ 營業中（今日 {today_hours_line}）")
        else:
            lines.append(f"🚦 狀態：✅ 營業中")
    elif open_now is False:
        if today_hours_line:
            lines.append(f"🚦 狀態：❌ 休息中（今日 {today_hours_line}）")
        else:
            lines.append(f"🚦 狀態：❌ 休息中")
    else:
        lines.append(f"🚦 狀態：❌ 休息中")
    lines.append(f"🌐 網站：{website}")
    lines.append(f"🔗 Google Maps：{maps_url}")
    lines.append(f"🌐 官方 Google 商家頁面：https://www.google.com/search?q={urllib.parse.quote(name)}#{maps_url.split('?')[1]}")
    price_hist = (maps_price.get("price_histogram",[]) if maps_price else [])
    rep_label  = (maps_price.get("reporter","") if maps_price else "")
    if price_range_api:
        lines.append(f"💵 每人消費：{price_range_api}" + (f"（{rep_label}）" if rep_label else ""))
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
        if menu_url: lines.append(f"🍽️ Menu：{menu_url}")
    svcs = (maps_price.get("service", []) if maps_price else [])
    if svcs: lines.append(f"📌 服務：{ '、'.join(svcs) }")
    pop_items = (maps_price.get("popular_items", []) if maps_price else [])
    if pop_items:
        cleaned = []
        for item in pop_items:
            m = re.search(r'^(.+?)(?:[,\s]+\d+\s*則)?[評論提到]*$', item.strip())
            label = m.group(1).strip() if m else item.strip()
            if label and label not in cleaned: cleaned.append(label)
        if cleaned: lines.append(f"🍜 熱門品項：{'｜'.join(cleaned[:8])}")
    food_cats = (maps_price.get("food_categories", []) if maps_price else [])
    if food_cats:
        lines.append(f"🔥 特色食品：{'、'.join(food_cats)}")
    else:
        # fallback to dish highlights if no food categories found
        dish_hl = extract_dish_highlights(reviews)
        if dish_hl:
            lines.append("🔥 特色菜色：")
            for dish_name, snippet in dish_hl: lines.append(f"   {dish_name}：{snippet}")
    rev_hl = extract_review_highlights(all_reviews if all_reviews is not None else reviews)
    if rev_hl:
        lines.append("📝 網友心得：")
        for author, note, time_str in rev_hl:
            note2 = note if len(note) <= 150 else note[:150]+"…"
            lines.append(f"   {author}：{note2}（{time_str}）")
    price_lines = format_reviews_price(reviews)
    if price_lines:
        lines.append("💬 用戶反饋價格（6個月內）：")
        for pl in price_lines: lines.append(pl)
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
    out = goplaces(f'search "{query}" --limit {limit}' + (f" --lat {lat} --lng {lng} --radius-m {radius}" if lat and lng else "") + (f" --min-rating {min_rating}" if min_rating else "") + (" --open-now" if open_now else ""))
    lines_out = out.strip().split("\n")
    place_id = None
    for line in lines_out:
        if line.startswith("ID:"):
            place_id = line.split("ID:")[1].strip().split()[0]; break
    if not place_id:
        print("（未找到 place_id）\n"+out); return
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    all_reviews, data = get_reviews(place_id)
    if not data:
        print("（未找到 place_id）\n"+out); return
    reviews_6m = [r for r in all_reviews if r.get("days_ago", 999) <= 180]
    price_range_api = get_price_range_api(place_id)
    maps_price = {"found": False}
    try:
        maps_price = asyncio.run(asyncio.wait_for(
            scrape_price_from_browser(place_id, maps_url),
            timeout=45.0
        ))
    except asyncio.TimeoutError:
        maps_price = {"found": False, "error": "CDP timeout (45s)"}
        print("[CDP] ⚠️ CDP timeout after 45s, skipping CDP data", flush=True)
    except Exception as e:
        maps_price = {"found": False, "error": str(e)}
        print(f"[CDP] ⚠️ CDP error: {e}", flush=True)
    print(format_output(data, maps_price, reviews_6m, price_range_api, all_reviews))


def cmd_full(args):
    place_id = next((a for a in args if not a.startswith("--")), None)
    if not place_id:
        print("錯誤：缺少 place_id"); return
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    all_reviews, data = get_reviews(place_id)
    if not data:
        print("錯誤：無法取得店家資料"); return
    reviews_6m = [r for r in all_reviews if r.get("days_ago", 999) <= 180]
    price_range_api = get_price_range_api(place_id)
    maps_price = {"found": False}
    try:
        maps_price = asyncio.run(asyncio.wait_for(
            scrape_price_from_browser(place_id, maps_url),
            timeout=45.0
        ))
    except asyncio.TimeoutError:
        maps_price = {"found": False, "error": "CDP timeout (45s)"}
        print("[CDP] ⚠️ CDP timeout after 45s, skipping CDP data", flush=True)
    except Exception as e:
        maps_price = {"found": False, "error": str(e)}
        print(f"[CDP] ⚠️ CDP error: {e}", flush=True)
    print(format_output(data, maps_price, reviews_6m, price_range_api, all_reviews))


def cmd_details(args):
    place_id = args[0]
    all_reviews, data = get_reviews(place_id)
    if not data:
        print("錯誤：無法取得店家資料"); return
    reviews_6m = [r for r in all_reviews if r.get("days_ago", 999) <= 180]
    price_range_api = get_price_range_api(place_id)
    print(format_output(data, {"found": False}, reviews_6m, price_range_api, all_reviews))


if __name__ == "__main__":
    # ─── Chrome 預熱（避免冷啟動延遲）───────────────────────────────
    _WARMED = False

def warmup_chrome():
    """預熱 Chrome CDP：啟動並建立一個空 tab，避免第一次查詢時冷啟動。"""
    global _WARMED
    if _WARMED:
        return
    import urllib.request, json, time, socket, os
    HOST = "127.0.0.1"
    PORT = 18800   # 與 scrape_price_from_browser() 一致

    def port_used(port):
        s = socket.socket(); s.settimeout(1)
        try:
            s.connect((HOST, port)); s.close(); return True
        except Exception:
            return False

    def cdp_reachable():
        try:
            req = urllib.request.Request(f"http://{HOST}:{PORT}/json")
            with urllib.request.urlopen(req, timeout=3) as r:
                return bool(json.loads(r.read()))
        except Exception:
            return False

    def start_edge_background():
        # ★ 分離 profile：warmup 用獨立目錄，不影響 scrape 的 Chrome session
        WARMUP_PROFILE = "/tmp/openclaw-chrome-warmup"
        os.makedirs(WARMUP_PROFILE, exist_ok=True)
        if port_used(PORT):
            os.system("ps aux 2>/dev/null | grep 'openclaw-chrome-warmup' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null; sleep 2")
        import subprocess
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        edge_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        browser = chrome_path if os.path.exists(chrome_path) else edge_path
        args = [
            browser,
            "--headless=new",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={WARMUP_PROFILE}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ]
        try:
            subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    if not cdp_reachable():
        start_edge_background()
        for _ in range(15):
            time.sleep(1)
            if cdp_reachable():
                break
    if cdp_reachable():
        try:
            req = urllib.request.Request(f"http://{HOST}:{PORT}/json/new")
            with urllib.request.urlopen(req, timeout=5) as r:
                json.loads(r.read())
        except Exception:
            pass
    _WARMED = True
    print("[Chrome] 預熱完成")


    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    # 第一次 full/details 指令時自動預熱
    if cmd in ("full", "details") and not _WARMED:
        warmup_chrome()

    {"search": cmd_search, "details": cmd_details, "full": cmd_full}.get(cmd, lambda _: print(f"未知指令：{cmd}"))(args)
