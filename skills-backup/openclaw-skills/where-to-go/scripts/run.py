#!/usr/bin/env python3
"""
where-to-go 完整執行腳本 v2.0（2026-03-22）
整合 Step 2→3→4→5：搜尋 → 過濾排序 → 詳細查詢 → 輸出完整結果

更新：
- 自動對每個候選地點呼叫『Google Places 地點查詢技能』（query.py full）
- 新增食物關鍵字（火鍋、壽司、合菜、快炒、素食、港式、飲茶…）
- 食物關鍵字會過濾店家的說明、評論、特色菜色，只有提到該食物的店家才入選
"""
import subprocess
import json
import sys
import os
import re
import math
import time
import asyncio
from typing import List, Dict, Optional, Tuple

# ─── 設定 ────────────────────────────────────────────────────
DEFAULT_LAT = 24.18588146738243
DEFAULT_LNG = 120.66765935832942
DEFAULT_RADIUS_M = 1000
DEFAULT_MIN_RATING = 4.5
DEFAULT_MAX_RESULTS = 5
DEFAULT_MAX_CANDIDATES = 30   # 先多抓一些，食物關鍵字會過濾掉部分

EXPANSION_RADII = [1000, 1500, 2500, 5000, 10000, 20000, 50000]

# ─────────────────────────────────────────────────────────────
# 觸發關鍵字
# ─────────────────────────────────────────────────────────────

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
    "燒肉", "燒烤", "牛排", "炸物", "披薩", "義大利麵",
    "咖哩", "拉麵", "烏龍麵", "牛肉麵", "蚵仔煎", "肉圓",
    "滷肉飯", "雞腿飯", "便當", "自助餐", "buffet",
    "早午餐", "brunch", "咖啡", "甜點", "蛋糕", "冰淇淋",
    "剉冰", "豆花", "仙草", "芋圓",
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


# ─────────────────────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# 關鍵字偵測
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# 食物過濾器
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# goplaces search
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# filter + sort
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# Google Places 地點查詢技能（query.py full）
# ─────────────────────────────────────────────────────────────

def query_place_full(place_id: str) -> Tuple[Optional[dict], str]:
    """
    呼叫『Google Places 地點查詢技能』的 query.py full。
    回傳 (structured_data, raw_text_output)
    """
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
    """只透過 goplaces details + priceRange API 取結構化資料"""
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
                return None
    except Exception:
        return None

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
        data["_price_range"] = price_range
        if "place_id" not in data and "id" in data:
            data["place_id"] = data["id"]
        # 只留6個月內評論（供食物過濾用）
        data["_filtered_reviews"] = _filter_reviews_6m(data.get("reviews", []))
        return data
    return None


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


# ─────────────────────────────────────────────────────────────
# 格式化輸出（query.py full 原始結果 + 摘要）
# ─────────────────────────────────────────────────────────────

def format_full_output(raw: str, place_data: dict, food_kw: Optional[str],
                       dist_m: float, index: int) -> str:
    """
    輸出 query.py full 的完整文字，並在頂部加上本系統的摘要列。
    店家分隔線使用雙線（══）提高辨識度。
    """
    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    name = place_data.get("name", "未知店家") if place_data else "未知店家"
    pid = place_data.get("place_id", "") if place_data else ""
    rating = place_data.get("rating", 0) if place_data else 0
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""

    # 距離估算
    drv = estimate_time(dist_m, "driving")
    wal = estimate_time(dist_m, "walking")
    dist_str = f"📏 直線距離：{dist_m:.0f}m（🚗 {drv}分 🚶 {wal}分）"

    # 食物關鍵字標記
    food_tag = ""
    if food_kw:
        food_tag = f"｜🍴 符合：{food_kw}"

    header = [
        f"{medal[index]} {'═'*52}",
        f"🏪 {name}｜⭐ {rating}{food_tag}",
        f"{dist_str}",
        f"🔗 {maps_url}",
        "",
    ]

    # 如果有 query.py full 原始輸出，直接附加
    if raw and len(raw) > 50:
        return "\n".join(header) + "\n" + raw
    else:
        # 沒有 raw 時，用 place_data 勉強湊一個
        lines = header
        if place_data:
            lines.append(f"📍 {place_data.get('address', '無地址')}")
            phone = place_data.get("phone", "")
            if phone:
                lines.append(f"📞 {phone}")
            open_now = place_data.get("open_now", False)
            status = "✅ 營業中" if open_now else "❌ 休息中"
            lines.append(f"🚦 狀態：{status}")
            pr = place_data.get("_price_range", "")
            if pr:
                lines.append(f"💵 每人消費：{pr}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 解析使用者輸入
# ─────────────────────────────────────────────────────────────

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

    return {
        "keyword": keyword,
        "food_kw": food_kw,
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "radius_hint": radius_hint,
        "min_rating": min_rating,
        "max_results": max_results,
    }


# ─────────────────────────────────────────────────────────────
# 主搜尋流程
# ─────────────────────────────────────────────────────────────

def search_and_detail(params: Dict, verbose: bool = True) -> str:
    keyword   = params["keyword"]
    food_kw   = params["food_kw"]       # 可能為 None
    lat       = params["lat"]
    lng       = params["lng"]
    radius_m  = params["radius_m"]
    radius_hint = params["radius_hint"]
    min_rating = params["min_rating"]
    max_results = params["max_results"]

    expansion_log: List[int] = []
    candidates: List[dict] = []
    final_radius = radius_m

    # ── Step 2: 半徑擴張搜尋 ──
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

    # ── Step 3: 過濾 + 排序 ──
    filtered = filter_and_sort(candidates, lat, lng, min_rating)

    # ── 食物關鍵字過濾（★★★ 新增邏輯） ──
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

    # ── Step 4: 取評分最高的5家（候選選擇） ──
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
        # ── Step 5: 重新按距離由近到遠排列 ──
        top_results.sort(key=lambda x: x.get("_distance_m", 999999))
    else:
        top_results = filtered[:max_results]

    # ── 輸出 Header ──
    r_display = f"{final_radius // 1000}km" if final_radius >= 1000 else f"{final_radius}m"
    rh_display = f"（{radius_hint}）" if radius_hint else ""
    food_display = f"｜食物過濾：{food_kw}" if food_kw else ""

    lines: List[str] = []
    lines.append("=" * 54)
    lines.append("📍 搜尋條件")
    lines.append(f"   關鍵字：{keyword} {food_display}")
    lines.append(f"   圓心：({lat:.4f}, {lng:.4f})｜半徑：{r_display} {rh_display}")
    if expansion_log:
        expanded = " → ".join(str(x) for x in expansion_log)
        lines.append(f"   找到 {len(candidates)} 家候選｜半徑擴張：{expanded} {filter_note}")
    else:
        lines.append(f"   找到 {len(candidates)} 家候選 {filter_note}")

    if not top_results:
        lines.append("")
        lines.append("⚠️ 在指定範圍內找不到符合條件的地點（評分 ≥ {:.1f}，現在有開）".format(min_rating))
        return "\n".join(lines)

    sort_note = "評分最高5家→由近到遠輸出" if is_food_keyword(params["keyword"]) else f"評分 ≥ {min_rating}，由近到遠"
    lines.append(f"   顯示前 {len(top_results)} 家（{sort_note}）")
    lines.append("")
    lines.append(f"🔍 正在查詢 {len(top_results)} 家地點完整資訊（請稍候）...")
    lines.append("")

    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    # ── Step 4: 對每個地點呼叫『Google Places 地點查詢技能』─
    for i, place in enumerate(top_results):
        pid  = get_place_id(place)
        dist = place.get("_distance_m", 0)

        if verbose:
            lines.append(f"⏳ {medal[i]} 查詢中：{get_display_name(place)} ...")

        # 優先用已被食物過濾快取的 api_data，否則重新取
        api_data: Optional[dict] = place.get("_api_data")
        if api_data is None and pid:
            api_data = query_place_api_only(pid)

        # 呼叫 query.py full（完整查詢，包含 CDP 每人消費 + 分布圖）
        raw_output = ""
        if pid:
            _, raw_output = query_place_full(pid)

        detail_text = format_full_output(raw_output, api_data, food_kw, dist, i)
        lines.append(detail_text)
        lines.append("")

        if i < len(top_results) - 1:
            time.sleep(0.5)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────────

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
    print(result)


if __name__ == "__main__":
    main()
