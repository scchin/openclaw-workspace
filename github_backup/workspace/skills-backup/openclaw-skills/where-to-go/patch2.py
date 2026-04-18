#!/usr/bin/env python3
"""補丁2：重寫 format_full_output 為新版卡片格式"""
import re, ast, sys

PATH = "/Users/KS/.openclaw/skills/where-to-go/scripts/run.py"

with open(PATH, encoding="utf-8") as f:
    c = f.read()

print(f"行數: {len(c.splitlines())}")

# ── 新的 format_full_output 函式 ─────────────────────────────
NEW_FORMAT_FULL = '''
def format_full_output(place_data: dict, maps_price: dict,
                       food_kw: Optional[str], dist_m: float,
                       index: int, reviews: list = None) -> str:
    """
    新版卡片格式（2026-03-23）：每個資訊一行，| 開頭為獨立區塊。
    """
    medal = ["\\uD83C\\uDFC6", "\\uD83E\\uDD48", "\\uD83C\\uDFC9", "4\\uFE0F\\u20E3", "5\\uFE0F\\u20E3"]

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

    # 距離進度條（固定 max_dist=3000m 為基準）
    drv = estimate_time(dist_m, "driving")
    wal = estimate_time(dist_m, "walking")
    max_dist = 3000
    bar_w = min(10, max(1, int(dist_m / max_dist * 10))) if max_dist > 0 else 5
    bar = "\\u2593" * bar_w + "\\u2591" * (10 - bar_w)

    icon = "\\u2705" if open_now else "\\u274C"
    txt  = "營業中" if open_now else "休息中"

    lines = []
    food_tag = f"\\uff08\\u2661\\u98df\\u54c1\\u7b26\\u5408\\uff1a{food_kw}\\uff09" if food_kw else ""

    lines.append(f"  {medal[index]} +{'-' * 50}")
    lines.append(f"    | {name}{food_tag}")
    lines.append(f"    | \\u2B50 {rating}\\uff08{rcount}\\u5249\\uff09")
    lines.append(f"    | {bar}")
    lines.append(f"    | \\uD83D\\uDE97{drv}\\u5206 \\uD83D\\uDEB6{wal}\\u5206")
    lines.append(f"    | {icon} {txt}")

    if address and address != "無地址":
        lines.append(f"    | \\uD83D\\uDCCD {address}")
    if phone and phone != "無":
        lines.append(f"    | \\uD83D\\uDCDE {phone}")

    if price_rng:
        lines.append(f"    | \\uD83D\\uDCB5 {price_rng}")
    elif price_hist:
        for lbl, cnt, pct in price_hist:
            bar2 = "\\u2593" * max(1, int(pct / 10)) + "\\u2591" * (10 - max(1, int(pct / 10)))
            lines.append(f"    | \\uD83D\\uDCB5 {lbl}")
            lines.append(f"    |   {bar2}  {cnt}\\uff08{pct}\\u2030\\uff09")

    if svcs:
        lines.append(f"    | \\uD83D\\uDCCC {'\\u3001'.join(svcs)}")

    # 特色菜色
    dish_list = _dish_from_reviews(reviews or [])
    if dish_list:
        seen = set()
        for dname, snippet in dish_list:
            if dname not in seen:
                seen.add(dname)
                s2 = snippet[:80] + "..." if len(snippet) > 80 else snippet
                lines.append(f"    | \\uD83C\\uDF74 {dname}\\uff1a{s2}")
        if not seen:
            lines.append(f"    | \\uD83C\\uDF74 \\u7121\\uff08\\u6700\\u8FD1\\u8A0A\\u8AD6\\u4E2D\\u672A\\u62A5\\u7A2E\\u7279\\u5B9A\\u83D8\\u8272\\uff09")
    else:
        lines.append(f"    | \\uD83C\\uDF74 \\u7121\\uff08\\u6700\\u8FD1\\u8A0A\\u8AD6\\u4E2D\\u672A\\u62A5\\u7A2E\\u7279\\u5B9A\\u83D8\\u8272\\uff09")

    # 網友心得
    rev_list = _rev_from_list(reviews or [])
    if rev_list:
        for author, note in rev_list[:3]:
            n2 = note[:60] + "..." if len(note) > 60 else note
            lines.append(f"    | \\uD83D\\uDC64 {author}\\uff1a{n2}")
    else:
        lines.append(f"    | \\uD83D\\uDC64 \\u7121\\uff08\\u6700\\u8FD1\\u7121\\u8A0A\\u8AD6\\uff09")

    if maps_url:
        lines.append(f"    | \\uD83D\\uDDFA {maps_url}")

    lines.append(f"    +{'-' * 50}")

    return "\\n".join(lines)

'''

# ── 找並取代舊的 format_full_output ─────────────────────────
# 用正则匹配整個函式（到下一個頂層定義為止）
pattern = r'\ndef format_full_output\([^)]*\)[^:]*:.*?(?=\n(?:def |class |# ---|\Z))'
match = re.search(pattern, c, re.DOTALL)
if match:
    print(f"找到舊 format_full_output，長度 {len(match.group())} 字元")
    c = c[:match.start()] + NEW_FORMAT_FULL.strip() + c[match.end():]
    print("✅ 已替換 format_full_output")
else:
    print("❌ 找不到 format_full_output")
    sys.exit(1)

try:
    ast.parse(c)
    print("✅ 語法正確")
except SyntaxError as e:
    print(f"❌ 語法錯誤：{e}")
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(c)

print(f"✅ 寫入成功，行數: {len(c.splitlines())}")
