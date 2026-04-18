#!/usr/bin/env python3
"""Scrape v8 - Phase 2 tab clicks + Phase 3 arrow button + 4-strategy histogram"""
import asyncio, websockets, json as _json, urllib.request, time, re as _re

async def scrape_price_from_browser(place_id, maps_url=None):
    maps_url = maps_url or f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    print(f"[CDP] place={place_id[:20]}")

    result = {
        "found": False, "price_range": None, "reporter": None,
        "price_histogram": [], "service": [], "popular_items": [],
        "photo_label": "", "menu_url": None,
    }

    HOST = "127.0.0.1"; PORT = 18800

    def get_all_tabs(max_wait=60):
        for _ in range(max_wait):
            try:
                req = urllib.request.Request(f"http://{HOST}:{PORT}/json")
                with urllib.request.urlopen(req, timeout=5) as r:
                    tabs = _json.loads(r.read())
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
                return bool(_json.loads(r.read()))
        except Exception:
            return False

    async def cdp_send_recv(ws, mid, method, params=None, timeout=10.0):
        msg = {"id": mid, "method": method}
        if params:
            msg["params"] = params
        await ws.send(_json.dumps(msg))
        for _ in range(12):
            r = await asyncio.wait_for(ws.recv(), timeout=timeout)
            d = _json.loads(r)
            if d.get("id") == mid:
                return d
        return None

    async def cdp_eval(ws, expr, timeout=15.0):
        for attempt in range(2):
            try:
                r = await cdp_send_recv(ws, 99, "Runtime.evaluate",
                    {"expression": expr, "returnByValue": True}, timeout=timeout)
                if r:
                    val = r.get("result", {}).get("result", {}).get("value", "")
                    return val if val is not None else ""
                return ""
            except Exception:
                if attempt < 1:
                    await asyncio.sleep(0.5)
        return ""

    async def ws_ping(ws_url_str, timeout=5.0):
        try:
            async with websockets.connect(ws_url_str, open_timeout=timeout) as ws_ping:
                r = await asyncio.wait_for(
                    cdp_send_recv(ws_ping, 999, "Runtime.evaluate",
                                  {"expression": "1+1", "returnByValue": True}, timeout=timeout),
                    timeout=timeout)
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
                print(f"[CDP] WS OK: {tab.get('url','')[:60]}")
                return wurl, tab
        print("[CDP] Building new Maps tab...")
        for tab in tab_list:
            wurl = tab.get("webSocketDebuggerUrl", "")
            if not wurl or not await ws_ping(wurl):
                continue
            try:
                async with websockets.connect(wurl, open_timeout=10) as host_ws:
                    r = await asyncio.wait_for(
                        cdp_send_recv(host_ws, 777, "Target.createTarget",
                                      {"url": maps_url}, timeout=15), timeout=15)
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
            info = _json.loads(raw) if isinstance(raw, str) else raw
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
        print("[CDP] Browser not running; start with browser tool first")
        return {"found": False, "error": "browser not started"}

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
                "    var h = links[i].href || '';"
                "    if(h.indexOf('dudooeat')!==-1||h.indexOf('inline_menu')!==-1||h.indexOf('menu')!==-1){"
                "      r.menu_url = h; break;"
                "    }"
                "  }"
                "  return JSON.stringify(r);"
                "})()"
            )

            raw_basic = await cdp_eval(ws, JS_BASIC, timeout=20)
            if raw_basic:
                try:
                    basic = _json.loads(raw_basic) if isinstance(raw_basic, str) else raw_basic
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
                    "    var h = links[i].href || '';"
                    "    var t = (links[i].innerText||'').trim();"
                    "    if((h.indexOf('dudooeat')!==-1||h.indexOf('menu')!==-1||"
                    "        t.match(/^[Oo]rder/)||t.match(/^[Ll]ink.*[Mm]enu/))&&"
                    "       h.startsWith('http') && h.length>20){"
                    "      return JSON.stringify({ok:true,url:h,text:t.substring(0,60)});"
                    "    }"
                    "  }"
                    "  return JSON.stringify({ok:false});"
                    "})()"
                ), timeout=12)
                if raw_menu:
                    try:
                        mi = _json.loads(raw_menu) if isinstance(raw_menu, str) else raw_menu
                        if mi.get("ok") and mi.get("url"):
                            result["menu_url"] = mi["url"]
                            print("  [CDP] Menu URL: %s" % mi["url"][:80])
                    except Exception:
                        pass

            # ── click "評論" tab ────────────────────────────
            print("[Phase 2] Clicking '評論' tab...")
            clicked = await click_tab(ws, "評論", wait=3)
            if clicked:
                raw_pop = await cdp_eval(ws, (
                    "(function(){"
                    "  var radios = document.querySelectorAll('[role=radio]');"
                    "  var found = [];"
                    "  for(var i=0;i<radios.length;i++){"
                    "    var lbl = radios[i].getAttribute('aria-label')||'';"
                    "    if(lbl.includes('mentioned in')) found.push(lbl);"
                    "  }"
                    "  return JSON.stringify({ok:true,items:found.slice(0,8)});"
                    "})()"
                ), timeout=12)
                if raw_pop:
                    try:
                        pi = _json.loads(raw_pop) if isinstance(raw_pop, str) else raw_pop
                        items = (pi.get("items", []) if isinstance(pi, dict) else [])
                        for item in items:
                            if item and item not in result["popular_items"]:
                                result["popular_items"].append(item)
                        if items:
                            print("  [CDP] Popular items: %s" % items[:3])
                    except Exception:
                        pass

            # ── back to overview, polling ───────────────────
            await click_tab(ws, "總覽", wait=2)
            await asyncio.sleep(1)

            prev_state = (0, 0, 0)
            stable = 0
            for rnd in range(8):
                print("[Phase 2 polling %d]" % rnd)
                raw = await cdp_eval(ws, JS_BASIC, timeout=20)
                if raw:
                    try:
                        info = _json.loads(raw) if isinstance(raw, str) else raw
                    except Exception:
                        info = {}
                    if info.get("price_range") and not result["price_range"]:
                        result["found"] = True
                        result["price_range"] = info.get("price_range")
                        result["reporter"] = info.get("reporter")
                    if info.get("menu_url") and not result["menu_url"]:
                        result["menu_url"] = info.get("menu_url")

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
                        btn_info = _json.loads(btn_raw) if isinstance(btn_raw, str) else btn_raw
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
                                    hd = _json.loads(hist_raw)
                                except Exception:
                                    hd = {}
                                if hd.get("found"):
                                    rep_str = str(result.get("reporter") or "71")
                                    rep_cnt = int(_re.sub(r"\D", "", rep_str)) or 71
                                    ents = hd.get("entries", [])
                                    hist = []
                                    for e2 in ents[:4]:
                                        lbl = e2.get("label", "$")
                                        pct = e2.get("pct", 0)
                                        cnt = round(pct/100*rep_cnt)
                                        hist.append([lbl, "\u7e23%d\u4eba" % cnt, pct])
                                    if not hist:
                                        nums = hd.get("nums", [])
                                        parts = hd.get("parts", [])
                                        for i2, ns in enumerate(nums):
                                            pct2 = int(ns.replace("%",""))
                                            lbl2 = parts[i2].strip() if i2 < len(parts) else "$"
                                            cnt2 = round(pct2/100*rep_cnt)
                                            hist.append([lbl2, "\u7e23%d\u4eba" % cnt2, pct2])
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
