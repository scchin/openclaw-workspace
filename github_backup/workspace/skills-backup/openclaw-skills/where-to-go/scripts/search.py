#!/usr/bin/env python3
"""
where-to-go 搜尋腳本 v1.0
根據關鍵字、圓心、範圍，搜尋 Google Places 候選店家並做排序/過濾。
"""
import subprocess
import json
import sys
import os
import math
import re
from typing import List, Dict, Optional, Tuple

# ─── 設定 ────────────────────────────────────────────────────
DEFAULT_LAT = 24.18588146738243
DEFAULT_LNG = 120.66765935832942
DEFAULT_RADIUS_M = 1000
DEFAULT_MIN_RATING = 4.5
DEFAULT_MAX_RESULTS = 5
DEFAULT_MAX_CANDIDATES = 20

EXPANSION_RADII = [1000, 1500, 2500, 5000, 10000, 20000, 50000]

TRIGGER_KEYWORDS = [
    "早餐", "午餐", "晚餐", "宵夜", "下午茶", "點心",
    "麵包", "小吃", "夜市", "餐館", "飯店",
    "廁所", "加油站", "停車場"
]

RADIUS_MAP = {
    # 半徑(公尺) for N 分鐘 driving/walking
    "driving": lambda m: 500 * m,
    "walking": lambda m: 80 * m,
}


# ─── 工具函式 ────────────────────────────────────────────────

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """計算兩點間直線距離（公尺）"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_radius(raw: str) -> Tuple[Optional[int], str]:
    """
    解析半徑字串，回傳 (半徑_公尺, 單位).
    支援："500m", "1km", "開車10分", "走路15分", "10分鐘", "1000"
    """
    raw = raw.strip()
    # 公尺直接數字
    m = re.match(r"^(\d+)\s*m\b", raw, re.IGNORECASE)
    if m:
        return int(m.group(1)), "m"
    # 公里
    km = re.match(r"^([\d.]+)\s*km\b", raw, re.IGNORECASE)
    if km:
        return int(float(km.group(1)) * 1000), "km"
    # 開車 N 分
    drv = re.match(r"開車\s*(\d+)\s*(分|分鐘|min)", raw)
    if drv:
        mins = int(drv.group(1))
        return 500 * mins, f"開車{mins}分"
    # 走路 N 分
    wal = re.match(r"走路\s*(\d+)\s*(分|分鐘|min)", raw)
    if wal:
        mins = int(wal.group(1))
        return 80 * mins, f"走路{mins}分"
    # 純數字 → 視為公尺
    num = re.match(r"^(\d+)$", raw)
    if num:
        return int(num.group(1)), "m"
    return None, ""


def is_open(data: dict) -> bool:
    """檢查店家是否營業中"""
    try:
        # goplaces 直接在頂層放 open_now (snake_case)
        if "open_now" in data:
            return bool(data["open_now"])
        if "openNow" in data:
            return bool(data["openNow"])
        # 舊格式
        hours = data.get("currentOpeningHours", {})
        if "currentOperatingHours" in hours:
            return hours["currentOperatingHours"].get("openNow", False)
        if "regularHours" in hours:
            return hours["regularHours"][0].get("openNow", False)
        return hours.get("openNow", False)
    except Exception:
        pass
    return False


def is_permanently_closed(data: dict) -> bool:
    """檢查是否永久停業"""
    try:
        return data.get("businessStatus") == "CLOSED_PERMANENTLY"
    except Exception:
        return False


def normalize_status(data: dict) -> str:
    """回傳狀態描述"""
    if is_permanently_closed(data):
        return "永久停業"
    if is_open(data):
        return "營業中"
    return "休息中"


def get_display_name(data: dict) -> str:
    return data.get("displayName", {}).get("text", data.get("name", "未知店家"))


def get_rating(data: dict) -> float:
    try:
        return float(data.get("rating", 0))
    except Exception:
        return 0.0


def get_address(data: dict) -> str:
    return data.get("formattedAddress", data.get("address", "無地址"))


def get_place_id(data: dict) -> str:
    return data.get("id", data.get("placeId", ""))


def extract_keyword(text: str) -> Optional[str]:
    """從使用者文字中擷取第一個觸發關鍵字"""
    for kw in TRIGGER_KEYWORDS:
        if kw in text:
            return kw
    return None


def goplaces_search(keyword: str, lat: float, lng: float,
                    radius_m: int, min_rating: float,
                    max_results: int = DEFAULT_MAX_CANDIDATES) -> List[dict]:
    """
    呼叫 goplaces search 並解析結果。
    """
    env = os.environ.copy()
    work_dir = os.path.expanduser("~/.openclaw/skills/google-places")
    args = [
        "goplaces", "search", keyword,
        "--lat", str(lat),
        "--lng", str(lng),
        "--radius-m", str(radius_m),
        "--open-now",
        "--min-rating", str(min_rating),
        "--limit", str(max_results),
        "--json",
    ]
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                          env=env, timeout=30, cwd=work_dir)
        out = r.stdout + r.stderr
        # goplaces --json 輸出：JSON array 後面還有 next_page_token，非標準 JSON
        # 從倒數第2行往回找，倒數第1行是空字串，倒數第2行才是真正的 ]
        all_lines = out.split("\n")
        # 策略：最後一個 ] 單獨一行（陣列結尾）
        json_end_idx = None
        for j in range(len(all_lines) - 2, -1, -1):  # 跳過倒數第1行（空白）
            if all_lines[j].strip() == "]":
                json_end_idx = j
                break
        if json_end_idx is not None:
            json_text = "\n".join(all_lines[:json_end_idx + 1])
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        if json_text:
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        # 兜底：整個輸出
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass
    except Exception as e:
        print(f"[goplaces search 錯誤] {e}", file=sys.stderr)
    return []


def filter_and_sort(candidates: List[dict],
                    center_lat: float, center_lng: float,
                    min_rating: float) -> List[dict]:
    """
    過濾 + 計算距離 + 排序。
    """
    filtered = []
    for c in candidates:
        if is_permanently_closed(c):
            continue
        if get_rating(c) < min_rating:
            continue
        lat = c.get("location", {}).get("lat", 0)
        lng = c.get("location", {}).get("lng", 0)
        dist = haversine(center_lat, center_lng, lat, lng)
        c["_distance_m"] = dist
        filtered.append(c)

    # 由近到遠排序
    filtered.sort(key=lambda x: x["_distance_m"])
    return filtered


def estimate_driving_time_mins(distance_m: float) -> int:
    """粗估市區開車分鐘數（含停等）"""
    km = distance_m / 1000
    # 市區約 20 km/h（含停等紅綠燈、塞車）
    return max(1, round(km / 20 * 60))


def estimate_walking_time_mins(distance_m: float) -> int:
    """粗估走路分鐘數"""
    km = distance_m / 1000
    # 約 5 km/h
    return max(1, round(km / 5 * 60))


# ─── 主搜尋流程 ──────────────────────────────────────────────

def search(keyword: str,
           center_lat: float = DEFAULT_LAT,
           center_lng: float = DEFAULT_LNG,
           radius_m: int = DEFAULT_RADIUS_M,
           min_rating: float = DEFAULT_MIN_RATING,
           max_results: int = DEFAULT_MAX_RESULTS,
           radius_hint: str = "") -> Dict:
    """
    完整搜尋流程：半徑擴張 → 過濾排序 → 回傳結果。
    """
    expansion_log = []
    candidates = []
    final_radius = radius_m

    for radius in EXPANSION_RADII:
        if radius < radius_m:
            continue
        final_radius = radius
        expansion_log.append(radius)
        results = goplaces_search(keyword, center_lat, center_lng,
                                  radius, min_rating)
        if isinstance(results, dict) and "places" in results:
            candidates = results["places"]
        elif isinstance(results, list):
            candidates = results
        else:
            candidates = []

        if len(candidates) >= max_results:
            break
        if radius >= 50000:
            break

    filtered = filter_and_sort(candidates, center_lat, center_lng, min_rating)
    top_results = filtered[:max_results]

    return {
        "keyword": keyword,
        "center": {"lat": center_lat, "lng": center_lng},
        "initial_radius_m": radius_m,
        "final_radius_m": final_radius,
        "expansion_log": expansion_log,
        "total_candidates": len(candidates),
        "results": top_results,
        "radius_hint": radius_hint,
    }


# ─── 格式化輸出 ──────────────────────────────────────────────

def format_place(place: dict, keyword: str, index: int) -> str:
    """格式化單一店家（基礎列表視圖）"""
    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    dist = place.get("_distance_m", 0)
    drv = estimate_driving_time_mins(dist)
    wal = estimate_walking_time_mins(dist)
    name = get_display_name(place)
    rating = get_rating(place)
    address = get_address(place)
    status = normalize_status(place)
    status_icon = "✅" if status == "營業中" else "❌"
    phone = place.get("nationalPhoneNumber", place.get("phoneNumber", ""))
    pid = get_place_id(place)

    lines = []
    lines.append(f"{medal[index]} 【{keyword}】{name}｜⭐ {rating}｜🚗 {drv}分 🚶 {wal}分")
    lines.append(f"   📍 {address}")
    if phone:
        lines.append(f"   📞 {phone}｜{status_icon} {status}")
    else:
        lines.append(f"   📞 無｜{status_icon} {status}")
    lines.append(f"   📏 距離：{dist:.0f}m（直線）")
    if pid:
        lines.append(f"   🔗 https://www.google.com/maps/place/?q=place_id:{pid}")
    return "\n".join(lines)


def format_result(result: Dict) -> str:
    lines = []
    kw = result["keyword"]
    c = result["center"]
    r = result["final_radius_m"]
    rh = result["radius_hint"]

    radius_str = f"{r // 1000}km" if r >= 1000 else f"{r}m"
    hint_str = f"（{rh}）" if rh else ""

    lines.append("=" * 48)
    lines.append(f"📍 搜尋條件")
    lines.append(f"   關鍵字：{kw}｜圓心：({c['lat']:.4f}, {c['lng']:.4f})｜半徑：{radius_str} {hint_str}")

    if result["expansion_log"]:
        expanded = " → ".join(str(x) for x in result["expansion_log"])
        lines.append(f"   找到 {result['total_candidates']} 家候選｜半徑擴張：{expanded}")
    else:
        lines.append(f"   找到 {result['total_candidates']} 家候選")

    results_list = result["results"]
    if not results_list:
        lines.append("")
        lines.append("⚠️ 在指定範圍內找不到符合條件的店家")
        return "\n".join(lines)

    lines.append(f"   顯示前 {len(results_list)} 家（評分 ≥ {DEFAULT_MIN_RATING}，由近到遠）")
    lines.append("")

    for i, place in enumerate(results_list):
        lines.append(format_place(place, kw, i))
        lines.append("")

    return "\n".join(lines)


# ─── CLI 入口（測試用）───────────────────────────────────────

if __name__ == "__main__":
    # python search.py 早餐 24.18588146738243 120.66765935832942 1000
    if len(sys.argv) >= 2:
        keyword = sys.argv[1]
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LAT
        lng = float(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_LNG
        radius = int(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_RADIUS_M

        res = search(keyword, lat, lng, radius)
        print(format_result(res))
    else:
        print("用法: python search.py <關鍵字> [lat] [lng] [半徑_m]")
