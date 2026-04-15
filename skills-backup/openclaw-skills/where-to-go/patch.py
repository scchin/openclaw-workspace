#!/usr/bin/env python3
"""一次性補丁：還原備份 + 套用所有修改"""
import re, ast, sys

SRC = "/Users/KS/.openclaw/workspace/skills-backup/openclaw-skills/where-to-go/scripts/run.py"
DST = "/Users/KS/.openclaw/skills/where-to-go/scripts/run.py"

with open(SRC, encoding="utf-8") as f:
    c = f.read()

print(f"備份行數: {len(c.splitlines())}")

# ── 1. Unicode → ASCII（框線字元）─────────────────────────────
pairs = [
    ("\u2502", "|"),   # │
    ("\u252C", "+"),   # ╭
    ("\u251C", "+"),   # ╰
    ("\u2501", "|"),   # ║
    ("\u2550", "-"),   # ═
    ("\u2500", "-"),   # ─
]
for old, new in pairs:
    n = c.count(old)
    if n: print(f"  U+{ord(old):04X}→{new!r}: {n}處")
    c = c.replace(old, new)
print("✅ 1. Unicode框線→ASCII")

# ── 2. 版本號 ────────────────────────────────────────────────
c = c.replace("v2.0（2026-03-22）", "v2.2（2026-03-23）")
print("✅ 2. 版本→v2.2")

# ── 3. 加入「冰」關鍵字 ──────────────────────────────────────
c = c.replace(
    '    "早午餐", "brunch", "咖啡", "甜點", "蛋糕", "冰淇淋",',
    '    "冰", "早午餐", "brunch", "咖啡", "甜點", "蛋糕", "冰淇淋",'
)
print("✅ 3. 加入冰關鍵字")

# ── 4. main() 包 code block ─────────────────────────────────
c = c.replace(
    '    print(result)\n\n\nif __name__ == "__main__":',
    '    print("```")\n    print(result)\n    print("```")\n\n\nif __name__ == "__main__":'
)
print("✅ 4. main()包code block")

# ── 5. 重寫 format_full_output ──────────────────────────────
# 找舊函式範圍
m = re.search(r'\ndef format_full_output\(raw.*?(?=\n(?:def |class |# -{10}|\Z))', c, re.DOTALL)
if not m:
    print("❌ 找不到 format_full_output")
    sys.exit(1)
old_fn = m.group()
old_start = m.start()
old_end = m.end()
print(f"舊函式長: {len(old_fn)} 字元")

# 新函式本體（直接寫 Unicode，避免轉義地獄）
new_fn = '''
def format_full_output(place_data: dict, maps_price: dict,
                       food_kw: Optional[str], dist_m: float,
                       index: int, reviews: list = None) -> str:
    """
    新版卡片格式（2026-03-23）：每資訊一行，| 開頭為獨立區塊。
    """
    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    name    = place_data.get("name", "未知店家") if place_data else "未知店家"
    pid     = place_data.get("place_id", "") if place_data else ""
    rating  = place_data.get("rating", 0) if place_data else 0
    rcount  = place_data.get("user_rating_count", 0) if place_data else 0
    address = place_data.get("formattedAddress", "無地址") if place_data else "無地址"
    phone   = place_data.get("phone", "無") if place_data else "無"
    open_now = place_data.get("open_now") if place_data else None
    price_rng = maps_price.get("price_range") or ""
    svcs = maps_price.get("service", [])
    price_hist = maps_price.get("price_histogram", [])

    maps_url = f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""

    drv = estimate_time(dist_m, "driving")
    wal = estimate_time(dist_m, "walking")
    max_dist = 3000
    bar_w = min(10, max(1, int(dist_m / max_dist * 10))) if max_dist > 0 else 5
    bar = "▓" * bar_w + "░" * (10 - bar_w)

    icon = "✅" if open_now else "❌"
    txt  = "營業中" if open_now else "休息中"

    lines = []
    food_tag = f"｜🍴 符合：{food_kw}" if food_kw else ""

    lines.append(f"  {medal[index]} +{'-' * 50}")
    lines.append(f"    | {name}{food_tag}")
    lines.append(f"    | ⭐ {rating}（{rcount}則）")
    lines.append(f"    | {bar}")
    lines.append(f"    | 🚗{drv}分 🚶{wal}分")
    lines.append(f"    | {icon} {txt}")

    if address and address != "無地址":
        lines.append(f"    | 📍 {address}")
    if phone and phone != "無":
        lines.append(f"    | 📞 {phone}")

    if price_rng:
        lines.append(f"    | 💵 {price_rng}")
    elif price_hist:
        for lbl, cnt, pct in price_hist:
            bar2 = "▓" * max(1, int(pct / 10)) + "░" * (10 - max(1, int(pct / 10)))
            lines.append(f"    | 💵 {lbl}")
            lines.append(f"    |   {bar2}  {cnt}（{pct}%）")

    if svcs:
        lines.append(f"    | 📌 {'、'.join(svcs)}")

    # 特色菜色
    dish_list = _dish_from_reviews(reviews or [])
    if dish_list:
        seen = set()
        for dname, snippet in dish_list:
            if dname not in seen:
                seen.add(dname)
                s2 = snippet[:80] + "..." if len(snippet) > 80 else snippet
                lines.append(f"    | 🍴 {dname}：{s2}")
        if not seen:
            lines.append("    | 🍴 無（近期評論中未抓獲特定菜色）")
    else:
        lines.append("    | 🍴 無（近期評論中未抓獲特定菜色）")

    # 網友心得
    rev_list = _rev_from_list(reviews or [])
    if rev_list:
        for author, note in rev_list[:3]:
            n2 = note[:60] + "..." if len(note) > 60 else note
            lines.append(f"    | 👤 {author}：{n2}")
    else:
        lines.append("    | 👤 無（近期無評論）")

    if maps_url:
        lines.append(f"    | 🗺️ {maps_url}")

    lines.append(f"    +{'-' * 50}")

    return "\\n".join(lines)

'''

c = c[:old_start] + new_fn + c[old_end:]
print("✅ 5. format_full_output 重寫")

# ── 6. 補 _parse_maps_price_from_raw ────────────────────────
_parse_fn = '''

def _parse_maps_price_from_raw(raw: str) -> dict:
    """從 query.py full 的 raw 文字輸出中，解析 CDP maps_price 結構"""
    mp = {"found": False, "price_range": None, "reporter": None,
          "price_histogram": [], "service": [], "popular_items": [], "menu_url": None}

    m = re.search(r"💵\s*每人消費：([^\n]+)", raw)
    if m:
        line = m.group(1).strip()
        bar_m = re.search(r"^([^\n]+?)(?:\s{2,}|$)", line)
        if bar_m:
            price_part = bar_m.group(1).strip()
            price_part = re.sub(r"^【CDP 無法提供】", "", price_part)
            price_part = re.sub(r"（[^）]*人回報[^）]*）$", "", price_part)
            cdp_direct = "【CDP 無法提供】" not in m.group(0)
            if price_part and price_part not in ("店家未提供", "無法讀取", "無"):
                mp["found"] = cdp_direct
                mp["price_range"] = price_part

    rm = re.search(r"（(\d+)\s*人回報）", raw)
    if rm:
        mp["reporter"] = f"{rm.group(1)}人回報"

    for line in raw.split("\\n"):
        hm = re.search(r"\s*([▓░])\s+(\$[^\s]+)\s+(約\d+人)\s+（(\d+)%）", line)
        if hm:
            mp["price_histogram"].append([hm.group(2), hm.group(3), int(hm.group(4))])

    sm = re.search(r"📌\s*服務：([^\n]+)", raw)
    if sm:
        mp["service"] = [s.strip() for s in re.split(r"[、，]", sm.group(1)) if s.strip()]

    return mp

'''

# 插入在 format_full_output 之後
ff_end = c.find("def format_full_output", old_start)
# 找這個新函式的結尾
ff_match = re.search(r'\ndef format_full_output.*?(?=\n(?:def |class |# -{10}|\Z))', c, re.DOTALL)
if ff_match:
    insert_pos = ff_match.end()
    c = c[:insert_pos] + _parse_fn + c[insert_pos:]
    print("✅ 6. _parse_maps_price_from_raw 已插入")
else:
    print("❌ 6. 找不到插入點")

# ── 7. 補 _get_reviews_from_api_data ────────────────────────
_reviews_fn = '''

def _get_reviews_from_api_data(api_data: dict) -> list:
    """從 api_data 中取出評論（Progressive time window 過濾）"""
    raw_reviews = api_data.get("_all_reviews", []) or api_data.get("reviews", [])
    if not raw_reviews:
        return []

    from datetime import datetime, timezone, timedelta
    WINDOWS = [180, 365, 730, float("inf")]
    now_utc = datetime.now(timezone.utc)

    enriched = []
    for r in raw_reviews:
        orig_t = (r.get("original_text", {}) or {}).get("text", "") if isinstance(r.get("original_text"), dict) else str(r.get("original_text", ""))
        trans_t = (r.get("text", {}) or {}).get("text", "") if isinstance(r.get("text"), dict) else str(r.get("text", ""))
        raw_content = orig_t or trans_t
        try:
            from deep_translator import GoogleTranslator
            content = GoogleTranslator(source="auto", target="zh-TW").translate(raw_content) if raw_content else raw_content
        except Exception:
            content = raw_content
        pub_str = r.get("publish_time", "")
        try:
            pub_time = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(timezone.utc)
            days_ago = (now_utc - pub_time).days
        except Exception:
            pub_time = now_utc
            days_ago = 0
        enriched.append({
            "author": (r.get("author") or {}).get("display_name", "匿名") if isinstance(r.get("author"), dict) else r.get("author", "匿名"),
            "rating": r.get("rating", 0),
            "publish_time": pub_time.strftime("%Y-%m-%d") if pub_str else "",
            "days_ago": days_ago,
            "content": content,
            "_pub_time": pub_time,
        })

    enriched.sort(key=lambda x: x["_pub_time"], reverse=True)

    for days_limit in WINDOWS:
        if days_limit == float("inf"):
            candidates = enriched[:]
        else:
            cutoff = now_utc - timedelta(days=days_limit)
            candidates = [r for r in enriched if r["_pub_time"] >= cutoff]
        if len(candidates) >= 5:
            return candidates[:5]
    return enriched[:5]

'''

# 插入在 _parse_maps_price_from_raw 之後
if "_parse_maps_price_from_raw" in c:
    pos = c.find("_parse_maps_price_from_raw")
    end_pos = re.search(r'\ndef _parse_maps_price_from_raw.*?(?=\n(?:def |class |# -{10}|\Z))', c, re.DOTALL)
    if end_pos:
        insert_pos = end_pos.end()
        c = c[:insert_pos] + _reviews_fn + c[insert_pos:]
        print("✅ 7. _get_reviews_from_api_data 已插入")

# ── 8. 補 _dish_from_reviews 和 _rev_from_list ──────────────
_dish_fn = '''

# ── 特色菜色 ──────────────────────────────────────────────────
_DISH_PATTERNS = [
    ("蝦滷飯","蝦滷飯"),("澎湖小卷","小卷"),("煎干貝","干貝"),("脆皮燒肉","燒肉"),
    ("辣椒","辣椒"),("海鮮炒麵","炒麵"),("海鮮粥","海鮮粥"),("油蔥蝦仁飯","油蔥蝦仁飯"),
    ("川燙花枝","花枝"),
    ("燒賣","燒賣"),("蝦餃","蝦餃"),("蝦餃皇","蝦餃皇"),("叉燒包","叉燒包"),
    ("流沙包","流沙包"),("蛋撻","蛋撻"),("菠蘿包","菠蘿包"),("鮮蝦腸粉","腸粉"),
    ("牛肉丸","牛肉丸"),("蒸餃","蒸餃"),("小籠包","小籠包"),("腐皮捲","腐皮捲"),
    ("煲仔飯","煲仔飯"),("咖哩魚蛋","魚蛋"),("雲吞","雲吞"),("餛飩","餛飩"),
    ("鹹水角","鹹水角"),("春捲","春捲"),("叉燒飯","叉燒飯"),("燒臘","燒臘"),
    ("烤鴨","烤鴨"),("豆花","豆花"),("燒仙草","燒仙草"),
    ("鐵板麵","鐵板麵"),("陽春麵","陽春麵"),("蛋餅","蛋餅"),("鍋貼","鍋貼"),
    ("水煎包","水煎包"),("蔥油餅","蔥油餅"),("餡餅","餡餅"),
    ("蘿蔔糕","蘿蔔糕"),("碗粿","碗粿"),("肉粽","肉粽"),("飯糰","飯糰"),
    ("蚵仔麵線","蚵仔麵線"),("麵線","麵線"),
    ("豆漿","豆漿"),("米漿","米漿"),("鹹豆漿","鹹豆漿"),("甜豆漿","甜豆漿"),
    ("燒餅","燒餅"),("油條","油條"),("水餃","水餃"),("肉圓","肉圓"),
    ("蚵仔煎","蚵仔煎"),("肉燥飯","肉燥飯"),("滷肉飯","滷肉飯"),("雞腿飯","雞腿飯"),
    ("便當","便當"),("自助餐","自助餐"),("素食","素食"),
]

def _dish_from_reviews(reviews):
    found = {}
    for review in reviews:
        content = review.get("content","")
        for pattern, canonical in _DISH_PATTERNS:
            if canonical in found: continue
            key = pattern.split("，")[0].split("（")[0]
            idx = content.find(key)
            if idx < 0: continue
            snippet = content[idx+len(key): idx+60].strip()
            snippet = re.sub(r"[\\n\\r]+", "，", snippet)
            snippet = re.sub(r"，+，", "，", snippet)
            snippet = re.sub(r"\\s+", " ", snippet).strip()
            m2 = re.search(r"[。！？?！]", snippet)
            if m2: snippet = snippet[:m2.end()]
            snippet = snippet.strip("。，、：：「」\\"''()（）　 ")
            if len(snippet) < 4: continue
            found[canonical] = (pattern, snippet)
        if len(found) >= 5: break
    result = []
    for pattern, canonical in _DISH_PATTERNS:
        if canonical in found:
            result.append((found[canonical][0], found[canonical][1]))
    return result[:5]


def _rev_from_list(reviews):
    results = []; seen = set()
    for review in reviews:
        author  = review.get("author","")
        content = review.get("content","")
        if not content: continue
        for sent in re.split(r"[。\\n]", content):
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 80: continue
            if re.search(r"\$\\d+", sent): continue
            if sent in seen: continue
            seen.add(sent); results.append((author, sent)); break
        if len(results) >= 3: break
    if len(results) < 3:
        for review in reviews:
            content = review.get("content","")
            if not content: continue
            for sent in re.split(r"[。\\n]", content):
                sent = sent.strip()
                if len(sent) < 10 or len(sent) > 60: continue
                if re.search(r"\$\\d+", sent): continue
                if sent in seen: continue
                seen.add(sent); results.append((review.get("author",""), sent)); break
            if len(results) >= 3: break
    return [(a,n) for a,n in results if len(n) >= 10][:3]


'''

# 插入在 _get_reviews_from_api_data 或 format_full_output 之後
insert_targets = ["def _get_reviews_from_api_data", "def format_full_output"]
insert_pos = -1
for target in insert_targets:
    pos = c.rfind(target)
    if pos >= 0:
        m2 = re.search(r'\ndef ' + target[4:] + r'.*?(?=\n(?:def |class |# -{10}|\Z))', c[pos:], re.DOTALL)
        if m2:
            insert_pos = pos + m2.end()
            break

if insert_pos > 0:
    c = c[:insert_pos] + _dish_fn + c[insert_pos:]
    print("✅ 8. _dish_from_reviews + _rev_from_list 已插入")
else:
    print("❌ 8. 找不到插入點")

# ── 9. 更新 search_and_detail 中的呼叫 ──────────────────────
# 舊呼叫：detail_text = format_full_output(raw_output, api_data, food_kw, dist, i)
# 新呼叫：maps_price = _parse_maps_price_from_raw(raw_out)
#         reviews = _get_reviews_from_api_data(api_data)
#         detail_text = format_full_output(api_data, maps_price, food_kw, dist, i, reviews)

old_call = '        detail_text = format_full_output(raw_output, api_data, food_kw, dist, i)'
new_call = '''        # CDP 每人消費解析
        maps_price = {"found": False, "price_range": "", "price_histogram": [], "service": []}
        if pid:
            _, raw_out = query_place_full(pid)
            maps_price = _parse_maps_price_from_raw(raw_out)
        reviews = _get_reviews_from_api_data(api_data) if api_data else []
        detail_text = format_full_output(api_data or {}, maps_price, food_kw, dist, i, reviews)'''

if old_call in c:
    c = c.replace(old_call, new_call, 1)
    print("✅ 9. search_and_detail 中的呼叫已更新")
else:
    print("⚠️ 9. 找不到舊呼叫（可能已更新）")

# ── 10. 更新抬頭格式 ──────────────────────────────────────────
old_header_lines = [
    '    lines.append("=" * 54)',
    '    lines.append("\\uD83D\\uDCCD 搜尋條件")',
]
new_header_lines = '''    lines.append(f"+{"-" * 56}+")
    lines.append(f"|{"🍽️  {keyword} 選 項  🍽️".center(56)}|")
    lines.append(f"+{"-" * 56}+")
    lines.append("")
    lines.append(f"  📍 條件  {keyword}")
    lines.append(f"  📏 範圍  ({lat:.4f}, {lng:.4f}) 半徑 {r_display} {rh_display}")
    lines.append(f"  📊 排序  評分 ≥ {min_rating}，由近到遠")
    lines.append(f"  🔍 搜尋  共 {len(candidates)} 家候選，擴張半徑：{expansion_log[-1] if expansion_log else radius_m}")
    lines.append("")'''

# 找並取代抬頭建立處
old_h = '    lines.append("=" * 54)\\n    lines.append("📍 搜尋條件")'
if old_h in c:
    c = c.replace(old_h, new_header_lines.replace('\\n', '\n'), 1)
    print("✅ 10. 抬頭格式已更新")
else:
    # 找實際內容
    idx = c.find('    lines.append("=" * 54)')
    if idx >= 0:
        print(f"  找到 lines.append at {idx}，手動置換")
        c = c[:idx] + new_header_lines.replace('\\n', '\n') + c[c.find('\n', idx+10):]
        print("✅ 10. 抬頭已替換")

# 寫入
with open(DST, "w", encoding="utf-8") as f:
    f.write(c)

# 驗證
try:
    ast.parse(c)
    print(f"✅ 語法正確，總行數: {len(c.splitlines())}")
except SyntaxError as e:
    print(f"❌ 語法錯誤 line {e.lineno}: {e}")
    sys.exit(1)
