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
    venv_python = os.path.expanduser("~/.openclaw/skills/google-places/.venv/bin/python")
    python_bin = venv_python if os.path.exists(venv_python) else "python3"
    try:
        r = subprocess.run(
            [python_bin, script, "full", place_id],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=os.environ.copy(), timeout=90
        )
        raw = r.stdout
        if not raw and r.stderr:
            # script 可能 stderr 有錯誤，但 stdout 起碼會有內容
            raw = r.stderr
        # 只保留明確的實質內容行（嚴格不刪減）
        clean_lines = []
        for line in raw.split("\n"):
            stripped = line.strip()
            # 跳過純 CDP debug 識別字首（每行第一個 token）
            skip_prefixes = (
                "[CDP]", "Phase", "stable ", "state:",
                "done", "result.", "hist=", "Click ",
                "WS OK", "WS connected", "Tab clicked",
                "WS ", "[Phase",
            )
            if any(stripped.startswith(p) for p in skip_prefixes):
                continue
            # 跳過包含 "polling" 的純狀態行（非內容行）
            if "polling" in stripped and len(stripped) < 80:
                continue
            # 跳過純空行
            if not stripped:
                continue
            # 其餘全部保留（address/phone/rating/status/評論等）
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
        "GOOGLE_PLACES_API_KEY", "AIzaSyBHXbe-9_jDT6WREBg8czfpt2iGqqtPtG8")
    venv_python = os.path.expanduser("~/.openclaw/skills/google-places/.venv/bin/python")
    python_bin = venv_python if os.path.exists(venv_python) else sys.executable

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

def _parse_maps_price_from_raw(raw: str) -> dict:
    """
    從 query.py full 的 raw 文字輸出中，
    解析出 CDP maps_price 結構（price_range / service / popular_items / price_histogram）。
    """
    mp = {"found": False, "price_range": None, "reporter": None,
          "price_histogram": [], "service": [], "popular_items": [], "menu_url": None}

    # ── price_range：找 💵 每人消費：$X–$Y 那行 ──────────────
    m = re.search(r"💵\s*每人消費：([^\n]+)", raw)
    if m:
        line = m.group(1).strip()
        # 去除 distribution bar 部分（如 "   ▓▓▓░░  $100–$200  約71人（50%）"）
        bar_m = re.search(r"^([^\n]+?)(?:\s{2,}|$)", line)
        if bar_m:
            price_part = bar_m.group(1).strip()
            # 去掉結尾的 "（N人回報）"
            price_part = re.sub(r"（[^）]*人回報[^）]*）$", "", price_part)
            if price_part and price_part not in ("店家未提供", "無法讀取"):
                mp["found"] = True
                mp["price_range"] = price_part

    # ── reporter：從 "（71人回報）" 這類格式抓 ──────────────
    rm = re.search(r"（(\d+)\s*人回報）", raw)
    if rm:
        mp["reporter"] = f"{rm.group(1)}人回報"

    # ── price_histogram：找 ▓▓░ 分布那幾行 ─────────────────
    for line in raw.split("\n"):
        hm = re.search(r"\s*([▓░])\s+(\$[^\s]+)\s+(約\d+人)\s+（(\d+)%）", line)
        if hm:
            mp["price_histogram"].append([hm.group(2), hm.group(3), int(hm.group(4))])

    # ── service：找 📌 服務：那一行 ─────────────────────────
    sm = re.search(r"📌\s*服務：([^\n]+)", raw)
    if sm:
        svcs = [s.strip() for s in re.split(r"[、，]", sm.group(1)) if s.strip()]
        mp["service"] = svcs

    # ── popular_items：找 🍜 熱門品項：那一行 ────────────────
    pm = re.search(r"🍜\s*熱門品項：([^\n]+)", raw)
    if pm:
        items = [it.strip() for it in re.split(r"[｜\n]", pm.group(1)) if it.strip()]
        mp["popular_items"] = items

    # ── menu_url：找 🍽️ Menu：那一行 ────────────────────────
    mm = re.search(r"🍽️\s*Menu：([^\n]+)", raw)
    if mm:
        mp["menu_url"] = mm.group(1).strip()

    return mp


def _get_reviews_from_api_data(api_data: dict) -> list:
    """從 api_data 中取出 6 個月內的評論（供格式化用）"""
    reviews = api_data.get("_filtered_reviews", [])
    if not reviews:
        reviews = api_data.get("reviews", [])
    return reviews


def format_full_output(raw: str, place_data: dict, maps_price: dict,
                       food_kw: Optional[str], dist_m: float,
                       index: int, reviews: list = None) -> str:
    """
    ★ 確保輸出完整的 12 項欄位（確定性格式化）★
    欄位：
      1. 店名  2. 地址  3. 經緯度  4. 電話  5. 評分
      6. 每人消費  7. 服務  8. 特色菜色  9. 網友心得
     10. 營業狀態  11. 網站  12. Google Maps
    """
    from datetime import datetime, timedelta

    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    # ── 基本欄位取值 ────────────────────────────────────────
    name       = place_data.get("name", "未知店家") if place_data else "未知店家"
    pid        = place_data.get("place_id", place_data.get("id", "")) if place_data else ""
    rating     = place_data.get("rating", 0) if place_data else 0
    rcount     = place_data.get("user_rating_count", 0) if place_data else 0
    address    = (place_data.get("formattedAddress")
                 or place_data.get("address", "無地址")) if place_data else "無地址"
    lat        = (place_data.get("location", {}).get("lat", "")
                 if place_data else "")
    lng        = (place_data.get("location", {}).get("lng", "")
                 if place_data else "")
    phone      = place_data.get("phone", "無") if place_data else "無"
    website    = place_data.get("website", "無") if place_data else "無"
    open_now   = place_data.get("open_now") if place_data else None
    raw_hours  = place_data.get("regularHours", []) if place_data else []
    if isinstance(raw_hours, list):
        hours = [h for h in raw_hours if h]
    elif isinstance(raw_hours, str) and raw_hours:
        hours = [raw_hours]
    else:
        hours = place_data.get("hours", []) if place_data else []
    price_rng_api = place_data.get("_price_range") if place_data else None

    maps_url = f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""

    # ── 距離估算 ──────────────────────────────────────────
    drv = estimate_time(dist_m, "driving")
    wal = estimate_time(dist_m, "walking")
    dist_str = f"📏 直線距離：{dist_m:.0f}m（🚗 {drv}分 🚶 {wal}分）"

    # ── 食物關鍵字標記 ─────────────────────────────────────
    food_tag = f"｜🍴 符合：{food_kw}" if food_kw else ""

    lines = []

    # ══ 1. 店名 + 評分 ════════════════════════════════════════
    lines.append(f"{medal[index]} {'═'*52}")
    lines.append(f"🏪 店名：{name}｜⭐ 評分：{rating}（{rcount}則）{food_tag}")
    lines.append(f"{dist_str}")

    # ══ 2. 地址 ═══════════════════════════════════════════════
    lines.append(f"📍 地址：{_fmt_addr(address)}")

    # ══ 3. 經緯度 ══════════════════════════════════════════
    if lat and lng:
        lines.append(f"📍 經緯度：{round(float(lat), 6)}, {round(float(lng), 6)}")

    # ══ 4. 電話 ══════════════════════════════════════════════
    lines.append(f"📞 電話：{phone}")

    # ══ 5. 每人消費 ══════════════════════════════════════════
    price_hist = (maps_price or {}).get("price_histogram", [])
    rep_label  = (maps_price or {}).get("reporter", "") or ""
    if price_rng_api:
        rep_str = f"（{rep_label}）" if rep_label else ""
        lines.append(f"💵 每人消費：{price_rng_api}{rep_str}")
    elif maps_price and maps_price.get("found"):
        pr = maps_price.get("price_range", "店家未提供")
        rep_str = f"（{rep_label}）" if rep_label else ""
        lines.append(f"💵 每人消費：{pr}{rep_str}")
    else:
        lines.append(f"💵 每人消費：店家未提供")
    for lbl, cnt, pct in price_hist:
        bar = "▓" * max(1, int(pct / 10)) + "░" * (10 - max(1, int(pct / 10)))
        lines.append(f"   {bar}  {lbl}  {cnt}（{pct}%）")

    # ══ 6. 服務 ══════════════════════════════════════════════
    svcs = (maps_price or {}).get("service", [])
    if svcs:
        lines.append(f"📌 服務：{'、'.join(svcs)}")

    # ══ 7. 特色菜色 ════════════════════════════════════════
    dish_list = _dish_from_reviews(reviews or [])
    if dish_list:
        lines.append("🔥 特色菜色：")
        for dname, snippet in dish_list:
            s2 = snippet if len(snippet) <= 80 else snippet[:80] + "…"
            lines.append(f"   {dname}：{s2}")
    else:
        lines.append("🔥 特色菜色：無（評論中未抓獲特定菜色）")

    # ══ 8. 網友心得 ════════════════════════════════════════
    rev_list = _rev_from_list(reviews or [])
    if rev_list:
        lines.append("📝 網友心得：")
        for author, note in rev_list:
            n2 = note if len(note) <= 150 else note[:150] + "…"
            lines.append(f"   {author}：{n2}")
    else:
        lines.append("📝 網友心得：無（近期無評論）")

    # ══ 9. 營業狀態 ════════════════════════════════════════
    now = datetime.now()
    days_en = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    days_zh = ["週一","週二","週三","週四","週五","週六","週日"]
    today_en = days_en[now.weekday()]

    today_hr = None
    for h in (hours or []):
        if not h: continue
        parts = h.split(": ", 1)
        if len(parts) == 2 and parts[0].strip() == today_en:
            tp = parts[1].strip()
            today_hr = None if tp.lower() == "closed" else tp

    status_str = _fmt_status(open_now, today_hr, hours, now, days_en, days_zh)
    lines.append(f"🚦 狀態：{status_str}")

    # ══ 10. 網站 ═══════════════════════════════════════════
    lines.append(f"🌐 網站：{website}")

    # ══ 11. Google Maps ════════════════════════════════════
    lines.append(f"🔗 Google Maps：{maps_url}")

    return "\n".join(lines)

def _fmt_addr(addr_en: str) -> str:
    """地址中文化（對應 query.py format_address）"""
    a = addr_en.strip()
    if not a: return a

    # 1. 抽郵遞區號（結尾 3-5 位數）
    zipcode = ""
    zm = re.search(r"\b(\d{3,5})\s*$", a)
    if zm:
        zipcode = zm.group(1)
        a = a[:zm.start()].strip().rstrip(",").rstrip()

    # 2. 抽門牌號（No. 251號 / 251號兩種格式）
    house_num = ""
    hm = re.search(r"No\.?\s*(\d+)\s*號?", a)
    if hm:
        house_num = hm.group(1) + "號"
        rest = a[hm.end():].lstrip()
        if rest.startswith(","): rest = rest[1:].lstrip()
        a = rest.strip().rstrip(",").rstrip()
    else:
        hm2 = re.search(r"^(\d+)號\s*,", a)
        if hm2:
            house_num = hm2.group(1) + "號"
            a = a[hm2.end():].strip()

    # 3. 抽段
    section_num = ""
    sm = re.search(r"[Ss]ection\s*(\d+)", a)
    if sm:
        section_num = sm.group(1) + "段"
        a = re.sub(r"[Ss]ection\s*\d+\s*,?\s*", "", a).strip().rstrip(",").rstrip()

    # 4. 中英對照置換（用 \b word boundary，防止部分匹配）
    #    順序：長的先換（New Taipei > Taipei），並避開 "Taiwan" 單置
    rep = {
        "New Taipei City":"新北市","Taichung City":"台中市","Changhua City":"彰化市",
        "Taipei City":"台北市","Hsinchu City":"新竹市",
        "Beitun District":"北屯區","Xitun District":"西屯區","Nantun District":"南屯區",
        "Dali District":"大里區","Wuri District":"梧棲區","Dajia District":"大甲區",
        "Fengyuan District":"豐原區","Shalu District":"沙鹿區","Longjing District":"龍井區",
        "Qingshui District":"清水區","Dadu District":"大肚區","Wanhua District":"萬華區",
        "Da'an District":"大安區","Songshan District":"松山區","Neihu District":"內湖區",
        "Nangang District":"南港區","Zhonghe District":"中和區","Yonghe District":"永和區",
        "Zhongzheng District":"中正區","Datong District":"大同區","Banqiao District":"板橋區",
        "North District":"北區","South District":"南區","East District":"東區",
        "West District":"西區","Central District":"中區",
        "Hankou Rd":"漢口路","Dunhua Rd":"敦化路","Fuxing Rd":"復興路",
        "Zhongshan Rd":"中山路","Rd":"路","Road":"路","St":"街","Street":"街",
    }
    # 依 key 長度降冪，確保 "New Taipei City" 先於 "Taipei City"
    for en, zh in sorted(rep.items(), key=lambda x: -len(x[0])):
        # 使用 \b 邊界，確保不匹配 "Taichung City" in "Taichung CityHall"
        pattern = r"\b" + re.escape(en) + r"\b"
        a = re.sub(pattern, zh, a)

    # 5. 清理多餘符號
    a = re.sub(r",+", "，", a); a = re.sub(r"，+", "，", a)
    a = a.strip("，").strip()
    a = re.sub(r"^No\.?\s*", "", a).strip()
    # 移除結尾的「台灣」或「Taiwan」（country part）
    a = re.sub(r"，?\s*台灣\s*$", "", a).strip()
    a = re.sub(r"，?\s*Taiwan\s*$", "", a, flags=re.IGNORECASE).strip()

    # 6. 以「，」分段，重組地址
    road_kws = ["路","街","巷","弄","大道"]
    tokens = [t.strip() for t in re.split(r"[，,]+", a) if t.strip()]
    city = ""; district = ""; road = ""; others = []
    for tok in tokens:
        if any(tok.endswith(k) for k in road_kws):
            road = tok
        elif tok in ["台中市","彰化市","台北市","新北市","新竹市"]:
            city = tok
        elif "區" in tok:
            district = tok
        elif re.match(r"^\d{3,5}$", tok):
            pass  # 郵遞區號殘留，跳過
        else:
            others.append(tok)

    zip_lbl = f"（{zipcode}）" if zipcode else ""
    return city + district + "".join(others) + road + section_num + house_num + zip_lbl

def _fmt_status(open_now, today_hr, hours, now, days_en, days_zh) -> str:
    """營業狀態格式化（對應 query.py 狀態邏輯）"""
    from datetime import timedelta
    import re
    if open_now is True:
        if today_hr:
            fm = re.search(
                r"(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)",
                today_hr, re.IGNORECASE)
            if fm:
                oh=int(fm[1]); om=int(fm[2]); oampm=fm[3].upper()
                ch=int(fm[4]); cm=int(fm[5]); campm=fm[6].upper()
                oh24=oh%12+(12 if oampm=='PM' else 0)
                ch24=ch%12+(12 if campm=='PM' else 0)
                cl_dt=now.replace(hour=ch24,minute=cm,second=0,microsecond=0)
                op_dt=now.replace(hour=oh24, minute=om, second=0, microsecond=0)
                # 跨日： closing < opening 或 closing=12AM 表示隔日凌晨打烊
                if ch24 <= oh24 or ch24 < 12:
                    cl_dt += timedelta(days=1)
                diff=int((cl_dt-now).total_seconds())
                if diff>0:
                    hl=diff//3600; ml=(diff%3600)//60
                    tl = f"距離關門 {hl} 小時 {ml} 分鐘" if hl>0 else f"距離關門 {ml} 分鐘"
                else:
                    tl = "已超過關門時間"
                return f"✅ 營業中（今日 {today_hr}，{tl}）"
        return "✅ 營業中"
    elif open_now is False:
        if today_hr:
            fm = re.search(
                r"(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)",
                today_hr, re.IGNORECASE)
            if fm:
                oh=int(fm[1]); om=int(fm[2]); oampm=fm[3].upper()
                ch=int(fm[4]); cm=int(fm[5]); campm=fm[6].upper()
                oh24=oh%12+(12 if oampm=='PM' else 0)
                ch24=ch%12+(12 if campm=='PM' else 0)
                op_dt=now.replace(hour=oh24, minute=om, second=0, microsecond=0)
                cl_dt=now.replace(hour=ch24,minute=cm,second=0,microsecond=0)
                if ch24<oh24 or ch24<12: cl_dt += timedelta(days=1)
                secs_op=int((op_dt-now).total_seconds())
                secs_cl=int((cl_dt-now).total_seconds())
                if secs_op>0:
                    hl=secs_op//3600; ml=(secs_op%3600)//60
                    ws = f"距離開門 {hl} 小時 {ml} 分鐘" if hl>0 else f"距離開門 {ml} 分鐘"
                    return f"❌ 休息中（今日 {today_hr}，{ws}）"
                elif secs_cl>0:
                    hl=secs_cl//3600; ml=(secs_cl%3600)//60
                    tl = f"距離關門 {hl} 小時 {ml} 分鐘" if hl>0 else f"距離關門 {ml} 分鐘"
                    return f"✅ 營業中（今日 {today_hr}，{tl}）"
            return f"❌ 休息中（今日 {today_hr}）"
        cur_idx=now.weekday()
        for offset in range(1,8):
            nidx=(cur_idx+offset)%7
            for h in hours:
                parts=h.split(": ",1)
                if len(parts)!=2 or parts[0].strip()!=days_en[nidx]: continue
                tp=parts[1].strip()
                if tp.lower()!="closed":
                    return f"❌ 休息中（今日公休，{days_zh[nidx]} {tp} 開門）"
        return "❌ 休息中"
    else:
        if today_hr:
            return f"✅ 營業中（今日 {today_hr}）"
        return "❌ 休息中"


# ── 特色菜色 ══════════════════════════════════════════════════
_DISH_PATTERNS = [
    ("蝦滷飯","蝦滷飯"),("澎湖小卷","小卷"),("煎干貝","干貝"),("脆皮燒肉","燒肉"),
    ("辣椒","辣椒"),("海鮮炒麵","炒麵"),("海鮮粥","海鮮粥"),("油蔥蝦仁飯","油蔥蝦仁飯"),
    ("川燙花枝","花枝"),
    ("燒賣","燒賣"),("蝦餃","蝦餃"),("蝦餃皇","蝦餃皇"),("叉燒包","叉燒包"),
    ("叉燒","叉燒"),("流沙包","流沙包"),("奶黃包","奶黃包"),("蛋撻","蛋撻"),
    ("菠蘿包","菠蘿包"),("鮮蝦腸粉","腸粉"),("牛肉丸","牛肉丸"),("蒸餃","蒸餃"),
    ("小籠包","小籠包"),("腐皮捲","腐皮捲"),("炸兩","炸兩"),("臘味蘿蔔糕","蘿蔔糕"),
    ("XO醬炒蘿蔔糕","蘿蔔糕"),("煲仔飯","煲仔飯"),("咖喱魚蛋","魚蛋"),("雲吞","雲吞"),
    ("餛飩","餛飩"),("鹹水角","鹹水角"),("春捲","春捲"),("天扶良","天扶良"),
    ("叉燒飯","叉燒飯"),("燒臘","燒臘"),("烤鴨","烤鴨"),("脆皮烤鴨","烤鴨"),
    ("豆花","豆花"),("燒仙草","燒仙草"),
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
            snippet = re.sub(r"[\n\r]+", "，", snippet)
            snippet = re.sub(r"，+，", "，", snippet)
            snippet = re.sub(r"\s+", " ", snippet).strip()
            m = re.search(r"[。！？?！]", snippet)
            if m: snippet = snippet[:m.end()]
            snippet = snippet.strip("。，、：：「」\"''()（）　 ")
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
        if not content or author == "LISON": continue
        for sent in re.split(r"[。\n]", content):
            sent = sent.strip()
            if len(sent) < 10 or len(sent) > 80: continue
            if re.search(r"\$\d+", sent): continue
            if sent in seen: continue
            seen.add(sent); results.append((author, sent)); break
        if len(results) >= 3: break
    if len(results) < 3:
        for review in reviews:
            content = review.get("content","")
            if not content or review.get("author") == "LISON": continue
            for sent in re.split(r"[。\n]", content):
                sent = sent.strip()
                if len(sent) < 10 or len(sent) > 60: continue
                if re.search(r"\$\d+", sent): continue
                if sent in seen: continue
                seen.add(sent); results.append((review.get("author",""), sent)); break
            if len(results) >= 3: break
    return [(a,n) for a,n in results if len(n) >= 10][:3]


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
        maps_price: dict = {"found": False}
        reviews_list: list = []
        if pid:
            _, raw_output = query_place_full(pid)
            maps_price = _parse_maps_price_from_raw(raw_output)
            reviews_list = _get_reviews_from_api_data(api_data)

        detail_text = format_full_output(
            "", api_data, maps_price, food_kw, dist, i, reviews_list
        )
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
