#!/usr/bin/env python3
"""
where-to-go 完整執行腳本 v2.12（2026-03-24）
整合 Step 2→3→4→5：搜尋 → 過濾排序 → 詳細查詢 → 輸出完整結果

更新：
- 2026-03-24 v2.11：評論移除 textwrap.fill 自動換行，保持原文完整；新增「價格留言」專區，
  智慧解析產品名/份量/價格並顯示發布時間（多久以前）；_rev_from_list 回傳 days_ago
- 2026-03-24 v2.10：Header 移除多餘 \n，消滅兩行空白；版本同步更新至 v2.10
- 2026-03-24 v2.9：🍜 熱門品項從 CDP popular_items 解析並新增該欄位
- 2026-03-24 v2.8：Phase 3 無條件執行（平均每人分布圖）、Chrome CDP profile 自動複製（已登入）
- 2026-03-24 v2.7：🚗開車/🚶走路合併一行 + 💵每人消費欄位
- 2026-03-24 v2.6：評論超過52字自動換行（textwrap.fill width=52）
- 2026-03-23 v2.5：純文字模板輸出（符合 MEMORY.md v2.5 格式）
- 2026-03-23：冰品關鍵字擴張（冰品、冰店、雪花冰、芒果冰、豆花、仙草、芋圓、
              甜湯、甜品、燒仙草、愛玉、杏仁豆腐、楊枝甘露等）
- 自動對每個候選地點呼叫『Google Places 地點查詢技能』（query.py full）
- 食物關鍵字會過濾店家的說明、評論、特色菜色，只有提到該食物的店家才入選
"""
import subprocess
import json
import sys
import os
import re
import math
import time
import textwrap
import asyncio
from typing import List, Dict, Optional, Tuple

# --- 設定 ----------------------------------------------------
DEFAULT_LAT = 24.18588146738243
DEFAULT_LNG = 120.66765935832942
DEFAULT_RADIUS_M = 1000
DEFAULT_MIN_RATING = 4.5
DEFAULT_MAX_RESULTS = 5
DEFAULT_MAX_CANDIDATES = 30   # 先多抓一些，食物關鍵字會過濾掉部分
REV_COUNT = 6                  # 每家店預設抓幾則評論

EXPANSION_RADII = [1000, 1500, 2500, 5000, 10000, 20000, 50000]

# -------------------------------------------------------------
# In-memory cache（同一程序內重複查詢加速）
# -------------------------------------------------------------
_QUERY_API_CACHE: Dict[str, Optional[dict]] = {}
_QUERY_FULL_CACHE: Dict[str, str] = {}

# -------------------------------------------------------------
# 觸發關鍵字
# -------------------------------------------------------------

# 餐飲時段 / 業態關鍵字（原有）
MEAL_KEYWORDS = [
    "早餐", "午餐", "晚餐", "宵夜", "下午茶", "點心",
    "麵包", "小吃", "夜市", "餐館", "飯店",
]

# 設施關鍵字（原有）
FACILITY_KEYWORDS = [
    "廁所", "加油站", "停車場",
]

# 設施/地點擴充關鍵字（對應 MEMORY.md 地點查詢天條）
PLACE_KEYWORDS = [
    "美術館", "博物館", "展覽館", "展場",
    "旅館", "民宿", "青年旅舍",
    "圖書館",
    "公園", "景點", "學校",
]

# 食物關鍵字（2026-03-22 新增）
FOOD_KEYWORDS = [
    # 類型
    "火鍋", "壽司", "合菜", "快炒", "素食", "港式", "飲茶",
    "燒肉", "燒烤", "碳烤", "牛排", "炸物", "披薩", "義大利麵",
    "咖哩", "拉麵", "烏龍麵", "牛肉麵", "蚵仔煎", "肉圓",
    "滷肉飯", "雞腿飯", "便當", "自助餐", "buffet",
    "冰", "早午餐", "brunch", "咖啡", "甜點", "蛋糕", "冰淇淋",
    "剉冰", "豆花", "仙草", "芋圓",
    # 冰品同義擴張（2026-03-23）
    "冰品", "冰店", "雪花冰", "芒果冰", "豆花", "仙草凍",
    "芋圓", "地瓜圓", "湯圓", "米苔目", "愛玉", "石花凍",
    "杏仁豆腐", "米糕粥", "甜湯", "甜品", "涼茶", "青草茶",
    "楊枝甘露", "燒仙草", "冰剉冰", "傳統冰",
    "手搖", "珍奶", "飲料", "奶茶", "果昔",
    "居酒屋", "小吃", "鹹酥雞", "滷味", "關東煮",
    "水煎包", "蔥油餅", "蛋餅", "吐司", "三明治",
    "Pizza", "pizza", "漢堡", "薯條", "炸雞",
    "泰式", "日式", "韓式", "越式", "印度料理",
    "法式", "義式", "美式", "德式", "墨西哥",
    "海鮮", "生魚片", "烤魚", "龍蝦", "螃蟹",
    "藥膳", "麻油雞", "羊肉爐", "薑母鴨", "臭豆腐",
    "鍋貼", "水餃", "小籠包", "餛飩", "麵食",
    "粥", "飯糰", "碗粿", "肉粽", "蚵仔麵線",
    "吐司", "比司吉", "可頌", "司康", "馬芬",
    "甜甜圈", "泡芙", "提拉米蘇", "慕斯", "巧克力",
]

TRIGGER_KEYWORDS = MEAL_KEYWORDS + FACILITY_KEYWORDS + PLACE_KEYWORDS + FOOD_KEYWORDS

SKIP_KEYWORDS = ["哪裡", "什麼", "怎麼", "如何", "為什麼", "教", "學", "做"]


# -------------------------------------------------------------
# 工具函式
# -------------------------------------------------------------

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def is_open(data: dict) -> bool:
    if "open_now" in data: return bool(data["open_now"])
    if "openNow" in data: return bool(data["openNow"])
    try:
        hours = data.get("currentOpeningHours", {})
        if "currentOperatingHours" in hours: return hours["currentOperatingHours"].get("openNow", False)
        if "regularHours" in hours: return hours["regularHours"][0].get("openNow", False)
        return hours.get("openNow", False)
    except Exception:
        pass
    return False


def is_permanently_closed(data: dict) -> bool:
    try:
        return data.get("businessStatus") == "CLOSED_PERMANENTLY"
    except Exception:
        return False


def normalize_status(data: dict) -> str:
    if is_permanently_closed(data): return "永久停業"
    if is_open(data): return "營業中"
    return "休息中"


def get_display_name(data: dict) -> str:
    return data.get("displayName", {}).get("text", data.get("name", "未知店家"))


def get_rating(data: dict) -> float:
    try: return float(data.get("rating", 0))
    except Exception: return 0.0


def get_address(data: dict) -> str:
    return data.get("formattedAddress", data.get("address", "無地址"))


def get_place_id(data: dict) -> str:
    return data.get("place_id", data.get("id", ""))


def estimate_time(dist_m: float, mode: str = "driving") -> int:
    if mode == "walking":
        return max(1, round(dist_m / 1000 / 5 * 60))
    return max(1, round(dist_m / 1000 / 20 * 60))


# -------------------------------------------------------------
# 關鍵字偵測
# -------------------------------------------------------------

def extract_keyword(text: str) -> Optional[str]:
    """抓第一個出現的觸發關鍵字"""
    for kw in TRIGGER_KEYWORDS:
        if kw in text:
            return kw
    return None


def is_food_keyword(kw: str) -> bool:
    return kw in FOOD_KEYWORDS


def extract_food_keyword(text: str) -> Optional[str]:
    """從文字中找出食物關鍵字（用於過濾評論）"""
    for kw in FOOD_KEYWORDS:
        if kw in text:
            return kw
    return None


# -------------------------------------------------------------
# 食物過濾器
# -------------------------------------------------------------

FOOD_ALIASES = {
    "火鍋": ["火鍋", "涮涮鍋", "麻辣鍋", "石頭火鍋", "羊肉爐", "薑母鴨", "鍋物"],
    "壽司": ["壽司", "生魚片", "握壽司", "炙燒", "巻き", "花壽司", "手卷"],
    "合菜": ["合菜", "桌菜", "辦桌", "套餐", "客家菜", "台菜", "中式料理"],
    "快炒": ["快炒", "熱炒", "台式", "家常菜"],
    "素食": ["素食", "蔬食", "素食餐", "vegetarian", "Vegan"],
    "港式": ["港式", "港點", "茶餐廳", "燒臘", "腸粉", "叉燒", "流沙包", "蝦餃", "燒賣"],
    "飲茶": ["飲茶", "港式飲茶", "點心", "小點"],
    "燒肉": ["燒肉", "烤肉", "和牛", "韓式燒肉", "牛角燒肉"],
    "牛排": ["牛排", "排餐", "steak", "肋眼", "菲力", "沙朗"],
    "披薩": ["披薩", "pizza", "義式", "瑪格麗特"],
    "義大利麵": ["義大利麵", "pasta", "義麵", "番茄麵", "奶油麵"],
    "咖哩": ["咖哩", "curry", "印度咖哩", "日式咖哩"],
    "拉麵": ["拉麵", "ramen", "豚骨", "醬油拉麵", "味噌拉麵"],
    "早午餐": ["早午餐", "brunch", "brunch店"],
    "咖啡": ["咖啡", "cafe", "coffee", "拿鐵", "卡布奇諾", "espresso"],
    "甜點": ["甜點", "dessert", "蛋糕", " pastry", "法式甜點", "千層"],
    "海鮮": ["海鮮", "現流", "活凍", "龍蝦", "螃蟹", "蛤蜊", "鮮魚"],
    "日本料理": ["日本料理", "日式", "和風", "居酒屋", "和民"],
    "韓式": ["韓式", "韓國料理", "烤肉", "石鍋", "拌飯", "泡菜", "韓鍋"],
    "泰式": ["泰式", "泰國料理", "酸辣", "冬蔭功", "月亮蝦餅"],
    "吃到飽": ["吃到飽", "buffet", "自助餐", "all you can eat", "燒烤吃到飽"],
}

# 所有食物關鍵字（含別名）用於正則建表
ALL_FOOD_TERMS: List[str] = list(FOOD_KEYWORDS)
for aliases in FOOD_ALIASES.values():
    ALL_FOOD_TERMS.extend(aliases)
# 去重
seen, ALL_FOOD_TERMS = set(), []
for t in FOOD_KEYWORDS + [a for als in FOOD_ALIASES.values() for a in als]:
    if t not in seen:
        seen.add(t)
        ALL_FOOD_TERMS.append(t)

# 建立正則（依長度降冪，避免短詞先匹配長詞）
FOOD_PATTERN = re.compile(
    "|".join(sorted((re.escape(t) for t in ALL_FOOD_TERMS), key=len, reverse=True)),
    re.IGNORECASE
)


def matches_food_keyword(text: str, food_kw: str) -> bool:
    """檢查文字中是否有某食物關鍵字的提及"""
    if not text:
        return False
    text_lower = text.lower()
    # 先看直接關鍵字
    if food_kw.lower() in text_lower:
        return True
    # 再看別名
    aliases = FOOD_ALIASES.get(food_kw, [])
    for alias in aliases:
        if alias.lower() in text_lower:
            return True
    return False


def place_mentions_food(place_data: dict, food_kw: str) -> bool:
    """
    檢查店家資料中是否提到某食物關鍵字。
    掃描範圍：名稱 + 類型 + 說明 + 熱門品項 + 6個月內評論文字。
    只要任一則提到就回傳 True。
    """
    # 1. 名稱
    name = place_data.get("name", "")
    if matches_food_keyword(name, food_kw):
        return True

    # 2. 類型（types / category）
    types = place_data.get("types", [])
    if isinstance(types, list):
        types_text = " ".join(str(t) for t in types)
        if matches_food_keyword(types_text, food_kw):
            return True

    # 3. 說明（editorialSummary / description）
    desc = (
        place_data.get("editorialSummary", {})
        or place_data.get("description", "")
        or place_data.get("about", [])
    )
    if isinstance(desc, dict):
        desc = desc.get("text", "")
    if matches_food_keyword(str(desc), food_kw):
        return True

    # 4. 熱門品項（popular_items from CDP，或 API 的 dishes/overview）
    popular = place_data.get("popular_items", [])
    if isinstance(popular, list):
        for item in popular:
            if matches_food_keyword(str(item), food_kw):
                return True

    # 5. 6個月內評論
    reviews = place_data.get("_filtered_reviews", [])
    if not reviews:
        reviews = place_data.get("reviews", [])
    for rev in reviews:
        # 原文優先
        orig = rev.get("original_text", {})
        if isinstance(orig, dict):
            content = orig.get("text", "")
        else:
            content = str(rev.get("content", rev.get("text", "")))
        if matches_food_keyword(content, food_kw):
            return True
        # 翻譯文字
        trans = rev.get("text", {})
        if isinstance(trans, dict):
            trans_text = trans.get("text", "")
        else:
            trans_text = str(rev.get("text", ""))
        if matches_food_keyword(trans_text, food_kw):
            return True

    return False


# -------------------------------------------------------------
# goplaces search
# -------------------------------------------------------------

def goplaces_search(keyword: str, lat: float, lng: float,
                    radius_m: int, min_rating: float,
                    max_results: int = DEFAULT_MAX_CANDIDATES) -> List[dict]:
    env = os.environ.copy()
    work_dir = os.path.expanduser("~/.openclaw/skills/google-places")
    args = [
        "goplaces", "search", keyword,
        "--lat", str(lat), "--lng", str(lng),
        "--radius-m", str(radius_m),
        "--open-now", "--min-rating", str(min_rating),
        "--limit", str(min(max_results, 20)), "--json",  # goplaces 上限 20
    ]
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                          env=env, timeout=30, cwd=work_dir)
        out = r.stdout + r.stderr
        all_lines = out.split("\n")
        json_end_idx = None
        for j in range(len(all_lines) - 2, -1, -1):
            if all_lines[j].strip() == "]":
                json_end_idx = j
                break
        if json_end_idx is not None:
            json_text = "\n".join(all_lines[:json_end_idx + 1])
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"[goplaces search 錯誤] {e}", file=sys.stderr)
    return []


# -------------------------------------------------------------
# filter + sort
# -------------------------------------------------------------

def filter_and_sort(candidates: List[dict],
                    center_lat: float, center_lng: float,
                    min_rating: float) -> List[dict]:
    filtered = []
    for c in candidates:
        if is_permanently_closed(c): continue
        if get_rating(c) < min_rating: continue
        lat = c.get("location", {}).get("lat", 0)
        lng = c.get("location", {}).get("lng", 0)
        dist = haversine(center_lat, center_lng, lat, lng)
        c["_distance_m"] = dist
        filtered.append(c)
    filtered.sort(key=lambda x: x["_distance_m"])
    return filtered


# -------------------------------------------------------------
# Google Places 地點查詢技能（query.py full）
# -------------------------------------------------------------

def query_place_full(place_id: str) -> Tuple[Optional[dict], str]:
    """
    呼叫『Google Places 地點查詢技能』的 query.py full。
    回傳 (structured_data, raw_text_output)
    """
    if place_id in _QUERY_FULL_CACHE:
        return None, _QUERY_FULL_CACHE[place_id]

    script = os.path.expanduser("~/.openclaw/skills/google-places/scripts/query.py")
    try:
        r = subprocess.run(
            ["python3", script, "full", place_id],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=os.environ.copy(), timeout=90
        )
        raw = r.stdout
        # query.py full 輸出結果，去掉 [CDP] debug lines
        clean_lines = []
        for line in raw.split("\n"):
            stripped = line.strip()
            # 跳過 CDP debug 行、空行、Phase 行
            if stripped.startswith("[CDP]") or stripped.startswith("Phase ") \
               or stripped.startswith("state:") or stripped.startswith("stable ") \
               or stripped.startswith("[Phase") or stripped.startswith("done") \
               or stripped.startswith("result.") or stripped.startswith("hist=") \
               or stripped.startswith("Click ") or stripped.startswith("WS ") \
               or stripped.startswith("WS OK") or stripped.startswith("WS connected") \
               or stripped.startswith("Tab ") or stripped.startswith("Tab clicked") \
               or stripped == "" or "polling" in stripped:
                continue
            clean_lines.append(line)
        clean_raw = "\n".join(clean_lines)
        # 寫入 cache（供同一程序內重複使用）
        _QUERY_FULL_CACHE[place_id] = clean_raw
        # 嘗試解析結構成 dict（供食物過濾用）
        structured = _parse_query_full_output(clean_raw, place_id)
        return structured, clean_raw
    except Exception as e:
        return None, f"[錯誤] {e}"


def _parse_query_full_output(raw: str, place_id: str) -> Optional[dict]:
    """
    從 query.py full 的純文字輸出中，
    擷取可用於食物關鍵字過濾的結構化欄位。
    主要靠 goplaces API 本身。
    """
    # goplaces details 已能還原大部分欄位，直接用另一支 function
    return query_place_api_only(place_id)


def query_place_api_only(place_id: str) -> Optional[dict]:
    """只透過 goplaces details + priceRange API 取結構化資料（附 cache）"""
    if place_id in _QUERY_API_CACHE:
        return _QUERY_API_CACHE[place_id]

    env = os.environ.copy()
    env["GOOGLE_PLACES_API_KEY"] = os.environ.get(
        "GOOGLE_PLACES_API_KEY", "[API_KEY_REDACTED]")

    args = ["goplaces", "details", place_id, "--reviews", "--json"]
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                          env=env, timeout=30,
                          cwd=os.path.expanduser("~/.openclaw/skills/google-places"))
        out = r.stdout.strip()
        data = None
        for line in out.split("\n"):
            if line.strip().startswith("{"):
                try:
                    data = json.loads("\n".join(out.split("\n")[out.split("\n").index(line):]))
                    break
                except Exception:
                    pass
        if data is None:
            try:
                data = json.loads(out)
            except Exception:
                data = None
    except Exception:
        data = None

    # priceRange API
    price_range = None
    try:
        import urllib.request
        key = env["GOOGLE_PLACES_API_KEY"]
        url = (f"https://places.googleapis.com/v1/places/{place_id}"
               f"?fields=priceRange&key={key}")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            pr_data = json.loads(resp.read())
        pr = pr_data.get("priceRange")
        if pr:
            s = pr.get("startPrice", {}).get("units", "")
            e = pr.get("endPrice", {}).get("units", "")
            price_range = f"${s}–${e}" if s and e else None
    except Exception:
        pass

    if data:
        # priceRange API（v1 endpoint）SSL 失敗時，用 goplaces price_level 兜底
        # price_level: 1=$ | 2=$$ | 3=$$$ | 4=$$$$
        if not price_range:
            pl = data.get("price_level")
            if isinstance(pl, int) and pl >= 1:
                price_range = "$" * min(pl, 4)
        data["_price_range"] = price_range
        if "place_id" not in data and "id" in data:
            data["place_id"] = data["id"]
        # 只留6個月內評論（供食物過濾用）
        data["_filtered_reviews"] = _filter_reviews_6m(data.get("reviews", []))
    _QUERY_API_CACHE[place_id] = data
    return data


def _filter_reviews_6m(reviews: list) -> list:
    """過濾6個月內的評論（供食物關鍵字比對用）"""
    from datetime import datetime, timezone, timedelta
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    filtered = []
    for rev in reviews:
        pub_str = rev.get("publish_time", "")
        if not pub_str:
            continue
        try:
            pub_time = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            continue
        if pub_time < six_months_ago:
            continue
        filtered.append(rev)
    return filtered


# -------------------------------------------------------------
# v2.5 輸出格式（純文字模板，符合 MEMORY.md 規範）
# -------------------------------------------------------------


def format_full_output(place_data: dict, maps_price: dict,
                       food_kw: Optional[str], dist_m: float,
                       index: int, reviews: list = None,
                       price_range_api: str = "",
                       rev_count: int = REV_COUNT) -> str:
    """
    格式化單一店家輸出（純文字，每欄位一行）。
    輸出預設用於包在 Triple backticks（```）中呈現於 webchat。
    """
    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    medal_str = medal[index] if index < len(medal) else f"{index + 1}️⃣"

    name     = place_data.get("name", "未知店家") if place_data else "未知店家"
    pid      = place_data.get("place_id", "") if place_data else ""
    rating   = place_data.get("rating", 0) if place_data else 0
    rcount   = place_data.get("user_rating_count", 0) if place_data else 0
    phone    = place_data.get("phone", "") if place_data else ""
    open_now = place_data.get("open_now") if place_data else None
    svcs     = maps_price.get("service", [])
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""

    drv = estimate_time(dist_m, "driving")
    wal = estimate_time(dist_m, "walking")
    max_dist = 3000
    bar_w = min(10, max(1, int(dist_m / max_dist * 10))) if max_dist > 0 else 5
    bar = "▓" * bar_w + "░" * (10 - bar_w)

    status_icon  = "✅"
    status_txt   = "營業中"
    status_extra = ""
    if maps_price.get("status_line"):
        sl = maps_price["status_line"]
        # status_line 格式：「✅ 營業中（今日...）」或「❌ 休息中（...）」
        m2 = re.search(r"^([✅❌])\s*([^\s（\(]+)\s*[（\(](.+?)[）\)]$", sl)
        if m2:
            status_icon = m2.group(1)
            status_txt  = m2.group(2)
            status_extra = "（" + m2.group(3) + "）"
        else:
            # fallback：只抓 emoji 與括號內文
            m3 = re.search(r"^([✅❌])", sl)
            m4 = re.search(r"[（\(]([^）\)]+)[）\)]$", sl)
            if m3:
                status_icon = m3.group(1)
            if m4:
                status_txt  = sl[len(status_icon):].strip().split("（")[0].strip() if len(sl) > len(status_icon) else "營業中"
                status_extra = "（" + m4.group(1) + "）"
    elif open_now is not None:
        status_icon = "✅" if open_now else "❌"
        status_txt  = "營業中" if open_now else "休息中"

    svcs_list = [s.strip() for s in svcs] if svcs else []

    phone_str = f"📞 電話：{phone}" if phone else ""
    svcs_str  = f"📌 服務：{'、'.join(svcs_list)}" if svcs_list else ""

    # ★★★ 特色菜色（v2.5 新增）★★★
    # _dish_from_reviews 回傳 List[(pattern, snippet)]，pattern=菜色名，snippet=評論片段
    dish_items = []
    if reviews:
        dish_raw = _dish_from_reviews(reviews)
        if dish_raw:
            dish_items = [d[0] for d in dish_raw[:5]]  # d[0]=pattern=菜色名稱
    dish_str = "｜".join(dish_items) if dish_items else ""

    # ★★★ 熱門品項（v2.9 新增，從 CDP popular_items）★★★
    # popular_items 格式：["空間（7則）", "調酒（7則）"] 或 ["空間", "調酒"]
    # 先從 maps_price 拿，沒有則從 place_data 的 _popular_items 拿
    pop_items_raw: list = maps_price.get("popular_items", []) if maps_price else []
    if not pop_items_raw:
        pop_items_raw = place_data.get("_popular_items", []) if place_data else []
    if pop_items_raw:
        # 從完整 aria-label 抽出品項名（格式如「空間，7則評論」或「空間」）
        pop_cleaned = []
        for item in pop_items_raw:
            item_str = str(item).strip()
            m = re.search(r"^(.+?)(?:[,\s]+\d+\s*則)?[評論提到]*$", item_str)
            label = m.group(1).strip() if m else item_str
            if label and label not in pop_cleaned:
                pop_cleaned.append(label)
        pop_str = "｜".join(pop_cleaned[:6]) if pop_cleaned else ""
    else:
        pop_str = ""
    pop_line = f"  🍜 熱門：{pop_str}" if pop_str else ""

    # ★★★ 評論（最多3則，無自動換行，保持原文完整）★★★
    rev_list = _rev_from_list(reviews or [], rev_count)
    if rev_list:
        rev_lines = []
        for author, note, days_ago in rev_list:
            time_str = _days_ago_str(days_ago)
            rev_lines.append(f"  👤 {author}：{note} {time_str}")
    else:
        rev_lines = [f"  👤 無（近期評論中未抓獲特定菜色）"]

    # ★★★ v2.6 純文字模板（每一個欄位獨立一行）★★★
    lines_out: List[str] = []
    lines_out.append(f"• {medal_str} {name}")

    lines_out.append(f"  ⭐ 評分：{rating}（{rcount}則）")
    lines_out.append(f"  📊 熱度：{bar}")
    lines_out.append(f"  🚗 開車：{drv}分｜🚶 走路：{wal}分")
    lines_out.append(f"  {status_icon} {status_txt}{status_extra}")

    # ★★★ 每人消費（v2.7 新增，v2.9 支援 API priceRange）★★★
    price_val = ""
    if price_range_api and price_range_api not in ("無", "店家未提供", "無法讀取"):
        # ① Google Places API priceRange（最準確）優先
        price_val = price_range_api
    elif maps_price.get("found") and maps_price.get("price_range"):
        # ② CDP 有找到
        price_val = maps_price.get("price_range") or ""
    elif maps_price.get("price_range") and maps_price.get("price_range") not in ("無", "店家未提供", "無法讀取"):
        # ③ CDP fallback
        price_val = maps_price.get("price_range")
    elif reviews:
        # ④ 從評論中提取價格（價格關鍵字：$數字、每人$數字、+數字元）
        import re as _re
        _price_re = _re.compile(
            r"(?:每人|per person|人均)[\s:：]*\$?(\d+)|"
            r"\$\d+(?:\.\d{2})?|"
            r"[+＋]\s*\$?(\d+)\s*元|"
            r"(\d+)\s*元(?:\s*[/人每位])?"
        )
        _all_prices = []
        for rev in (reviews or []):
            _content = rev.get("content", "")
            if not _content:
                continue
            for _m in _price_re.finditer(_content):
                _v = next((g for g in _m.groups() if g), "")
                if _v and 10 <= int(_v) <= 10000:
                    _all_prices.append(int(_v))
        if _all_prices:
            _unique = sorted(set(_all_prices))
            if len(_unique) == 1:
                price_val = f"${_unique[0]}"
            else:
                price_val = f"${_unique[0]}–${_unique[-1]}"
    # 無論如何一定顯示該欄位（v2.7 鐵律）
    lines_out.append(f"  💵 每人：{price_val if price_val else "無"}")

    if phone_str:
        lines_out.append(f"  {phone_str}")
    if svcs_str:
        lines_out.append(f"  {svcs_str}")
    # 特色菜色一定出現（v2.6鐵律）
    if dish_str:
        lines_out.append(f"  🍴 特色：{dish_str}")
    else:
        lines_out.append(f"  🍴 特色：無（近期評論中未抓獲特定菜色）")
    # 熱門品項（v2.9 新增）
    if pop_line:
        lines_out.append(pop_line)
    # 評論（一般，無自動換行）
    lines_out.extend(rev_lines)

    # ★★★ 價格留言（v2.11 新增，專門抓有提到價格的評論）★★★
    price_rev_list = _price_rev_from_list(reviews or [], rev_count)
    if price_rev_list:
        for author, full_sent, product, portion, price_str, days_ago in price_rev_list:
            time_str = _days_ago_str(days_ago)
            # 組合呈現：🍴品項  💰價格  👤留言  時間
            segment = f"  🍴 {product}" if product != "（未識別品項）" else ""
            if portion:
                segment += f"（{portion}）" if segment else f"  🍴（{portion}）"
            if price_str:
                segment += f"  💰 {price_str}"
            segment += f"\n  👤 {author}：{full_sent} {time_str}"
            lines_out.append(segment)

    # Google Maps 連結
    if maps_url:
        lines_out.append(f"  🗺️ 地圖：{maps_url}")
    # 末尾雙橫線
    lines_out.append("  ──")

    return "\n".join(lines_out)

# -------------------------------------------------------------
# 解析使用者輸入
# -------------------------------------------------------------

def parse_input(user_text: str) -> Dict:
    text = user_text.strip()

    # 1. 抓觸發關鍵字（第一個出現的）
    keyword = extract_keyword(text)
    if not keyword:
        return {}

    # 2. 食物關鍵字（用於過濾）
    food_kw = extract_food_keyword(text)

    # 3. 找經緯度
    lat, lng = DEFAULT_LAT, DEFAULT_LNG
    coord_match = re.search(r"([-+]?\d+\.\d+)[,，]\s*([-+]?\d+\.\d+)", text)
    if coord_match:
        lat, lng = float(coord_match.group(1)), float(coord_match.group(2))

    # 4. 半徑
    radius_m = DEFAULT_RADIUS_M
    radius_hint = ""

    drv = re.search(r"開車\s*(\d+)\s*(分|分鐘|min)", text)
    if drv:
        radius_m = 500 * int(drv.group(1))
        radius_hint = f"開車{drv.group(1)}分"

    wal = re.search(r"走路\s*(\d+)\s*(分|分鐘|min)", text)
    if wal:
        radius_m = 80 * int(wal.group(1))
        radius_hint = f"走路{wal.group(1)}分"

    m_match = re.search(r"(\d+)\s*m\b", text, re.IGNORECASE)
    if m_match:
        radius_m = int(m_match.group(1))
        radius_hint = f"{radius_m}m"

    km_match = re.search(r"([\d.]+)\s*km\b", text, re.IGNORECASE)
    if km_match:
        radius_m = int(float(km_match.group(1)) * 1000)
        radius_hint = f"{km_match.group(1)}km"

    radius_patterns = [
        r"(?:半徑|方圓|範圍|周圍|附近)[^\d]*(\d+)\s*m\b",
        r"(\d+)\s*m(?:半徑|範圍|內|以內)",
    ]
    for pat in radius_patterns:
        rm = re.search(pat, text, re.IGNORECASE)
        if rm:
            radius_m = int(rm.group(1))
            radius_hint = f"{radius_m}m"
            break

    # 5. 評分
    min_rating = DEFAULT_MIN_RATING
    # 食物類型：跳過評分門檻，改為取評分最高的5家
    if is_food_keyword(keyword):
        min_rating = DEFAULT_MIN_RATING  # 食物類：API 取够多候選，後面再重排
    rating_match = re.search(r"(\d+\.?\d*)\s*(?:分|星|評分|rating)\s*(?:以上|以?|greater)", text)
    if rating_match:
        min_rating = float(rating_match.group(1))

    # 6. 數量
    max_results = DEFAULT_MAX_RESULTS
    count_match = re.search(r"(\d+)\s*(?:家|間|個|筆|結果)", text)
    if count_match:
        max_results = int(count_match.group(1))

    # 7. 評論數
    rev_count = REV_COUNT
    rev_match = re.search(r"--reviews[=：]?\s*(\d+)", text)
    if rev_match:
        rev_count = int(rev_match.group(1))

    return {
        "keyword": keyword,
        "food_kw": food_kw,
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "radius_hint": radius_hint,
        "min_rating": min_rating,
        "max_results": max_results,
        "rev_count": rev_count,
    }


# -------------------------------------------------------------
# 主搜尋流程
# -------------------------------------------------------------

def search_and_detail(params: Dict, verbose: bool = True) -> str:
    keyword   = params["keyword"]
    food_kw   = params["food_kw"]       # 可能為 None
    lat       = params["lat"]
    lng       = params["lng"]
    radius_m  = params["radius_m"]
    radius_hint = params["radius_hint"]
    min_rating = params["min_rating"]
    max_results = params["max_results"]
    rev_count = params.get("rev_count", REV_COUNT)

    expansion_log: List[int] = []
    candidates: List[dict] = []
    final_radius = radius_m

    # -- Step 2: 半徑擴張搜尋 --
    for radius in EXPANSION_RADII:
        if radius < radius_m: continue
        final_radius = radius
        expansion_log.append(radius)

        results = goplaces_search(keyword, lat, lng, radius, min_rating)
        if isinstance(results, list):
            candidates = results
        elif isinstance(results, dict) and "places" in results:
            candidates = results["places"]
        else:
            candidates = []

        if len(candidates) >= max_results:
            break
        if radius >= 50000:
            break

    # -- Step 3: 過濾 + 排序 --
    filtered = filter_and_sort(candidates, lat, lng, min_rating)

    # -- 食物關鍵字過濾（★★★ 新增邏輯） --
    if food_kw and filtered:
        food_filtered: List[dict] = []
        skipped_count = 0
        for place in filtered:
            pid = get_place_id(place)
            if not pid:
                skipped_count += 1
                continue
            # 取結構化資料（API 評論），供食物比對
            api_data = query_place_api_only(pid)
            if api_data and place_mentions_food(api_data, food_kw):
                place["_api_data"] = api_data   # 快取，避免重複呼叫
                food_filtered.append(place)
            else:
                skipped_count += 1

        # 若過濾後不夠5家，則放寬門檻（取原本過濾結果）
        if len(food_filtered) < max_results:
            # 把被跳過的加回來補足數量
            for place in filtered:
                if place not in food_filtered:
                    place["_api_data"] = place.get("_api_data")
                    food_filtered.append(place)
                    if len(food_filtered) >= max_results:
                        break

        filtered = food_filtered
        filter_note = f"（食物關鍵字「{food_kw}」過濾，跳過 {skipped_count} 家不符）"
    else:
        filter_note = ""

    # -- Step 4: 取評分最高的5家（候選選擇） --
    if is_food_keyword(params["keyword"]):
        filtered.sort(key=lambda x: get_rating(x), reverse=True)
        all_top = filtered[:DEFAULT_MAX_CANDIDATES]  # 多取幾家作為遞補池
        # ★★★ 確保全是營業中的（不足時從後面遞補）★★★
        open_ones, closed_ones = [], []
        for p in all_top:
            pid = get_place_id(p)
            api_d = p.get("_api_data") or (query_place_api_only(pid) if pid else None)
            is_open_now = api_d.get("open_now") if api_d else False
            if is_open_now:
                open_ones.append(p)
            else:
                closed_ones.append(p)
            if len(open_ones) >= DEFAULT_MAX_RESULTS:
                break
        # 若營業中不足5家，則用休息中的補足（使用者要求一定給5間）
        if len(open_ones) < DEFAULT_MAX_RESULTS:
            deficit = DEFAULT_MAX_RESULTS - len(open_ones)
            open_ones.extend(closed_ones[:deficit])
        top_results = open_ones
        filter_note = (filter_note + "（評分最高5家）").strip()
        # -- Step 5: 重新按距離由近到遠排列 --
        top_results.sort(key=lambda x: x.get("_distance_m", 999999))
    else:
        top_results = filtered[:max_results]

    # -- 輸出 Header --
    r_display = f"{final_radius // 1000}km" if final_radius >= 1000 else f"{final_radius}m"
    rh_display = f"（{radius_hint}）" if radius_hint else ""
    food_display = f"｜食物過濾：{food_kw}" if food_kw else ""

    lines: List[str] = []
    lines.append(f"## 🍽️  {keyword}  選 項")
    lines.append(f"📍 條件：{keyword}")
    lines.append(f"📏 範圍：({lat:.4f}, {lng:.4f}) 半徑 {r_display} {rh_display}")
    lines.append(f"📊 評分 ≥ {min_rating}")
    lines.append(f"🔍 共 {len(candidates)} 家候選")

    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    # -- Step 4: 對每個地點呼叫『Google Places 地點查詢技能』-
    for i, place in enumerate(top_results):
        pid  = get_place_id(place)
        dist = place.get("_distance_m", 0)

        if verbose:
            pass  # 靜默，不輸出查詢中提示（模板無此行）

        # 優先用已被食物過濾快取的 api_data，否則重新取
        api_data: Optional[dict] = place.get("_api_data")
        if api_data is None and pid:
            api_data = query_place_api_only(pid)

        # api_data 優先用 query_place_full 回的 structured（含 CDP 解析結果），
        # 若為 None 才另外呼叫 query_place_api_only（節省一次 goplaces call）
        structured: Optional[dict] = None
        if pid:
            structured, raw_output = query_place_full(pid)
            maps_price = _parse_maps_price_from_raw(raw_output)
        api_data = structured if structured else {}
        if not api_data and pid:
            api_data = query_place_api_only(pid)
        # api_data._price_range：来自 query_place_api_only() 内的 priceRange API（或 SSL fallback 到 price_level）
        price_range_api = (api_data or {}).get("_price_range") or ""
        reviews = _get_reviews_from_api_data(api_data) if api_data else []
        detail_text = format_full_output(api_data or {}, maps_price, food_kw, dist, i,
                                         reviews, price_range_api=price_range_api,
                                         rev_count=rev_count)
        lines.append(detail_text)

        if i < len(top_results) - 1:
            time.sleep(0.5)

    return "\n".join(lines)


def _parse_maps_price_from_raw(raw: str) -> dict:
    mp = {"found": False, "price_range": None, "reporter": None,
          "price_histogram": [], "service": [], "popular_items": [], "menu_url": None,
          "status_line": None}
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
    for line in raw.split("\n"):
        hm = re.search(r"\s*([▓░])\s+(\$[^\s]+)\s+(約\d+人)\s+（(\d+)%）", line)
        if hm:
            mp["price_histogram"].append([hm.group(2), hm.group(3), int(hm.group(4))])
    sm = re.search(r"📌\s*服務：([^\n]+)", raw)
    if sm:
        mp["service"] = [s.strip() for s in re.split(r"[、，]", sm.group(1)) if s.strip()]
    # ── 解析 🍜 熱門品項（query.py full 输出版） ────────────────────
    # 格式：🍜 熱門品項：空間（7則）｜調酒（7則）｜聚餐（4則）
    for line in raw.split("\n"):
        if "🍜 熱門品項：" in line:
            parts = line.split("🍜 熱門品項：", 1)[-1].strip().rstrip("─").strip()
            if parts and parts not in ("無", "未抓獲"):
                items = [s.strip() for s in re.split(r"[｜|]", parts) if s.strip()]
                mp["popular_items"] = items
            break
    # ── 解析 🚦 狀態行（query.py full 输出版） ──────────────────────
    # 格式示例：
    #   🚦 狀態：✅ 營業中（今日 10:30–21:30，約剩 1 小時 34 分）
    #   🚦 狀態：❌ 休息中（今日已打烊，明日 11:00 開門）
    #   🚦 狀態：✅ 營業中（今日 11:00–22:00）
    #   🚦 狀態：❌ 休息中（今日 21:00 恢復營業，約剩 2 小時）
    #   🚦 狀態：❌ 休息中（週一公休）
    for line in raw.split("\n"):
        if "🚦 狀態：" in line:
            # 去掉 🚦 標記，只留「✅ 營業中（...）」或「❌ 休息中（...）」
            st = line.split("🚦 狀態：", 1)[-1].strip()
            mp["status_line"] = st
            break
    return mp


def _get_reviews_from_api_data(api_data: dict) -> list:
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
            pub_time = now_utc; days_ago = 0
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


_DISH_PATTERNS = [
    # 台式/傳統小吃
    ("蝦滷飯","蝦滷飯"),("澎湖小卷","小卷"),("煎干貝","干貝"),("脆皮燒肉","燒肉"),
    ("辣椒","辣椒"),("海鮮炒麵","炒麵"),("海鮮粥","海鮮粥"),("油蔥蝦仁飯","油蔥蝦仁飯"),
    ("川燙花枝","花枝"),
    ("鐵板麵","鐵板麵"),("陽春麵","陽春麵"),("蛋餅","蛋餅"),("鍋貼","鍋貼"),
    ("水煎包","水煎包"),("蔥油餅","蔥油餅"),("餡餅","餡餅"),
    ("蘿蔔糕","蘿蔔糕"),("碗粿","碗粿"),("肉粽","肉粽"),("飯糰","飯糰"),
    ("蚵仔麵線","蚵仔麵線"),("麵線","麵線"),
    ("豆漿","豆漿"),("米漿","米漿"),("鹹豆漿","鹹豆漿"),("甜豆漿","甜豆漿"),
    ("燒餅","燒餅"),("油條","油條"),("水餃","水餃"),("肉圓","肉圓"),
    ("蚵仔煎","蚵仔煎"),("肉燥飯","肉燥飯"),("滷肉飯","滷肉飯"),("雞腿飯","雞腿飯"),
    ("便當","便當"),("自助餐","自助餐"),("素食","素食"),
    ("鹹酥雞","鹹酥雞"),("雞排","雞排"),("珍珠奶茶","珍奶"),("手搖飲","手搖飲"),
    ("大腸蚵仔麵線","大腸麵線"),
    # 港式飲茶
    ("燒賣","燒賣"),("蝦餃","蝦餃"),("蝦餃皇","蝦餃皇"),("叉燒包","叉燒包"),
    ("流沙包","流沙包"),("蛋撻","蛋撻"),("菠蘿包","菠蘿包"),("鮮蝦腸粉","腸粉"),
    ("牛肉丸","牛肉丸"),("蒸餃","蒸餃"),("小籠包","小籠包"),("腐皮捲","腐皮捲"),
    ("煲仔飯","煲仔飯"),("咖哩魚蛋","魚蛋"),("雲吞","雲吞"),("餛飩","餛飩"),
    ("鹹水角","鹹水角"),("春捲","春捲"),("叉燒飯","叉燒飯"),("燒臘","燒臘"),
    ("烤鴨","烤鴨"),("叉燒","叉燒"),
    # 甜品/冰品
    ("豆花","豆花"),("燒仙草","燒仙草"),("愛玉","愛玉"),("仙草","仙草"),
    ("芋圓","芋圓"),("地瓜圓","地瓜圓"),("湯圓","湯圓"),("米苔目","米苔目"),
    ("石花凍","石花凍"),("杏仁豆腐","杏仁豆腐"),("楊枝甘露","楊枝甘露"),
    ("米糕粥","米糕粥"),("甜湯","甜湯"),("冰品","冰品"),("剉冰","剉冰"),
    ("雪花冰","雪花冰"),("芒果冰","芒果冰"),("草莓冰","草莓冰"),
    ("提拉米蘇","提拉米蘇"),("慕斯","慕斯"),("巧克力","巧克力"),
    ("甜甜圈","甜甜圈"),("泡芙","泡芙"),("司康","司康"),("可頌","可頌"),
    # 火鍋/燒烤
    ("麻辣鍋","麻辣鍋"),("石頭火鍋","石頭火鍋"),("涮涮鍋","涮涮鍋"),
    ("羊肉爐","羊肉爐"),("薑母鴨","薑母鴨"),("汕頭火鍋","汕頭火鍋"),
    ("燒肉","燒肉"),("烤肉","烤肉"),("和牛","和牛"),("牛舌","牛舌"),
    ("豬五花","豬五花"),("牛五花","牛五花"),("雞腿肉","雞腿肉"),
    ("海鮮拼盤","海鮮拼盤"),("大草蝦","草蝦"),("蛤蜊","蛤蜊"),
    ("生蠔","生蠔"),("干貝","干貝"),("透抽","透抽"),
    # 燒烤/居酒屋
    ("牛肉串","牛肉串"),("羊肉串","羊肉串"),("雞肉串","雞肉串"),("豬五花串","豬五花串"),
    ("一夜干","一夜干"),("烤麻糬","烤麻糬"),("明太子","明太子"),
    ("柳葉魚","柳葉魚"),("烤飯糰","烤飯糰"),("飛魚卵","飛魚卵"),
    # 日式
    ("握壽司","握壽司"),("生魚片","生魚片"),("炙燒","炙燒"),("花壽司","花壽司"),
    ("拉麵","拉麵"),("豚骨拉麵","豚骨"),("味噌拉麵","味噌"),("醬油拉麵","醬油"),
    ("咖哩飯","咖哩飯"),("牛井","牛井"),("鰻魚飯","鰻魚飯"),
    ("烏龍麵","烏龍麵"),("蕎麥麵","蕎麥"),("咖哩烏龍","咖哩烏龍"),
    # 義式/美式/其他
    ("義大利麵","義大利麵"),("披薩","披薩"),("薯條","薯條"),("漢堡","漢堡"),
    ("炸雞","炸雞"),("雞軟骨","雞軟骨"),("雞胗","雞胗"),
    ("牛排","牛排"),("肋眼","肋眼"),("菲力","菲力"),
    # 飲料
    ("泰式奶茶","泰奶"),("檸檬愛玉","愛玉"),("冬瓜茶","冬瓜茶"),
    ("青茶","青茶"),("烏龍茶","烏龍茶"),("決明子茶","決明子"),
]

def _dish_from_reviews(reviews):
    found = {}
    for review in reviews:
        content = review.get("content","")
        if content is None: continue
        for pattern, canonical in _DISH_PATTERNS:
            if canonical in found: continue
            key = pattern.split("，")[0].split("（")[0]
            idx = content.find(key)
            if idx < 0: continue
            snippet = content[idx+len(key): idx+60].strip()
            snippet = re.sub(r"[\n\r]+", "，", snippet)
            snippet = re.sub(r"，，+，", "，", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            m2 = re.search(r"[。！？?！]", snippet)
            if m2: snippet = snippet[:m2.end()]
            snippet = snippet.strip("。，、：：「」\"''()（）　 ")
            if len(snippet) < 4: continue
            found[canonical] = (pattern, snippet)
        if len(found) >= 5: break
    result = []
    for pattern, canonical in _DISH_PATTERNS:
        if canonical in found:
            result.append((found[canonical][0], found[canonical][1]))
    return result[:5]


def _days_ago_str(days: int) -> str:
    """將天數轉換為易讀的「多久以前」字串"""
    if days == 0:
        return "（今天）"
    elif days == 1:
        return "（1天前）"
    elif days < 30:
        return f"（{days}天前）"
    elif days < 365:
        return f"（{days // 30}個月前）"
    else:
        return f"（{days // 365}年前）"


def _rev_from_list(reviews, rev_count=REV_COUNT):
    results = []; seen = set()
    for review in reviews:
        author   = review.get("author","")
        content  = review.get("content","")
        days_ago = review.get("days_ago", 0)
        if not content: continue
        for sent in re.split(r"[。\n]", content):
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 80: continue
            if re.search(r"\$\d+", sent): continue
            if re.search(r"美元|美金|日幣|日圆|韓元|歐元|台幣", sent): continue
            if sent in seen: continue
            seen.add(sent); results.append((author, sent, days_ago)); break
        if len(results) >= rev_count: break
    if len(results) < rev_count:
        for review in reviews:
            content  = review.get("content","")
            days_ago = review.get("days_ago", 0)
            if not content: continue
            for sent in re.split(r"[。\n]", content):
                sent = sent.strip()
                # fallback：放寬英文句子長度限制至90字，避免英文長句被漏接
                if len(sent) < 4 or len(sent) > 90: continue
                if re.search(r"\$\d+", sent): continue
                if re.search(r"美元|美金|日幣|日圆|韓元|歐元|台幣", sent): continue
                if sent in seen: continue
                seen.add(sent); results.append((review.get("author",""), sent, days_ago)); break
            if len(results) >= rev_count: break
    return [(a,n,d) for a,n,d in results if len(n) >= 10][:rev_count]


# -------------------------------------------------------------
# 價格留言抓取（v2.11 新增）
# -------------------------------------------------------------
_PRICE_RE = re.compile(
    r"(?:每人|per person|人均)[\s:：]*\$?(\d+)|"
    r"\$([1-9]\d*)(?:\.\d{2})?|"
    r"[+＋]\s*\$?(\d+)\s*元|"
    r"(\d+)\s*元(?:\s*[/人每位])?|"
    r"(?:USD|US\$|US dollars)\s*(\d+)|"
    r"(\d+)\s*(?:美元|美金|日幣|日圆|韓元|歐元|英鎊|澳幣|加幣)"
, re.IGNORECASE)


def _price_rev_from_list(reviews, rev_count=REV_COUNT):
    """
    專門抓取提及價格的評論。
    回傳 List[Tuple(author, 完整句子, 產品名, 份量描述, 價格字串, days_ago)]
    """
    results = []; seen = set()
    for review in reviews:
        author   = review.get("author", "")
        content  = review.get("content", "")
        days_ago = review.get("days_ago", 0)
        if not content:
            continue
        for sent in re.split(r"[。\n]", content):
            sent = sent.strip()
            if len(sent) < 8:
                continue
            # 只保留有價格關鍵字的句子
            if not _PRICE_RE.search(sent):
                continue
            if sent in seen:
                continue
            seen.add(sent)

            # 智慧解析：抽出產品名、份量、價格
            product, portion, price_str = _parse_price_sentence(sent)

            results.append((author, sent, product, portion, price_str, days_ago))
        if len(results) >= rev_count:
            break
    return results[:rev_count]


def _parse_price_sentence(sent: str) -> Tuple[str, str, str]:
    """
    從含價格的句子中智慧解析：
    - 產品食物名稱（移除價格相關描述）
    - 份量描述（如大中小、超值套餐、加購等）
    - 價格字串（如 $120、$50–$80）
    回傳 (產品, 份量, 價格)
    """
    price_str = ""
    prices = []

    # ① 一次性正則（_PRICE_RE 已含新台幣+外幣所有模式）
    for m in _PRICE_RE.finditer(sent):
        for g in m.groups():
            if g:
                v = int(g)
                if 1 <= v <= 20000:
                    prices.append(v)

    if prices:
        unique = sorted(set(prices))
        # 如果價格 < 500 且句子有外幣關鍵字，標示幣別
        if unique[0] < 500 and re.search(r"美元|美金|日幣|日圆|韓元|歐元|英鎊|澳幣|加幣", sent):
            currency_label = next(
                (c for c in ["美元","美金","日幣","日圆","韓元","歐元","英鎊","澳幣","加幣"]
                 if c in sent), "外幣"
            )
            price_str = f"${unique[0]}（{currency_label}）" if len(unique) == 1 else f"${unique[0]}–${unique[-1]}（{currency_label}）"
        else:
            price_str = f"${unique[0]}" if len(unique) == 1 else f"${unique[0]}–${unique[-1]}"

    # 嘗試找出產品名（移除價格描述後的句子前半段）
    # 價格描述的關鍵字
    price_desc_kw = [
        "每人", "per person", "人均", "多少錢", "很便宜", "太貴", "CP值",
        "划算", "值得", "價錢", "價格", "收費", "消費", "特价", "特價",
        "优惠", "優惠", "套餐", "加購", "加點", "升級", "大中小",
        "均一價", "定食", "吃到飽", "自助吧",
    ]
    product_part = sent
    for kw in price_desc_kw:
        idx = product_part.find(kw)
        if idx >= 0:
            product_part = product_part[:idx]
            break

    # 清理產品名（取前面有意義的部分）
    product_part = product_part.strip(" ，,、：：「」\"''()（）　 ")
    # 取句子最前面的描述當產品名（至多30字）
    if len(product_part) > 30:
        # 嘗試在句中找到一個合理的斷點
        for sep in ["、", "，", "與", "和", "或"]:
            idx = product_part.rfind(sep, 0, 25)
            if idx > 0:
                product_part = product_part[:idx]
                break
        else:
            product_part = product_part[:30]

    # 移除價格符號、數字、結尾殘留的語氣詞
    product_part = re.sub(r"\s*\$?\d+.*$", "", product_part)
    product_part = product_part.rstrip("也很太又還最真").strip(" ，,、：：「」\"''()（）　")

    # 份量描述：找「大」、「中」、「小」、「套餐」、「加購」等
    portion = ""
    portion_kw = ["大份", "中份", "小份", "大碗", "中碗", "小碗",
                  "超值套餐", "套餐", "加購", "加點", "升級",
                  "吃到飽", "自助吧", "無限享用"]
    for kw in portion_kw:
        if kw in sent:
            portion = kw
            break
    else:
        # 預設份量：抓「1人份」「2人份」等
        m = re.search(r"(\d+)\s*人[份道個位]", sent)
        if m:
            portion = f"{m.group(1)}人份"

    product = product_part.strip() if product_part.strip() else "（未識別品項）"
    return product, portion, price_str


# -------------------------------------------------------------
# CLI 入口
# -------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: python3 run.py <使用者文字>")
        print("範例: python3 run.py 我想吃早餐")
        print("範例: python3 run.py 找停車場 24.1858,120.6677 開車5分")
        print("範例: python3 run.py 火鍋 評分4.5以上")
        print("範例: python3 run.py 素食 1km內 5家")
        sys.exit(1)

    user_text = " ".join(sys.argv[1:])

    params = parse_input(user_text)
    if not params:
        print("⚠️ 無法從文字中辨識搜尋意圖")
        print(f"   請使用餐飲/設施/地點/食物關鍵字，如：{TRIGGER_KEYWORDS[:10]}")
        sys.exit(1)

    result = search_and_detail(params)
    print(f"\n```\n{result}\n```\n")


if __name__ == "__main__":
    main()
