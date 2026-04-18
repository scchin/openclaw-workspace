#!/usr/bin/env python3
"""
整合 Step 2→3→4→5：搜尋 → 過濾排序 → 詳細查詢 → 輸出完整結果
整合 Step 2→3→4→5：搜尋 → 過濾排序 → 詳細查詢 → 輸出完整結果

更新：
- 2026-04-12 v2.24：修復 _wrap_chars 呼叫時缺少 indent 參數導致的 TypeError（修正評論斷行崩潰問題）
- 2026-04-09 v2.23：餐飲時段搜尋時，若候選不足，自動擴展至各餐飲類型（小吃、便當、合菜、義式、咖哩、燒肉、牛排…），以擴大候選池；排除 30 分鐘內即將打烊的店家（僅限餐飲時段）；餐飲時段排序改為距離由近到遠，早午餐店家 penalty +500m往後挪；_MEAT_DISPLAY 語法修復（dict→list of tuple）
- 2026-04-01 v2.18：💵每人：6層 fallback（新增第⑥層 place_data.priceRange）；
  google-places SSL→ssl._create_unverified_context() 確保 priceRange API 可用；
  🗺️地圖連結修正；🍴特色去重 dict.fromkeys()；
  評論時間戳 _parse_pub_time() 9→6位小數；_DISH_PATTERNS 擴充至200+；
  午餐 is_brunchy() 排除早午餐；半徑擴張 break 根據非早午餐數量；
  SWAP 3 處理路段+門牌黏連；_all_reviews 保留完整評論；
  goplaces_search 午餐時傳入 max(5,max_results)
- 2026-04-01 v2.13：移除 HTML 包裝層（純文字 Triple backticks 輸出）；地址翻譯修正常見殘留英文（Lane/N/S/E/W/North/South 等）+ token 內殘留空格移除；複合路名映射（Houzhuang Road→後庄路、Houzhuang North Road→後庄北路）；殘留路名翻譯（Dunhua/Fuxing/Chongqing 等）
- 2026-03-24 v2.12：評論移除 textwrap.fill 自動換行，保持原文完整；新增「價格留言」專區，
  智慧解析產品名/份量/價格並顯示發布時間（多久以前）；_rev_from_list 回傳 days_ago
- 2026-03-24 v2.11：新增「價格留言」專區
- 2026-03-24 v2.10：Header 移除多餘 \n，消滅兩行空白；版本同步更新至 v2.10
- 2026-03-24 v2.9：🍜 熱門品項從 CDP popular_items 解析並新增該欄位
- 2026-03-24 v2.8：Phase 3 無條件執行（平均每人分布圖）、Chrome CDP profile 自動複製（已登入）
- 2026-03-24 v2.7：🚗開車/🚶走路合併一行 + 💵每人消費欄位
- 2026-03-24 v2.6：評論超過52字自動換行（textwrap.fill width=52）
- 2026-03-23 v2.5：純文字模板輸出（符合 MEMORY.md 規範）
- 2026-03-23：冰品關鍵字擴張（冰品、冰店、雪花冰、芒果冰、豆花、仙草、芋圓、
              甜湯、甜品、燒仙草、愛玉、杏仁豆腐、楊枝甘露等）
- 自動對每個候選地點呼叫『Google Places 地點查詢技能』（query.py full）
- 食物關鍵字會過濾店家的說明、評論、特色菜色，只有提到該食物的店家才入選
"""
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import subprocess
import json
import sys
import os
import re
import math
import time
from datetime import datetime, timedelta
import textwrap
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
from translation_helper import translate_to_zh


# --- 設定 ----------------------------------------------------
DEFAULT_LAT = 24.18588146738243
DEFAULT_LNG = 120.66765935832942
DEFAULT_RADIUS_M = 1000
DEFAULT_MIN_RATING = 4.5
DEFAULT_MAX_RESULTS = 5   # 預設輸出5間；使用者指定數量時以指定者為準
DEFAULT_MAX_CANDIDATES = 30   # 先多抓一些，食物關鍵字會過濾掉部分
REV_COUNT = 10  # 每家店最多顯示10則，按時間排序

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
    "冰", "咖啡", "甜點", "蛋糕", "冰淇淋",
    "剉冰", "豆花", "仙草", "芋圓",
    # 冰品同義擴張（2026-03-23）
    "冰品", "冰店", "雪花冰", "芒果冰", "豆花", "仙草凍",
    "芋圓", "地瓜圓", "湯圓", "米苔目", "愛玉", "石花凍",
    "杏仁豆腐", "米糕粥", "甜湯", "甜品", "涼茶", "青草茶",
    "楊枝甘露", "燒仙草", "冰剉冰", "傳統冰",
    "手搖", "珍奶", "飲料", "奶茶", "果昔",
    "居酒屋", "小吃", "鹹酥雞", "滷味", "關東煮",
    "水煎包", "蔥油餅", "肉包", "蛋餅", "吐司", "三明治",
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

# 斷行輔助（2026-03-24）：prefix + 內容自動在空白處斷行，保持 prefix 對齊
_WRAP_WIDTH = 50  # 單行最大字元數（英文/數字混合情境適用）
_INDENT     = "  "  # 斷行後的縮排，與 prefix 後內容對齊

def _wrap_chars(indent: str, text: str, width: int) -> List[str]:
    """
    對長文字做字元級自動斷行（適合無空格的中文）。
    每行皆以 indent 開頭，若最後一行是時間孤兒則挪回上一行末尾。
    """
    _TIME_RE = re.compile(r"^（[0-9零一二三四五六七八九十百千]+[天月年]+前）$")
    if len(text) <= width:
        return [indent + text]
    # 按寬度截斷，並在可斷開的位置（句號、驚嘆號、問號、中黑、換行）切換
    lines: List[str] = []
    start = 0
    while start < len(text):
        if len(text) - start <= width:
            lines.append(indent + text[start:])
            break
        # 找最後一個可斷點
        chunk = text[start:start + width]
        break_chars = re.findall(r'[。！？；\n]', chunk)
        if break_chars:
            # 找到最後一個可斷開的標點
            last_pos = max(chunk.rfind(c) for c in break_chars)
            lines.append(indent + text[start:start + last_pos + 1])
            start += last_pos + 1
        else:
            # 無標點，直接截斷
            lines.append(indent + chunk)
            start += width
    # 時間孤兒處理（當時間独自成一行時，挪回上一行）
    out: List[str] = list(lines)
    while len(out) >= 2:
        last = out[-1].strip()
        m = _TIME_RE.match(last)
        if m and len(out[-2].strip()) > 8:  # 上一行起碼要有內容才合併（防呆）
            out.pop()
            out[-1] = out[-1].rstrip() + " " + last
        else:
            break
    return out

def _wrap_line(prefix: str, content: str, width: int = _WRAP_WIDTH) -> List[str]:
    """
    對長內容在空白處自動斷行，每行皆以 '  ' 開頭。
    若最後一行是時間孤兒（如「（3個月前）」），自動挪回上一行末尾。
    """
    indent = "  "
    _TIME_RE = re.compile(r"^（[0-9零一二三四五六七八九十百千]+[天月年]+前）$")
    # 移除 prefix 自帶的前導空白（避免 indent + prefix 疊加成 4 空格）
    prefix_stripped = prefix.lstrip()

    if len(prefix) + len(content) <= width:
        return [indent + prefix_stripped + _normalize_spaces(content)]

    # 在空白處斷行
    words: List[str] = content.split(" ")
    lines: List[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if current and len(prefix) + len(test) <= width:
            current = test
        else:
            if current:
                lines.append(current)
            current = test
    if current:
        lines.append(current)

    # 第一行：indent + prefix（前導已剷） + 內容；後續行：indent + 內容
    out: List[str] = []
    for idx, line_text in enumerate(lines):
        if idx == 0:
            out.append(indent + prefix_stripped + _normalize_spaces(line_text))
        else:
            out.append(indent + _normalize_spaces(line_text))

    # 時間孤兒處理：若最後一行是純時間，挪回倒數第二行末尾
    while len(out) >= 2:
        last = out[-1].strip()
        m = _TIME_RE.match(last)
        if m:
            out[-2] = out[-2].rstrip() + m.group(0)
            out.pop()
        else:
            break
    return out


def _normalize_spaces(text: str) -> str:
    """移除數值/英文與中文之間的多餘空格（不改行首/行尾縮排）。"""
    # 消除數字與中文之間的空格（例：七 街 → 七街；165 號 → 165號）
    text = re.sub(r"(?<=[0-9])\s+(?=[^\s　])|(?<=[^\s　])\s+(?=[0-9])", "", text)
    # 消除全形括號、冒號兩側多餘空格
    text = re.sub(r"\s*（\s*", "（", text)
    text = re.sub(r"\s*\）\s*", "）", text)
    text = re.sub(r"\s*：\s*", "：", text)
    # 不做 strip()！行首/行尾縮排由呼叫端負責
    return text


def _is_closing_soon(status_line: str) -> bool:
    """檢查店家是否在 30 分鐘內打烊"""
    if not status_line: return False
    # 模式 1: "距離關門 X 小時 Y 分鐘"
    m_full = re.search(r"距離關門\s*(\d+)\s*小時\s*(\d+)\s*分鐘", status_line)
    if m_full:
        return (int(m_full.group(1)) * 60 + int(m_full.group(2))) < 30
    # 模式 2: "距離關門 X 分鐘"
    m_min = re.search(r"距離關門\s*(\d+)\s*分鐘", status_line)
    if m_min:
        return int(m_min.group(1)) < 30
    return False

def _calculate_status_info(place_data: dict) -> Tuple[str, str, str]:
    """
    從原始 place_data 計算營業狀態與剩餘時間。
    回傳 (icon, text, extra)
    """
    if not place_data: return "❌", "未知", ""
    
    now = datetime.now()
    day_names_en = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    today_en = day_names_en[now.weekday()]
    
    hours_data = place_data.get("currentOpeningHours") or place_data.get("hours")
    today_hours = None
    
    if isinstance(hours_data, dict):
        reg_hours = hours_data.get("regularHours", [])
        for h in reg_hours:
            if isinstance(h, dict) and h.get("day") == today_en:
                today_hours = h.get("hours")
                break
    elif isinstance(hours_data, list):
        for h in hours_data:
            if isinstance(h, dict) and h.get("day") == today_en:
                today_hours = h.get("hours")
                break
            elif isinstance(h, str):
                parts = h.split(": ", 1)
                if len(parts) == 2 and parts[0].strip() == today_en:
                    today_hours = parts[1].strip()
                    break
    
    if not today_hours or "closed" in today_hours.lower():
        return "❌", "休息中", ""

    try:
        # 匹配格式: 10:30 AM – 9:30 PM
        m = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*[\u2013\u002d-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)', today_hours, re.IGNORECASE)
        if m:
            ch = int(m.group(4))
            cm = int(m.group(5))
            campm = m.group(6).upper()
            close_h24 = ch % 12 + (12 if campm == 'PM' else 0)
            close_dt = now.replace(hour=close_h24, minute=cm, second=0, microsecond=0)
            if close_h24 <= 0: close_dt += timedelta(days=1)
            diff = close_dt - now
            secs = int(diff.total_seconds())
            if secs > 0:
                extra = f"{secs//3600} 小時 {(secs%3600)//60} 分鐘後關門"
                return "✅", "營業中", f"（{extra}）"
            else:
                return "✅", "營業中", f"（今日 {today_hours}，已超過關門時間）"
    except Exception:
        pass
    
    return "✅", "營業中", f"（今日 {today_hours}）"

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
    raw = data.get("formattedAddress", data.get("address", ""))
    if not raw:
        return "無地址"
    return _format_address_zh(raw)



def _format_address_zh(addr_en: str) -> str:
    """
    將 Google Places 英文地址轉換為台灣標準中文地址格式。
    """
    import re as _re

    a = addr_en.strip()
    if not a:
        return addr_en

    # 郵遞區號（結尾）
    zipcode = ""
    zm = _re.search(r"\b(\d{3,5})\s*$", a)
    if zm:
        zipcode = zm.group(1)
        a = a[:zm.start()].strip().rstrip(",").rstrip()
    # 門牌號：最先處理（適用於 No.格式 和 NN號格式）
    house_num = ""
    hm = _re.search(r"(\d+)號", a)
    if hm:
        if _re.match(r"^No\.?\s*\d+號", a) or _re.match(r"^\d+號\s*,", a):
            house_num = hm.group(1) + "號"
            a = _re.sub(r"No\.?\s*\d+號\s*,\s*", "", a, count=1).strip()
            if house_num not in a:
                a = _re.sub(r"\d+號\s*,\s*", "", a, count=1).strip()
    else:
        hm2 = _re.match(r"^No\.?\s*(\d+)\s*,?\s*", a)
        if hm2:
            house_num = hm2.group(1) + "號"
            a = _re.sub(r"^No\.?\s*\d+\s*,\s*", "", a, count=1).strip()

    # 郵遞區號（結尾）
    zm = _re.search(r"\b(\d{3,5})\s*$", a)
    if zm:
        zipcode = zm.group(1)
        a = a[:zm.start()].strip().rstrip(",").rstrip()
    # 郵遞區號（開頭，如 "406, Taiwan, ..."）
    zm2 = _re.search(r"^\s*(\d{3,5})\s*[,，]", a)
    if zm2:
        zipcode = zipcode or zm2.group(1)
        a = a[zm2.end():].strip().lstrip(",").lstrip("，").strip()

    # 段
    section_num = ""
    m = _re.search(r"Section\s*(\d+)", a, _re.IGNORECASE)
    if m:
        section_num = m.group(1) + "段"
        a = _re.sub(r"Section\s*\d+\s*,?\s*", "", a, flags=_re.IGNORECASE).strip(",").strip()

    # 翻譯置換（list 確保順序，先長後短）
    rep_pairs = [
        # District
        ("Beitun District","北屯區"),("Xitun District","西屯區"),("Nantun District","南屯區"),
        ("Dali District","大里區"),("Wuri District","梧棲區"),("Dajia District","大甲區"),
        ("Fengyuan District","豐原區"),("Shalu District","沙鹿區"),("Longjing District","龍井區"),
        ("Qingshui District","清水區"),("Dadu District","大肚區"),("Wanhua District","萬華區"),
        ("Da'an District","大安區"),("Songshan District","松山區"),("Neihu District","內湖區"),
        ("Nangang District","南港區"),("Zhonghe District","中和區"),("Yonghe District","永和區"),
        ("Zhongzheng District","中正區"),("Datong District","大同區"),("Banqiao District","板橋區"),
        ("North District","北區"),("South District","南區"),("East District","東區"),
        ("West District","西區"),("Central District","中區"),
        # City
        ("Taichung City","台中市"),("Changhua City","彰化市"),
        ("Taipei City","台北市"),("New Taipei City","新北市"),("Hsinchu City","新竹市"),
        # Full road names (長→短)
        ("Hankou Rd","漢口路"),("Dunhua Rd","敦化路"),("Fuxing Rd","復興路"),
        ("Zhongshan Rd","中山路"),
        ("Chongqing Rd","重慶路"),("Chongqing Road","重慶路"),("Chongqing","重慶"),
        ("Zhongping Rd","中平路"),
        ("Zhongping","中平"),
        ("Zhongqing Rd","重慶路"),("Zhongqing Road","重慶路"),
        ("Zhongqing(?! ping)","中清"),
        ("Shunping Rd","順平路"),("Shunping","順平"),
        ("Changan Rd","長安路"),("ChangAn","長安"),("Chang'an Rd","長安路"),("Chang'an","長安"),
        ("Shenyang Rd","瀋陽路"),("Shenyang","瀋陽"),
        ("Dapeng Rd","大鵬路"),("Shanxi Rd","陝西路"),
        ("Houzhuang North Road","後庄北路"),("Houzhuang Road","後庄路"),("Houzhuang","後庄"),
        ("Wenxin Rd","文心路"),("Wenxin Road","文心路"),("Wenxin","文心"),
        ("Gongyi Rd","公正路"),("Gongyi Road","公正路"),("Gongyi","公正"),
        # Direction + Rd 複合（先處理）
        ("N Road","北路"),("S Road","南路"),("E Road","東路"),("W Road","西路"),
        # 縮寫
        ("Rd","路"),("Road","路"),("St","街"),("Street","街"),
        ("Lane","巷"),
        # 單一方向：使用 negative lookahead 防止吃掉 No、Behind 中的 O/N/S/E/W
        ("North(?![a-zA-Z])","北"),("South(?![a-zA-Z])","南"),
        ("East(?![a-zA-Z])","東"),("West(?![a-zA-Z])","西"),
        ("N(?![a-zA-Z])(?!o)(?!orth)","北"),
        ("S(?![a-zA-Z])(?!o)(?!outh)","南"),
        ("E(?![a-zA-Z])(?!a)(?!ast)","東"),
        ("W(?![a-zA-Z])(?!e)(?!est)","西"),
        # 序數
        ("9th","九"),("8th","八"),("7th","七"),("6th","六"),
        ("5th","五"),("4th","四"),("3rd","三"),("2nd","二"),("1st","一"),
        ("Section 1","一段"),("Section 2","二段"),("Section 3","三段"),
        # 殘留路名
        ("Dunhua","敦化"),("Fuxing","復興"),("Changan","長安"),("Shenyang","瀋陽"),
        ("Dapeng","大鵬"),("Chongqing","重慶"),("Shunping","順平"),("Zhongshan","中山"),
        ("Hankou","漢口"),("Dajia","大甲"),("Fengyuan","豐原"),("Wuri","梧棲"),
        ("Huamei","華美"),
        ("Dunhe","敦和"),
    ]

    for en, zh in rep_pairs:
        if "(" in en:
            a = _re.sub(en, zh, a)
        else:
            a = a.replace(en, zh)

    # 後處理
    a = _re.sub(r",+", "，", a); a = _re.sub(r"，+", "，", a)
    a = a.strip("，").strip()
    a = _re.sub(r"^No\.?\s*", "", a).strip()
    a = _re.sub(r"Taiwan", "台灣", a, flags=_re.IGNORECASE)
    a = _re.sub(r"，?\s*Taiwan\s*$", "", a, flags=_re.IGNORECASE).strip()
    a = _re.sub(r"台灣\s*", "", a)
    a = _re.sub(r"\b\d{5,6}(?=[\s,])", "", a)
    a = _re.sub(r"\b\d{5,6}(?=\S)", "", a)
    a = _re.sub(r"\s+", " ", a).strip()

    # 分 token 重組
    road_kws = ["路","街","巷","弄","大道"]
    tokens = [t.strip() for t in _re.split(r"[，,]+", a) if t.strip()]
    tokens = [_re.sub(r"\s+", "", t) for t in tokens if t]
    city = ""; district = ""; road = ""; others = []
    for tok in tokens:
        if _re.fullmatch(r"\d+", tok): continue
        if _re.fullmatch(r"[A-Za-z\s]+", tok): continue
        if any(tok.endswith(k) for k in road_kws): road = tok
        elif tok in ["台中市","彰化市","台北市","新北市","新竹市"]: city = tok
        elif "區" in tok and tok != "台灣": district = tok
        else: others.append(tok)

    zip_label = f"（{zipcode}）" if zipcode else ""

    # SWAP 1：others[-1] 含 "1125號中清路迪卡儂正後方中平路"，road="中平路"
    if others and road and _re.search(r"\d+號", others[-1]) and road in others[-1]:
        m_hn = _re.match(r"(\d+號)(.*)", others[-1])
        if m_hn:
            hp = m_hn.group(1); rest = m_hn.group(2)
            road = road + hp        # "中平路1125號"
            others[-1] = rest       # "中清路迪卡儂正後方中平路"
    # SWAP 2（fallback）：若 house_num 仍為空，且 others[-1] 含 "NNNN號"，說明門牌號被
    # zip2 前綴剝離（如 "Taiwan, ..., Zhongping Rd, 1125號..." → house_num 未觸發）
    # 直接從 others[-1] 抽取門牌號，附加到路名後
    if others and road and not house_num and _re.search(r"\d+號", others[-1]):
        m_hn = _re.match(r".*?(\d+號)(.*)", others[-1])
        if m_hn:
            hp = m_hn.group(1)
            rest = others[-1].replace(hp, "", 1).lstrip("，、， ")
            road = road + hp
            others[-1] = rest
    # SWAP 3（2026-04-01 新增）：針對「河南路二段106號」這類門牌號內嵌在路段中的格式
    # 此時 house_num 為空，road 也為空，others[-1] 包含 "路/街 NN號" 型態
    # 直接從 others[-1] 拆出 "前綴 + 門牌號"，前綴作為 road，門牌號作為 house_num
    if others and not house_num and _re.search(r"\d+號", others[-1]):
        m_hn = _re.match(r"(.+?)(\d+號)$", others[-1])
        if m_hn:
            prefix = m_hn.group(1)   # "河南路二段"
            hp = m_hn.group(2)        # "106號"
            if prefix.endswith(("路", "街", "巷", "弄", "大道")):
                road = prefix
                house_num = hp
                others[-1] = ""
            else:
                # 前綴不是標準路名，當作完整 others[-1] 是路名+門牌
                road = others[-1].replace(hp, "", 1).rstrip("，、， ")
                house_num = hp
                others[-1] = ""

    # Landmark 清理
    landmark_kws = [
        "迪卡儂正後方","迪卡儂旁","迪卡儂前","屈臣氏旁","全聯旁","7-11旁",
        "全家旁","萊爾富旁","OK旁","星巴克旁","麥當勞旁","肯德基旁",
        "必勝客旁","達美樂旁","停車場旁","停車場對面","捷運站旁",
        "火車站旁","高鐵站旁","公園旁","學校旁","醫院旁","消防局旁","警察局旁",
        "中清路","中平路","中山路","重慶路","和平路","成功路","民生路",
        "正氣路","自由路","復興路","新生路","大同路","中正路",
    ]
    cleaned = []
    for o in others:
        if not o: continue
        if any(kw in o for kw in landmark_kws): continue
        if not any(t.endswith(k) for t in [o] for k in ["路","街","巷","弄","大道"]): continue
        cleaned.append(o)
    others = cleaned

    return city + district + road + section_num + house_num + "".join(others) + zip_label

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

def _is_brunchy(p: dict) -> bool:
    """Judge if a place is a brunch/breakfast place (used for lunch keyword filtering)"""
    types = p.get("types") or []
    name  = p.get("name", "")
    return ("brunch_restaurant" in types
            or "\u65e9\u9910" in name
            or "\u65e9\u5348\u9910" in name
            or "brunch" in name.lower())

def _is_desserty(p: dict) -> bool:
    """Judge if a place is primarily a dessert/snack shop (v2.27 修正)"""
    types = p.get("types") or []
    name  = p.get("name", "")
    # 定義甜點類關鍵字（根據使用者 2026-04-13 指示）
    dessert_kws = ["豆花", "芋圓", "蛋糕", "抹茶", "甜點", "甜品", "冰品", "咖啡", "奶茶", "甜品店", "蛋糕店"]
    if any(kw in name for kw in dessert_kws):
        return True
    # 類型判定
    if "bakery" in types or "cafe" in types or "dessert_shop" in types:
        return True
    return False

def goplaces_search(keyword: str, lat: float, lng: float,
                    radius_m: int, min_rating: float,
                    max_results: int = DEFAULT_MAX_CANDIDATES) -> List[dict]:
    env = os.environ.copy()
    work_dir = os.path.expanduser("~/.openclaw/skills/google-places")

    def fetch_page(page_token: str = None) -> tuple:
        token_arg = ["--page-token", page_token] if page_token else []
        args = [
            "goplaces", "search", keyword,
            "--lat", str(lat), "--lng", str(lng),
            "--radius-m", str(radius_m),
            "--open-now", "--min-rating", str(min_rating),
            "--limit", "20",
            "--json", *token_arg,
        ]
        r = subprocess.run(args, capture_output=True, text=True,
                          env=env, timeout=30, cwd=work_dir)
        out = r.stdout + r.stderr
        lines = out.split("\n")
        json_end = None
        for j in range(len(lines) - 2, -1, -1):
            if lines[j].strip() == "]":
                json_end = j; break
        if json_end is None:
            return [], ""
        txt = "\n".join(lines[:json_end + 1])
        try:
            places = json.loads(txt)
        except json.JSONDecodeError:
            return [], ""
        next_token = ""
        for line in lines[json_end + 1:]:
            if line.strip().startswith("next_page_token:"):
                next_token = line.split(":", 1)[1].strip()
                break
        return places, next_token

    # Lunch keyword: paginate to collect enough candidates
    # (Google "lunch" results are dominated by brunch, pagination is essential)
    if keyword in ("\u5348\u9910",):
        all_places: List[dict] = []
        next_token = ""
        seen_ids: set = set()
        while True:
            places, next_token = fetch_page(next_token if next_token else None)
            if not places:
                break
            for p in places:
                pid = p.get("place_id", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_places.append(p)
            non_brunch = [p for p in all_places if not _is_brunchy(p)]
            # Stop when we have >= 2 non-brunch OR no more pages
            if len(non_brunch) >= 2 or not next_token:
                break
        if not all_places:
            return []
        brunch_all = [p for p in all_places if _is_brunchy(p)]
        non_brunch = [p for p in all_places if not _is_brunchy(p)]
        if len(non_brunch) >= 2:
            return non_brunch
        else:
            return non_brunch + brunch_all
    else:
        places, _ = fetch_page()
        return places


# -------------------------------------------------------------
# 產業類別驗證 (Industry Category Gatekeeper)
# -------------------------------------------------------------
INDUSTRY_MAP = {
    "FOOD": {"restaurant", "food", "cafe", "bakery", "meal_takeaway", "bar"},
    "PARKING": {"parking"},
    "GAS_STATION": {"gas_station"},
    "MUSEUM": {"museum"},
    "LIBRARY": {"library"},
    "PARK": {"park"},
    "SCHOOL": {"school"},
    "LODGING": {"lodging"},
}

def _is_industry_match(place: dict, keyword: str) -> bool:
    """
    產業類別優先原則：驗證地點類別是否符合關鍵字的底層邏輯。
    """
    types = place.get("types", [])
    if not isinstance(types, list):
        types = []
    
    # 1. 餐飲/食物類：必須屬於 FOOD 產業
    if keyword in MEAL_KEYWORDS or keyword in FOOD_KEYWORDS:
        return any(t in INDUSTRY_MAP["FOOD"] for t in types)
    
    # 2. 設施類：針對特定關鍵字驗證類別
    if keyword == "停車場":
        return any(t in INDUSTRY_MAP["PARKING"] for t in types)
    if keyword == "加油站":
        return any(t in INDUSTRY_MAP["GAS_STATION"] for t in types)
    
    # 3. 地點類：針對特定關鍵字驗證類別
    if keyword in ("美術館", "博物館"):
        return any(t in INDUSTRY_MAP["MUSEUM"] for t in types)
    if keyword == "圖書館":
        return any(t in INDUSTRY_MAP["LIBRARY"] for t in types)
    if keyword == "公園":
        return any(t in INDUSTRY_MAP["PARK"] for t in types)
    if keyword == "學校":
        return any(t in INDUSTRY_MAP["SCHOOL"] for t in types)
    if keyword in ("旅館", "民宿"):
        return any(t in INDUSTRY_MAP["LODGING"] for t in types)
    
    # 4. 兜底：若無明確定義的類別對應，則允許通過（避免過度過濾）
    return True

def filter_and_sort(candidates: List[dict],
                    center_lat: float, center_lng: float,
                    min_rating: float,
                    keyword: str = "") -> List[dict]:
    filtered = []
    for c in candidates:
        # ★★★ 產業類別驗證 (Gatekeeper) ★★★
        if not _is_industry_match(c, keyword):
            continue
            
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
    vpy = os.path.expanduser("~/.openclaw/skills/google-places/.venv/bin/python")
    try:
        r = subprocess.run(
            [vpy, script, "full", place_id],
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
        # 完整評論（未過濾，保留給 _get_reviews_from_api_data 輸出用）
        data["_all_reviews"] = data.get("reviews", [])
    _QUERY_API_CACHE[place_id] = data
    return data


def _parse_pub_time(pub_str: str):
    """將 Google publish_time 字串解析為 datetime（處理9位小數）。"""
    from datetime import datetime, timezone
    if not pub_str:
        return None
    s = pub_str.replace("Z", "+00:00")
    # fromisoformat 只支援最多6位小數，截斷超出的部分
    dot = s.find(".")
    if dot != -1:
        sign = s.find("+", dot)
        if sign == -1:
            sign = s.find("-", dot)
        if sign > dot + 7:
            s = s[:dot+7] + s[sign:]
    try:
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except ValueError:
        return None


def _filter_reviews_6m(reviews: list) -> list:
    """過濾6個月內的評論（供食物關鍵字比對用）"""
    from datetime import datetime, timezone, timedelta
    six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
    filtered = []
    for rev in reviews:
        pub_str = rev.get("publish_time", "")
        pub_time = _parse_pub_time(pub_str)
        if pub_time is None:
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
                       rev_count: int = REV_COUNT,
                       raw_out: str = "") -> str:
    """
    格式化單一店家輸出（純文字，每欄位一行）。
    輸出預設用於包在 Triple backticks（```）中呈現於 webchat。

    raw_out: query_place_full() 的原始文字輸出，裡面有中文店名（🏪 店名：...）。
    """
    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    medal_str = medal[index] if index < len(medal) else f"{index + 1}️⃣"

    name     = place_data.get("name", "未知店家") if place_data else "未知店家"
    # 從 query_place_full() raw output 的「🏪 店名：中文名」一行抓中文名（覆寫英文 name）
    if raw_out:
        for line in raw_out.split("\n"):
            ls = line.strip()
            if ls.startswith("🏪 店名："):
                cn = ls[len("🏪 店名："):].strip()
                if cn:
                    name = translate_to_zh(cn)
                break
    # 最終確保店名一定是中文（處理 raw_out 缺失 label 或 API 原名為英文之情況）
    name = translate_to_zh(name)


    # 從 query_place_full() raw output 的「📍 地址：...」一行抓中文地址（覆寫 get_address 英文結果）
    addr_from_raw = ""
    if raw_out:
        for line in raw_out.split("\n"):
            ls = line.strip()
            if ls.startswith("📍 地址："):
                addr_from_raw = ls[len("📍 地址："):].strip()
                break
    pid      = place_data.get("place_id", "") if place_data else ""
    rating   = place_data.get("rating", 0) if place_data else 0
    rcount   = place_data.get("user_rating_count", 0) if place_data else 0
    phone    = place_data.get("phone", "") if place_data else ""
    open_now = place_data.get("open_now") if place_data else None
    svcs     = maps_price.get("service", [])
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{pid}" if pid else ""

    drv = estimate_time(dist_m, "driving")
    wal = estimate_time(dist_m, "walking")
    dist_km = dist_m / 1000
    max_dist = 3000
    bar_w = min(10, max(1, int(dist_m / max_dist * 10))) if max_dist > 0 else 5
    bar = "▓" * bar_w + "░" * (10 - bar_w)

    status_icon  = "✅"
    status_txt   = "營業中"
    status_extra = ""
    
    # 同步優化：優先使用 place_data 計算狀態與時間，不再單純依賴 status_line 文本解析
    status_icon, status_txt, status_extra = _calculate_status_info(place_data)
    
    # 如果 CDP 提供了更詳細的 status_line，則嘗試覆蓋（以即時 UI 為準）
    if maps_price.get("status_line"):
        sl = maps_price["status_line"]
        m2 = re.search(r"^([✅❌])\s*([^\s（\(]+)\s*[（\(](.+?)[）\)]$", sl)
        if m2:
            icon, txt, extra_raw = m2.group(1), m2.group(2), m2.group(3)
            # 統一格式：將「距離關門 X 小時 Y 分鐘」或「約剩...」統一為「X 小時 Y 分鐘後關門」
            time_m = re.search(r"(?:距離關門|約剩)\s*(\d+)\s*小時\s*(\d+)\s*分鐘", extra_raw)
            if time_m:
                extra_processed = f"{time_m.group(1)} 小時 {time_m.group(2)} 分鐘後關門"
            else:
                extra_processed = extra_raw
            status_icon, status_txt, status_extra = icon, txt, f"（{extra_processed}）"

    address_str = addr_from_raw if addr_from_raw else (get_address(place_data) if place_data else "無")
    phone_str  = f"📞 電話：{phone}" if phone else ""
    svcs_list = [s.strip() for s in svcs] if svcs else []
    svcs_str  = f"📌 服務：{'、'.join(svcs_list)}" if svcs_list else ""

    # ★★★ 特色菜色（v2.5 新增，v2.16 去重）★★★
    # _dish_from_reviews 回傳 List[(pattern, snippet)]，pattern=菜色名，snippet=評論片段
    # 同一菜色可能因多種 pattern 而重複出現，用 dict.fromkeys() 去重並保持順序
    dish_items = []
    if reviews:
        dish_raw = _dish_from_reviews(reviews)
        if dish_raw:
            dish_items = list(dict.fromkeys(d[0] for d in dish_raw[:10]))[:5]
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

    # ★★★ v2.6 純文字模板（每一個欄位獨立一行）★★★
    lines_out: List[str] = []
    lines_out.append(f"• {medal_str} {name}")

    lines_out.append(f"  ⭐ 評分：{rating}（{rcount}則）")
    lines_out.append(f"  📊 熱度：{bar}")
    lines_out.append(f"  🚗 開車：{drv}分｜🚶 走路：{wal}分（{dist_km:.1f}km）")
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
        # ④ 從評論中提取價格
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
    # ⑤ goplaces details 的 price_level（當上述全部失敗時兜底）
    if not price_val:
        _pl = place_data.get("price_level") if place_data else None
        if isinstance(_pl, int) and _pl >= 1:
            price_val = "$" * min(_pl, 4)
    # ⑥ place_data.priceRange（Google API，CDP 抓不到時的最後一道防線）
    if not price_val:
        _pr = place_data.get("priceRange") if place_data else None
        if _pr and isinstance(_pr, str) and _pr not in ("", "null", "None"):
            price_val = _pr
    lines_out.append(f"  💵 每人：{price_val if price_val else '無'}")

    lines_out.extend(_wrap_line("  📍 地址：", address_str))
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
    # ★★★ 評論（最多3則，自動斷行）★★★
    rev_list = _rev_from_list(reviews or [], rev_count)
    # 收集已顯示的評論文字，用於去重價格評論
    shown_texts: set[str] = set()
    if rev_list:
        for author, note, days_ago in rev_list:
            shown_texts.add(note)
            time_str = _days_ago_str(days_ago)
            # 修正：執行翻譯以滿足使用者可讀性需求
            translated_note = translate_to_zh(note)
            safe_note = re.sub(r'[\ufe00-\ufe0f\u200d]', '', translated_note.replace(chr(10), " "))
            # 加上 MARKER_START 讓 _wrap_chars 的無標點截斷只發生一次，避免 cascading
            marked_note = f"MARKER_START{safe_note}"
            wrapped = _wrap_chars("", marked_note, _WRAP_WIDTH)
            for idx, seg in enumerate(wrapped):
                stripped = seg.strip()
                if not stripped or stripped in ("─", "──"):
                    continue
                if stripped.startswith("MARKER_START"):
                    stripped = stripped[len("MARKER_START"):]
                prefix = f"👤 {author}：" if idx == 0 else "  "
                if stripped and stripped not in lines_out:
                    lines_out.append(f"{prefix}`{stripped}`")
            # 時間獨立一行（不在 _wrap_chars 內，避免時間孤兒問題）
            lines_out.append(f"  {time_str}")
    else:
        lines_out.append(f"  👤 無（近期評論中未抓獲特定菜色）")

    # ★★★ 價格留言（v2.11 新增，專門抓有提到價格的評論）★★★
    price_rev_list = _price_rev_from_list(reviews or [], rev_count)
    if price_rev_list:
        for author, full_sent, product, portion, price_str, days_ago in price_rev_list:
            # 跳過已出現在 rev_list 的評論（避免重複）
            if full_sent in shown_texts:
                continue
            time_str = _days_ago_str(days_ago)
            # 組合呈現：🍴品項  💰價格  👤留言  時間
            segment = f"  🍴 {product}" if product != "（未識別品項）" else ""
            if portion:
                segment += f"（{portion}）" if segment else f"  🍴（{portion}）"
            if price_str:
                segment += f"  💰 {price_str}"
            # 修正：執行翻譯以滿足使用者可讀性需求
            translated_sent = translate_to_zh(full_sent)
            safe_sent = re.sub(r'[︀-️‍]', '', translated_sent.replace("\n", " "))
            safe_sent = re.sub(r'[\ufe00-\ufe0f\u200d]', '', translated_sent.replace("\n", " "))
            author_line = f"👤 {author}：`{safe_sent}` {time_str}"

            # 先輸出品項+價格行，再輸出作者+評論行
            if segment.strip():
                lines_out.append(segment)
            wrapped = _wrap_chars("  ", author_line, width=_WRAP_WIDTH)
            for wline in wrapped:
                stripped = wline.strip()
                if stripped and stripped not in ("─", "──"):
                    existing = any(stripped == l.strip() for l in lines_out)
                    if not existing:
                        lines_out.append(wline if wline.startswith("  ") else f"  {stripped}")

    # Google Maps 連結（URL 可能很長，一樣斷行）
    if maps_url:
        lines_out.extend(_wrap_line("  🗺️ 地圖：", maps_url))
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

    # 8. 跳過（前 N 家，用於「再看看其他」類需求）
    offset = 0
    offset_match = re.search(r"跳過[掉前]?\s*(\d+)\s*(?:家|間)", text)
    if offset_match:
        offset = int(offset_match.group(1))

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
        "offset": offset,
    }


# -------------------------------------------------------------
# 主搜尋流程
# -------------------------------------------------------------

def search_and_detail(params: Dict, verbose: bool = True) -> str:
    user_text = params.get("user_text", "")
    keyword   = params["keyword"]
    food_kw   = params["food_kw"]       # 可能為 None
    lat       = params["lat"]
    lng       = params["lng"]
    radius_m  = params["radius_m"]
    radius_hint = params["radius_hint"]
    min_rating = params["min_rating"]
    max_results = params["max_results"]
    rev_count = params.get("rev_count", REV_COUNT)
    offset = params.get("offset", 0)

    expansion_log: List[int] = []
    candidates: List[dict] = []
    final_radius = radius_m
    seen_pids: set = set()   # 用 place_id 去重，避免重複加入同一店家

    # -- Step 2: 半徑擴張搜尋（累加候選，不中途中斷）--
    # 使用原始 user_text 作為搜尋詞，而非僅使用觸發 keyword
    search_query = user_text if user_text else keyword
    
    for radius in EXPANSION_RADII:
        if radius < radius_m: continue
        final_radius = radius
        expansion_log.append(radius)

        results = goplaces_search(search_query, lat, lng, radius, min_rating)
        if isinstance(results, list):
            new_results = results
        elif isinstance(results, dict) and "places" in results:
            new_results = results["places"]
        else:
            new_results = []

        # 累加候選（依 place_id 去重）
        for place in new_results:
            pid = get_place_id(place)
            if pid and pid not in seen_pids:
                seen_pids.add(pid)
                candidates.append(place)

        non_brunch_count = sum(1 for p in candidates if not _is_brunchy(p))
        if non_brunch_count >= max_results:
            break
        if radius >= 50000:
            break

    # ★★★ 2026-04-09 餐飲時段擴展搜尋：數量不足時補足，僅限「非早午餐/非只賣早餐」的店家 ★★★
    if keyword in MEAL_KEYWORDS and len(candidates) < max_results * 2:
        # 先擴 breakfast 類（可能混在 lunch 結果裡），再擴一般餐飲
        extra_keywords = []
        if keyword == "午餐":
            extra_keywords = ["早午餐", "便當", "自助餐", "合菜", "快炒",
                              "義式", "咖哩", "燒肉", "牛排", "日式", "韓式", "港式"]
        elif keyword == "晚餐":
            extra_keywords = ["便當", "合菜", "快炒", "義式", "咖哩",
                              "燒肉", "牛排", "火鍋", "日式", "韓式", "港式"]
        elif keyword == "早餐":
            extra_keywords = ["早午餐", "蛋餅", "飯糰", "豆漿"]
        elif keyword == "宵夜":
            extra_keywords = ["小吃", "鹹酥雞", "滷味", "關東煮", "火鍋", "燒烤"]
        elif keyword == "下午茶":
            extra_keywords = ["咖啡", "甜點", "蛋糕", "冰品", "輕食", "義式", "豆花", "芋圓"]
        elif keyword == "點心":
            extra_keywords = ["小吃", "鹹酥雞", "雞排", "水煎包", "蔥油餅", "蛋餅", "甜點", "豆花"]
        else:
            extra_keywords = ["小吃", "便當", "合菜", "義式", "咖哩", "燒肉", "牛排"]

        for kw in extra_keywords:
            broad_results = goplaces_search(kw, lat, lng, final_radius, min_rating)
            if isinstance(broad_results, list):
                for place in broad_results:
                    pid = get_place_id(place)
                    if pid and pid not in seen_pids:
                        seen_pids.add(pid)
                        candidates.append(place)

    # -- Step 3: 過濾 + 排序 --
    filtered = filter_and_sort(candidates, lat, lng, min_rating, keyword)

    # ★★★ 正餐與甜點隔離過濾（2026-04-13 修正） ★★★
    if keyword in ("早餐", "午餐", "晚餐"):
        filtered = [p for p in filtered if not _is_desserty(p)]

    # -- 食物關鍵字過濾 --
    if food_kw and filtered:
        food_filtered: List[dict] = []
        skipped_count = 0
        for place in filtered:
            pid = get_place_id(place)
            if not pid:
                skipped_count += 1
                continue
            api_data = query_place_api_only(pid)
            if api_data and place_mentions_food(api_data, food_kw):
                place["_api_data"] = api_data
                food_filtered.append(place)
            else:
                skipped_count += 1
        if len(food_filtered) < max_results:
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

    # -- Step 4: 決定最終結果（處理打烊時間 + 早午餐降序） --
    # 餐飲時段：全部依距離由近到遠，早午餐店家排在同距離的末端
    # 食物關鍵字：依評分高低
    is_meal_kw = keyword in MEAL_KEYWORDS
    if is_food_keyword(params["keyword"]):
        filtered.sort(key=lambda x: get_rating(x), reverse=True)
        pool = filtered[:DEFAULT_MAX_CANDIDATES * 2]
    elif is_meal_kw:
        # 餐飲時段：依距離，brunch/早餐店家附加 penalty 往後挪
        def _meal_sort_key(p):
            dist = p.get("_distance_m", 999999)
            # penalty：早午餐店家 distance + 500m，避免完全排除但降低排序優
            penalty = 500 if _is_brunchy(p) else 0
            return dist + penalty
        filtered.sort(key=_meal_sort_key)
        pool = filtered[:DEFAULT_MAX_CANDIDATES * 3]   # 多取一些，30min內打烊會再過濾
    else:
        pool = filtered[offset : offset + max_results * 4]

    # 並行查詢詳細資料以獲取 status_line
    top_pids = [(i, get_place_id(p), p.get("_distance_m", 0), p) for i, p in enumerate(pool)]
    parallel_results: dict = {}

    def _fetch_place(pid_i):
        idx, pid = pid_i[0], pid_i[1]
        if not pid: return pid, None, None, None
        api_data = pool[idx].get("_api_data") or query_place_api_only(pid)
        structured, _raw_out = query_place_full(pid) if pid else (None, "")
        maps_price = _parse_maps_price_from_raw(_raw_out) if _raw_out else {"found": False}
        return pid, (api_data or structured or {}), maps_price, _raw_out

    with ThreadPoolExecutor(max_workers=min(len(top_pids), 5)) as ex:
        futures = {ex.submit(_fetch_place, (i, pid)): pid for i, pid, _, _ in top_pids if pid}
        for f in as_completed(futures):
            pid = futures[f]
            result = f.result()
            if result and result[0]:
                _pid, api_d, mp, raw_out = result
                parallel_results[_pid] = (api_d, mp, raw_out)

    # 根據營業狀態篩選
    final_results = []
    for place in pool:
        pid = get_place_id(place)
        if pid not in parallel_results: continue
        api_data, maps_price, raw_out = parallel_results[pid]
        
        # 檢查是否在 30 分鐘內打烊 (僅針對餐飲時段關鍵字)
        if keyword in MEAL_KEYWORDS and _is_closing_soon(maps_price.get("status_line")):
            continue
            
        # 儲存詳細資料供 format_full_output 使用
        place["_final_api_data"] = api_data
        place["_final_maps_price"] = maps_price
        place["_final_raw_out"] = raw_out
        
        final_results.append(place)
        if len(final_results) >= max_results:
            break

    # 重新按距離排序
    final_results.sort(key=lambda x: x.get("_distance_m", 999999))

    # -- 輸出 Header --
    r_display = f"{final_radius // 1000}km" if final_radius >= 1000 else f"{final_radius}m"
    rh_display = f"（{radius_hint}）" if radius_hint else ""
    lines: List[str] = []
    lines.append(f"# 🍽️ {keyword} 選項（{lat:.4f}, {lng:.4f}）")
    lines.append(f"📍 條件：{keyword}")
    lines.append(f"📏 半徑：{r_display} {rh_display}")
    lines.append(f"📊 評分 ≥ {min_rating}")
    offset_note = f"（第 {offset+1}–{offset+max_results} 名）" if offset > 0 else ""
    lines.append(f"🔍 共 {len(candidates)} 家候選{offset_note}")
    lines.append("---")

    for i, place in enumerate(final_results):
        pid  = get_place_id(place)
        dist = place.get("_distance_m", 0)
        api_data = place.get("_final_api_data")
        maps_price = place.get("_final_maps_price")
        raw_out = place.get("_final_raw_out")
        price_range_api = (api_data or {}).get("_price_range") or ""
        reviews = _get_reviews_from_api_data(api_data) if api_data else []
        detail_text = format_full_output(api_data or {}, maps_price or {}, food_kw, dist, i,
                                         reviews, price_range_api=price_range_api,
                                         rev_count=rev_count, raw_out=raw_out or "")
        lines.append(detail_text)

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
    # ── 解析 🚦 狀態行（query.py full 输出版）──────────────────────
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
        # 直接使用原始評論內容（不翻譯），符合數據真實性原則
        content = raw_content
        pub_str = r.get("publish_time", "")
        pub_time = _parse_pub_time(pub_str)
        if pub_time is None:
            pub_time = now_utc; days_ago = 0
        else:
            days_ago = (now_utc - pub_time).days
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
        days_limit = float(days_limit)
        if days_limit == float("inf"):
            candidates = enriched[:]
        else:
            cutoff = now_utc - timedelta(days=days_limit)
            candidates = [r for r in enriched if r["_pub_time"] >= cutoff]
        if len(candidates) >= 5:
            return candidates[:5]
    return enriched[:5]


# ────────────────────────────────────────────────────────────────
# 特色菜色匹配 patterns（2026-04-01 v2.16 大幅擴充）
# 格式：(匹配關鍵字, 顯示名稱)
# 原則：keyword 越精確越前面（長→短），顯示名稱取常見說法
# ────────────────────────────────────────────────────────────────
_MEAT_PROTEIN = [   # 蛋白質 / 肉類前綴（與形容詞搭配）
    "牛", "牛肉", "豬", "豬肉", "雞", "雞肉", "羊", "羊肉",
    "鵝", "鴨", "蝦", "蟹", "魚", "魷魚", "透抽", "小卷",
    "干貝", "蛤蜊", "生蠔", "牡蠣", "九孔", "淡菜",
    "海膽", "龍蝦", "花枝", "腿", "翅", "腩",
]
# 合併所有菜色 pattern：dict（前綴映射）+ list of tuple（精確品項）
_MEAT_DISPLAY = [
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
    ("咖喱飯","咖喱飯"),("咖哩飯","咖 curry飯"),("牛井","牛井"),("鰻魚飯","鰻魚飯"),
    ("烏龍麵","烏龍麵"),("蕎麥麵","蕎麥"),("咖喱烏龍","咖 curry烏龍"),("咖哩烏龍","咖 curry烏龍"),
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
    ("espresso","espresso"),("摩卡","摩卡"),("焦糖","焦糖"),
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
    ("餛飩麵","餛鈍麵"),("餛飩湯","餛飩湯"),("大腸麵線","大腸麵線"),("蚵仔麵線","蚵仔麵線"),
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
    ("花枝","花枝"),("小卷","小卷"),
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
    ("牛奶鍋","牛奶鍋"),("起司鍋","起司鍋"),("咖喱鍋","咖 curry鍋"),
    ("泡菜鍋","泡菜鍋"),("酸白菜鍋","酸白菜鍋"),("麻油雞","麻油雞"),
    # ── 其他主食（擴充）──────────────────────────────
    ("炒飯","炒飯"),("炒麵","炒麵"),("燴飯","燴飯"),("蓋飯","蓋飯"),
    ("雞肉飯","雞肉飯"),("排骨飯","排骨飯"),("牛腩飯","牛腩飯"),
    ("焢肉飯","焢肉飯"),("控肉飯","控肉飯"),("爌肉飯","爌肉飯"),
    ("羊肉炒麵","羊肉炒麵"),("蝦仁炒麵","蝦仁炒麵"),
    ("剝皮辣椒麵","剝皮辣椒麵"),("剝皮辣椒雞麵","剝皮辣椒雞麵"),
]

_DISH_PATTERNS = _MEAT_DISPLAY



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
    days = max(0, days)   # 時區邊界 protection
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
    # 時間孤兒過濾：純時間標記（如「（1年前）」「（3天前）」「（2個月前）」）不算一句
    _TIME_ONLY_RE = re.compile(r"^（[0-9零一二三四五六七八九十百千]+[天月年]+前）$")
    # Step 1: 將同一作者、同一時間的所有段落合併為一則評論（只取完整合併文字）
    merged: list[tuple[str, str, int]] = []  # (author, content, days_ago)
    for review in reviews:
        author   = review.get("author", "")
        content  = review.get("content", "")
        days_ago = review.get("days_ago", 0)
        if not content:
            continue
        # 所有段落合併為一則完整評論
        joined = "\n".join(p.strip() for p in content.split("\n") if p.strip())
        merged.append((author, joined, days_ago))

    # Step 2: 過濾與排序
    results: list[tuple[str, str, int]] = []
    seen_text: set[str] = set()
    for author, text, days_ago in merged:
        if _TIME_ONLY_RE.match(text): continue
        if len(text) < 4 or len(text) > 300: continue
        if re.search(r"\$\d+", text): continue
        if re.search(r"美元|美金|日幣|日圆|韓元|歐元|台幣", text): continue
        if text in seen_text: continue
        seen_text.add(text); results.append((author, text, days_ago))
        if len(results) >= rev_count: break

    if len(results) < rev_count:
        for author, text, days_ago in merged:
            if _TIME_ONLY_RE.match(text): continue
            if len(text) < 4 or len(text) > 300: continue
            if re.search(r"\$\d+", text): continue
            if re.search(r"美元|美金|日幣|日圆|韓元|歐元|台幣", text): continue
            if text in seen_text: continue
            seen_text.add(text); results.append((author, text, days_ago))
            if len(results) >= rev_count: break

    # Sort by days_ago ascending (most recent first), then cap at rev_count
    sorted_results = sorted([(a, n, d) for a, n, d in results if len(n) >= 10], key=lambda x: x[2])
    return sorted_results[:rev_count]


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
        # 預設份量：抓「1人份」「2人人份」等
        m = re.search(r"(\d+)\s*人[份道個位]", sent)
        if m:
            portion = f"{m.group(1)}人份"

    product = product_part.strip() if product_part.strip() else "（未識別品項）"
    return product, portion, price_str


# -------------------------------------------------------------
# CLI 入口
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLI 入口（2026-04-10 v2.24）
#批次輸出：count > 5 時自動分批，每批5間，間隔30秒，逐步輸出給使用者
# -------------------------------------------------------------

BATCH_SIZE = 5           # 每批處理上限
BATCH_COOLDOWN = 30      # 每批間隔秒數（等待配額恢復）

def main():
    if len(sys.argv) < 2:
        print("用法: python3 run.py <使用者文字> [--count N]")
        print("範例: python3 run.py 我想吃早餐")
        print("範例: python3 run.py 找停車場 24.1858,120.6677 開車5分")
        print("範例: python3 run.py 午餐 --count 10")
        sys.exit(1)

    # 處理 --count N 參數（2026-03-26 新增）
    argv = []
    count_suffix = ""
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--count" and i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            count_suffix = f" {sys.argv[i + 1]}間"
            i += 2
        elif arg.startswith("--count=") and arg.split("=", 1)[1].isdigit():
            num = arg.split("=", 1)[1]
            count_suffix = f" {num}間"
            i += 1
        else:
            argv.append(arg)
            i += 1

    user_text = " ".join(argv) + count_suffix

    params = parse_input(user_text)
    if not params:
        print("⚠️ 無法從文字中辨識搜尋意圖")
        print(f"   請使用餐飲/設施/地點/食物關鍵字，如：{TRIGGER_KEYWORDS[:10]}")
        sys.exit(1)

    total_count = params.get("max_results", DEFAULT_MAX_RESULTS)

    # ── 分批處理：count > 5 時，每批 BATCH_SIZE 間，逐步輸出 ──
    if total_count > BATCH_SIZE:
        offset = 0
        batch_num = 1
        while offset < total_count:
            batch_max = min(BATCH_SIZE, total_count - offset)
            params_batch = {**params, "max_results": batch_max, "offset": offset}

            batch_label = f"（第 {offset+1}–{offset+batch_max} 名，共 {total_count} 名）"
            result = search_and_detail(params_batch)
            # 在抬頭註明這是第幾批
            lines = result.split("\n")
            for li, line in enumerate(lines):
                if line.startswith("🔍 共"):
                    lines[li] = f"🔍 {batch_label}"
                    break

            output = "\n".join(lines)
            print(f"\n```\n{output}\n```\n")

            offset += batch_max

            if offset < total_count:
                remaining = total_count - offset
                print(f"⏳ 還有 {remaining} 間店家待查詢，正在等待配額恢復（{BATCH_COOLDOWN}s）...\n")
                time.sleep(BATCH_COOLDOWN)
            else:
                print("✅ 全部店家已查詢完畢！\n")
    else:
        result = search_and_detail(params)
        print(f"\n```\n{result}\n```\n")


if __name__ == "__main__":
    main()
